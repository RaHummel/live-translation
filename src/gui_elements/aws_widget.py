import configparser
import logging
import os
from typing import Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import AWSSettings
from constants import AWS_REGIONS, TRANSLATOR

LOGGER = logging.getLogger(__name__)


class AWSWidget(QWidget):
    """
    A widget for configuring Amazon Web Services (AWS) specific translation settings.
    It groups connection settings (Region, Credentials) and language settings (Source, Target).
    """

    target_lang_toggled = Signal(str, bool)  # Signal emitted when a target language checkbox is toggled
    aws_region_changed = Signal(str)  # Signal emitted when the selected AWS region changes

    def __init__(self, aws_settings: AWSSettings, parent: Optional[QWidget] = None):
        """
        Initializes the AWSConfigWidget.
        Args:
            aws_settings (AWSSettings): The AWS settings to be applied.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._aws_settings = aws_settings
        self.aws_target_lang_checkboxes = {}
        self.aws_voice_selectors = {}
        self._setup_ui()
        self._check_aws_credentials()

    def update_settings(self, aws_settings: AWSSettings) -> None:
        """
        Updates the AWS settings in the widget.
        Args:
            aws_settings (AWSSettings): User specific AWS settings.
        """
        self.aws_region_select.setCurrentText(f'{aws_settings.region} ({AWS_REGIONS[aws_settings.region]})')
        self.aws_source_lang.setCurrentText(aws_settings.source_language)

        # Apply target language and voice settings
        for lang, lang_setting in aws_settings.target_languages.items():
            voice_id = lang_setting.voice_id
            checkbox = self.aws_target_lang_checkboxes[lang]
            checkbox.setChecked(True)
            checkbox.setEnabled(True)

            voice_selector = self.aws_voice_selectors[lang]
            voice_selector.setEnabled(True)

            if voice_id in [voice_selector.itemText(i) for i in range(voice_selector.count())]:
                voice_selector.setCurrentText(voice_id)
            else:
                LOGGER.warning(f'Configured voice ID "{voice_id}" not found for language "{lang}".')

        self._aws_settings = aws_settings

    @staticmethod
    def get_aws_cred_path() -> Tuple[str, str]:
        aws_dir = os.path.expanduser('~/.aws')
        return aws_dir, os.path.join(aws_dir, 'credentials')

    def _setup_ui(self) -> None:
        """
        Sets up the user interface for the AWSConfigWidget.
        """
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins for a cleaner look within the tab

        aws_connection_group = QGroupBox('AWS Connection Settings')
        aws_connection_v_layout = QVBoxLayout(aws_connection_group)

        # Region Selection
        region_form_layout = QFormLayout()
        region_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignHCenter)
        region_form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter)
        region_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.aws_region_select = QComboBox()

        for region_code, region_name in AWS_REGIONS.items():
            self.aws_region_select.addItem(f'{region_code} ({region_name})', region_code)

        region = self._aws_settings.region
        self.aws_region_select.setCurrentText(f'{region} ({AWS_REGIONS[region]})')
        self.aws_region_select.setStatusTip('Select the AWS region where your resources are located.')
        self.aws_region_select.setToolTip('Choose your AWS region.')

        region_form_layout.addRow('Region:', self.aws_region_select)
        aws_connection_v_layout.addLayout(region_form_layout)

        # Credentials Status Label
        credentials_status_layout = QHBoxLayout()
        self.credentials_status_label = QLabel('Status: Initializing...')
        self.credentials_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credentials_status_layout.addWidget(self.credentials_status_label)
        aws_connection_v_layout.addLayout(credentials_status_layout)

        # Credential Management Button
        credential_buttons_layout = QHBoxLayout()
        credential_buttons_layout.addStretch()
        self.manage_credentials_button = QPushButton('Manage Credentials')
        self.manage_credentials_button.clicked.connect(self._open_credentials_dialog)
        credential_buttons_layout.addWidget(self.manage_credentials_button)
        credential_buttons_layout.addStretch()
        aws_connection_v_layout.addLayout(credential_buttons_layout)

        # Add the entire AWS connection group (with its QFormLayout) to the main layout
        main_v_layout.addWidget(aws_connection_group)

        # --- Language Settings Group (combining Source & Target Languages) ---
        language_settings_group = QGroupBox('Language Settings')
        # Use a QVBoxLayout to stack source language and target languages sections
        language_settings_layout = QVBoxLayout(language_settings_group)

        # Source Language
        source_lang_form_layout = QFormLayout(fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.aws_languages = sorted(list(TRANSLATOR['aws'].keys()))

        self.aws_source_lang = QComboBox()
        self.aws_source_lang.addItems(self.aws_languages)
        self.aws_source_lang.setCurrentText(self._aws_settings.source_language)
        self.aws_source_lang.setStatusTip('Select the language spoken by the input audio.')
        self.aws_source_lang.setToolTip('Select the language spoken by the input audio.')
        self.aws_source_lang.currentTextChanged.connect(
            self._update_target_languages
        )  # Connect to update target languages
        source_lang_form_layout.addRow('Source Language:', self.aws_source_lang)
        language_settings_layout.addLayout(source_lang_form_layout)  # Add source language section to language group

        target_lang_sub_group_title_label = QLabel('Translation Target Languages:')
        language_settings_layout.addWidget(target_lang_sub_group_title_label)

        # Target Languages (within a scroll area)
        scroll_area = QScrollArea(widgetResizable=True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # No horizontal scroll
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Vertical scroll as needed

        scroll_content_widget = QWidget()
        target_grid_layout = QGridLayout(scroll_content_widget)
        target_grid_layout.setContentsMargins(5, 5, 5, 5)
        target_grid_layout.setSpacing(10)

        # Ensure the grid expands to fill the available width
        target_grid_layout.setColumnStretch(0, 1)
        target_grid_layout.setColumnStretch(1, 1)

        row = 0
        col = 0
        num_cols = 2  # Number of columns for target language checkboxes and voice selectors

        for lang in self.aws_languages:
            lang_selection_layout = QVBoxLayout()
            lang_selection_layout.setContentsMargins(0, 0, 0, 0)

            checkbox = QCheckBox(lang)

            checkbox.setStatusTip(f'Enable translation to {lang}.')
            checkbox.setToolTip(f'Enable translation to {lang}.')
            # Connect checkbox toggle to emit target_lang_toggled signal
            checkbox.toggled.connect(lambda state, la=lang: self.target_lang_toggled.emit(la, state))

            voice_selector = QComboBox()
            voices = TRANSLATOR['aws'][lang].get('voice_ids', [])  # Get available voices for this language
            voice_selector.addItems(voices)

            voice_selector.setToolTip(f'Select the voice for {lang} translation output.')

            if lang in self._aws_settings.target_languages:
                checkbox.setChecked(True)
                voice_selector.setEnabled(True)
                voice_selector.setCurrentText(self._aws_settings.target_languages[lang].voice_id)
            else:
                voice_selector.setEnabled(False)  # Initially disabled until checkbox is checked

            # Connect checkbox toggle to enable/disable voice selector
            checkbox.toggled.connect(
                lambda state, vs=voice_selector, la=lang: self._toggle_voice_selector(state, vs, la),
            )

            lang_selection_layout.addWidget(checkbox)
            lang_selection_layout.addWidget(voice_selector)

            target_grid_layout.addLayout(lang_selection_layout, row, col)

            col += 1
            if col >= num_cols:
                col = 0
                row += 1

            self.aws_target_lang_checkboxes[lang] = checkbox
            self.aws_voice_selectors[lang] = voice_selector

        # Add expanding spacers to ensure proper layout and fill remaining space
        if col > 0:  # If the last row is not full, add an expanding spacer to fill the remaining columns
            target_grid_layout.addItem(
                QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), row, col
            )
        # Add a vertical expanding spacer at the end of the grid layout to push content upwards
        target_grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), row + 1, 0, 1, num_cols
        )

        scroll_area.setWidget(scroll_content_widget)
        language_settings_layout.addWidget(scroll_area)  # Add scroll area to language group
        main_v_layout.addWidget(language_settings_group)  # Add the entire language group to the main layout

        # Ensure the AWSConfigWidget itself expands vertically to fill available space
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        # Initialize target language states based on the current source language
        self._update_target_languages(self.aws_source_lang.currentText())

    def _check_aws_credentials(self) -> None:
        """
        Checks if AWS credentials (~/.aws/credentials) and a default region
        in the configuration file (~/.aws/config) exist and are properly configured.
        Updates the status label accordingly.
        """
        _, credentials_path = AWSWidget.get_aws_cred_path()
        status_text = 'Status: '
        creds_found = False

        # Check credentials file for access keys
        if os.path.exists(credentials_path):
            try:
                credentials_parser = configparser.ConfigParser()
                credentials_parser.read(credentials_path)
                if (
                    'default' in credentials_parser
                    and 'aws_access_key_id' in credentials_parser['default']
                    and 'aws_secret_access_key' in credentials_parser['default']
                ):
                    creds_found = True
            except Exception as e:
                LOGGER.error(f'Error reading AWS credentials file ({credentials_path}): {e}')

        # Update status label based on findings
        if creds_found:
            status_text += "<font color='green'>Credentials OK.</font>"
        else:
            status_text += "<font color='red'>Credentials NOT found.</font>"

        self.credentials_status_label.setText(status_text)

    def _open_credentials_dialog(self) -> None:
        """
        Opens a dialog for the user to manage (enter/save) their AWS credentials and default region.
        After the dialog closes, the credential status is re-checked.
        """
        dialog = self.AWSCredentialsDialog(self)
        if dialog.exec() == QDialog.accepted:
            self._check_aws_credentials()  # Re-check status after dialog is accepted
            LOGGER.debug('AWS credentials updated or saved.')

    def _toggle_voice_selector(self, state: bool, voice_selector: QComboBox, lang: str) -> None:
        """
        Toggles the enabled state of a voice selector QComboBox based on
        the corresponding language checkbox state.

        Args:
            state (bool): True if the checkbox is checked, False otherwise.
            voice_selector (QComboBox): The voice selector QComboBox to toggle.
            lang (str): The language code associated with the voice selector.
        """
        has_voices = TRANSLATOR['aws'][lang].get('voice_ids', [])
        # Enable if checkbox is checked AND it's not the source language AND voices are available
        voice_selector.setEnabled(state and (lang != self.aws_source_lang.currentText()) and bool(has_voices))

    def _update_target_languages(self, selected_source: str) -> None:
        """
        Updates the enabled state of target language checkboxes and voice selectors
        based on the currently selected source language. The source language cannot
        be a target language.

        Args:
            selected_source (str): The currently selected source language code.
        """
        for lang, checkbox in self.aws_target_lang_checkboxes.items():
            is_source = lang == selected_source
            checkbox.setEnabled(not is_source)  # Disable source language checkbox

            if is_source:
                checkbox.setChecked(False)  # Uncheck source language checkbox if it was active

            has_voices = TRANSLATOR['aws'][lang].get('voice_ids', [])
            # Enable/disable voice selector based on checkbox state,
            # whether it's the source language, and if voices are available.
            self.aws_voice_selectors[lang].setEnabled(checkbox.isChecked() and not is_source and bool(has_voices))
            self.aws_voice_selectors[lang].setStatusTip(f'Select the voice for {lang} translation output.')
            self.aws_voice_selectors[lang].setToolTip(f'Select the voice for {lang} translation output.')

    class AWSCredentialsDialog(QDialog):
        """
        A dialog for entering and saving AWS Access Key ID, Secret Access Key,
        and a default region to the standard ~/.aws/credentials and ~/.aws/config files.
        """

        def __init__(self, parent: Optional[QWidget] = None):
            """
            Initializes the AWSCredentialsDialog.
            Args:
                parent (QWidget, optional): The parent widget. Defaults to None.
            """
            super().__init__(parent)
            self.setWindowTitle('Manage AWS Credentials')
            self.setMinimumWidth(400)
            self._aws_path, self._credentials_path = AWSWidget.get_aws_cred_path()
            self._setup_ui()
            self._load_existing_credentials()  # Load existing data on dialog open

        def _setup_ui(self) -> None:
            """
            Sets up the user interface for the credentials dialog.
            Includes input fields for Access Key ID, Secret Access Key, and Default Region.
            """
            main_layout = QVBoxLayout(self)
            form_layout = QFormLayout()

            self.access_key_id_input = QLineEdit()
            self.access_key_id_input.setMinimumWidth(330)
            self.access_key_id_input.setPlaceholderText('Enter AWS Access Key ID (e.g., AKIAIOSFODNN7EXAMPLE)')
            form_layout.addRow('Access Key ID:', self.access_key_id_input)

            secret_layout = QHBoxLayout()
            self.secret_access_key_input = QLineEdit()
            self.secret_access_key_input.setMinimumWidth(330)
            self.secret_access_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.secret_access_key_input.setPlaceholderText(
                'Enter AWS Secret Access Key (e.g. wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY)'
            )

            self.toggle_secret_btn = QToolButton()
            self.toggle_secret_btn.setCheckable(True)
            self.toggle_secret_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
            self.toggle_secret_btn.setToolTip('Show/Hide password')
            self.toggle_secret_btn.toggled.connect(self._toggle_secret_visibility)

            secret_layout.addWidget(self.secret_access_key_input)
            secret_layout.addWidget(self.toggle_secret_btn)
            form_layout.addRow('Secret Access Key:', secret_layout)

            main_layout.addLayout(form_layout)

            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)
            main_layout.addWidget(self.button_box)

        def _toggle_secret_visibility(self, checked: bool) -> None:
            """
            Shows or hides the secret access key input based on the toggle button state.
            """
            if checked:
                self.secret_access_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.secret_access_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        def _load_existing_credentials(self) -> None:
            """
            Loads existing AWS credentials
            """

            # Load credentials from ~/.aws/credentials
            if os.path.exists(self._credentials_path):
                try:
                    credentials_parser = configparser.ConfigParser()
                    credentials_parser.read(self._credentials_path)
                    if 'default' in credentials_parser:
                        self.access_key_id_input.setText(credentials_parser['default'].get('aws_access_key_id', ''))
                        self.secret_access_key_input.setText(
                            credentials_parser['default'].get('aws_secret_access_key', '')
                        )
                except Exception as e:
                    LOGGER.warning(f'Could not read AWS credentials file "{self._credentials_path}": {e}')
                    QMessageBox.warning(self, 'Load Error', f'Could not read credentials file: {e}')

        def accept(self) -> None:
            """
            Handles saving credentials and default region when the OK button is pressed.
            Validates input and writes to ~/.aws/credentials and ~/.aws/config files.
            """
            access_key_id = self.access_key_id_input.text().strip()
            secret_access_key = self.secret_access_key_input.text().strip()

            # Prompt for confirmation if all fields are empty, implying a clear operation
            if not access_key_id and not secret_access_key:
                reply = QMessageBox.question(
                    self,
                    'Confirm Clear',
                    'All fields are empty. Do you want to clear your AWS credentials and region files?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return  # Do not save and do not close dialog

            # Warn if credentials are incomplete but some input is provided
            if (access_key_id or secret_access_key) and (not access_key_id or not secret_access_key):
                QMessageBox.warning(
                    self,
                    'Input Error',
                    'Both Access Key ID and Secret Access Key must be provided to save credentials.',
                )
                return  # Do not save and do not close dialog

            try:
                os.makedirs(self._aws_path, exist_ok=True)

                credentials_config = configparser.ConfigParser()
                # Read existing data to preserve other profiles if they exist
                if os.path.exists(self._credentials_path):
                    credentials_config.read(self._credentials_path)

                if not access_key_id and not secret_access_key:
                    # If credentials fields are empty, remove the 'default' section if it exists
                    if 'default' in credentials_config:
                        del credentials_config['default']
                else:
                    credentials_config['default'] = {
                        'aws_access_key_id': access_key_id,
                        'aws_secret_access_key': secret_access_key,
                    }

                # Write credentials with appropriate permissions (read/write for owner)
                # Note: configparser.write might not set specific permissions,
                # but typically standard open() would respect umask.
                # For stronger security on Unix-like systems, os.chmod might be used.
                with open(self._credentials_path, 'w') as cred_file:
                    credentials_config.write(cred_file)

                LOGGER.debug('AWS credentials and config saved successfully.')
                super().accept()
            except Exception as e:
                LOGGER.error(f'Failed to save AWS credentials/config: {e}')
                QMessageBox.critical(self, 'Save Error', f'Failed to save AWS credentials/config: {e}')
