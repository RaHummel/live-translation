import configparser
import logging
import os
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import AWSSettings
from constants import AWS_REGIONS, TRANSLATOR
from gui_elements.base_translator_widget import BaseTranslatorProviderWidget

LOGGER = logging.getLogger(__name__)


class AWSWidget(BaseTranslatorProviderWidget):
    """
    A widget for configuring Amazon Web Services (AWS) specific translation settings.
    It groups connection settings (Region, Credentials) and language settings (Source, Target).
    """

    aws_region_changed = Signal(str)

    def __init__(self, aws_settings: AWSSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._aws_settings = aws_settings
        self._source_lang_combo: QComboBox | None = None
        self._setup_ui()
        self._check_aws_credentials()

    def _get_provider_key(self) -> str:
        return 'aws'

    def _get_engine_names(self) -> List[str]:
        return ['standard', 'neural']

    def _get_source_language(self) -> str:
        return self._source_lang_combo.currentText() if self._source_lang_combo else self._aws_settings.source_language

    def _get_source_language_combo(self) -> QComboBox:
        if self._source_lang_combo is None:
            self._source_lang_combo = QComboBox()
            languages = sorted(
                set(list(TRANSLATOR['aws']['standard'].keys()) + list(TRANSLATOR['aws']['neural'].keys()))
            )
            self._source_lang_combo.addItems(languages)
            self._source_lang_combo.setCurrentText(self._aws_settings.source_language)
            self._source_lang_combo.setStatusTip('Select the language spoken by the input audio.')
            self._source_lang_combo.setToolTip('Select the language spoken by the input audio.')
            self._source_lang_combo.currentTextChanged.connect(self._update_target_languages)
        return self._source_lang_combo

    def _build_connection_ui(self, parent_layout: QVBoxLayout) -> None:
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

        parent_layout.addWidget(aws_connection_group)

    def update_settings(self, aws_settings: AWSSettings) -> None:
        """Updates the AWS settings in the widget."""
        self.aws_region_select.setCurrentText(f'{aws_settings.region} ({AWS_REGIONS[aws_settings.region]})')
        source_lang_combo = self._get_source_language_combo()
        source_lang_combo.setCurrentText(aws_settings.source_language)
        self._apply_target_language_state(aws_settings.target_languages)
        self._aws_settings = aws_settings

    # Backwards-compatible property aliases
    @property
    def aws_source_lang(self) -> QComboBox:
        return self._get_source_language_combo()

    @property
    def aws_engine_select(self) -> QComboBox:
        return self.engine_select

    @property
    def aws_target_lang_checkboxes(self) -> Dict[str, object]:
        return self.target_lang_checkboxes

    @property
    def aws_voice_selectors(self) -> Dict[str, QComboBox]:
        return self.voice_selectors

    @staticmethod
    def get_aws_cred_path() -> Tuple[str, str]:
        aws_dir = os.path.expanduser('~/.aws')
        return aws_dir, os.path.join(aws_dir, 'credentials')

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)

        self._build_connection_ui(main_v_layout)
        self._setup_language_ui(main_v_layout)
        self._init_target_state(self._aws_settings.target_languages)

    def _check_aws_credentials(self) -> None:
        _, credentials_path = AWSWidget.get_aws_cred_path()
        status_text = 'Status: '
        creds_found = False

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

        if creds_found:
            status_text += "<font color='green'>Credentials OK.</font>"
        else:
            status_text += "<font color='red'>Credentials NOT found.</font>"

        self.credentials_status_label.setText(status_text)

    def _open_credentials_dialog(self) -> None:
        dialog = self.AWSCredentialsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._check_aws_credentials()
            LOGGER.info('AWS credentials updated or saved.')

    class AWSCredentialsDialog(QDialog):
        """Dialog for entering and saving AWS credentials."""

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setWindowTitle('Manage AWS Credentials')
            self.setMinimumWidth(400)
            self._aws_path, self._credentials_path = AWSWidget.get_aws_cred_path()
            self._setup_ui()
            self._load_existing_credentials()

        def _setup_ui(self) -> None:
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
            if checked:
                self.secret_access_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.secret_access_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        def _load_existing_credentials(self) -> None:
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
            access_key_id = self.access_key_id_input.text().strip()
            secret_access_key = self.secret_access_key_input.text().strip()

            if not access_key_id and not secret_access_key:
                reply = QMessageBox.question(
                    self,
                    'Confirm Clear',
                    'All fields are empty. Do you want to clear your AWS credentials and region files?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            if (access_key_id or secret_access_key) and (not access_key_id or not secret_access_key):
                QMessageBox.warning(
                    self,
                    'Input Error',
                    'Both Access Key ID and Secret Access Key must be provided to save credentials.',
                )
                return

            try:
                os.makedirs(self._aws_path, exist_ok=True)

                credentials_config = configparser.ConfigParser()
                if os.path.exists(self._credentials_path):
                    credentials_config.read(self._credentials_path)

                if not access_key_id and not secret_access_key:
                    if 'default' in credentials_config:
                        del credentials_config['default']
                else:
                    credentials_config['default'] = {
                        'aws_access_key_id': access_key_id,
                        'aws_secret_access_key': secret_access_key,
                    }

                with open(self._credentials_path, 'w') as cred_file:
                    credentials_config.write(cred_file)

                LOGGER.debug('AWS credentials and config saved successfully.')
                super().accept()
            except Exception as e:
                LOGGER.error(f'Failed to save AWS credentials/config: {e}')
                QMessageBox.critical(self, 'Save Error', f'Failed to save AWS credentials/config: {e}')
