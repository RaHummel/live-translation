import logging
import os
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import GoogleSettings
from constants import GOOGLE_CHIRP3_HD_VOICES, GOOGLE_ENDPOINTING_OPTIONS, GOOGLE_REGIONS, TRANSLATOR
from gui_elements.base_translator_widget import BaseTranslatorProviderWidget

LOGGER = logging.getLogger(__name__)


class GoogleWidget(BaseTranslatorProviderWidget):
    """
    A widget for configuring Google Cloud specific translation settings.
    It groups connection settings (Region, Credentials) and language settings (Source, Target).
    """

    def __init__(self, google_settings: GoogleSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._google_settings = google_settings
        self._source_lang_combo: QComboBox | None = None
        self._credentials_path: str = google_settings.credentials_path
        self._setup_ui()
        self._check_google_credentials()

    # ------------------------------------------------------------------
    # BaseTranslatorProviderWidget hooks
    # ------------------------------------------------------------------

    def _get_provider_key(self) -> str:
        return 'google'

    def _get_engine_names(self) -> List[str]:
        return ['standard', 'wavenet', 'neural2', 'studio', 'chirp3-hd']

    def _get_source_language(self) -> str:
        if self._source_lang_combo:
            return self._source_lang_combo.currentText()
        return self._google_settings.source_language

    def _get_source_language_combo(self) -> QComboBox:
        if self._source_lang_combo is None:
            self._source_lang_combo = QComboBox()
            languages = sorted(
                set(
                    list(TRANSLATOR['google']['standard'].keys())
                    + list(TRANSLATOR['google']['wavenet'].keys())
                    + list(TRANSLATOR['google']['neural2'].keys())
                    + list(TRANSLATOR['google']['studio'].keys())
                    + list(GOOGLE_CHIRP3_HD_VOICES.keys())
                )
            )
            self._source_lang_combo.addItems(languages)
            self._source_lang_combo.setCurrentText(self._google_settings.source_language)
            self._source_lang_combo.setStatusTip('Select the language spoken by the input audio.')
            self._source_lang_combo.currentTextChanged.connect(self._update_target_languages)
        return self._source_lang_combo

    def _build_connection_ui(self, parent_layout: QVBoxLayout) -> None:
        google_connection_group = QGroupBox('Google Connection Settings')
        google_connection_v_layout = QVBoxLayout(google_connection_group)

        # Region Selection
        region_form_layout = QFormLayout()
        region_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignHCenter)
        region_form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter)
        region_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.google_region_select = QComboBox()
        for region_code, region_name in GOOGLE_REGIONS.items():
            self.google_region_select.addItem(f'{region_code} ({region_name})', region_code)
        region = self._google_settings.region
        self.google_region_select.setCurrentText(f'{region} ({GOOGLE_REGIONS[region]})')
        self.google_region_select.setStatusTip('Select the Google Cloud region for Speech-to-Text.')
        self.google_region_select.setToolTip('Choose your Google Cloud region.')
        region_form_layout.addRow('Region:', self.google_region_select)
        google_connection_v_layout.addLayout(region_form_layout)

        # Credentials status label
        credentials_status_layout = QHBoxLayout()
        self.credentials_status_label = QLabel('Status: Initializing...')
        self.credentials_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credentials_status_layout.addWidget(self.credentials_status_label)
        google_connection_v_layout.addLayout(credentials_status_layout)

        # Manage Credentials button
        credential_buttons_layout = QHBoxLayout()
        credential_buttons_layout.addStretch()
        self.manage_credentials_button = QPushButton('Manage Credentials')
        self.manage_credentials_button.clicked.connect(self._open_credentials_dialog)
        credential_buttons_layout.addWidget(self.manage_credentials_button)
        credential_buttons_layout.addStretch()
        google_connection_v_layout.addLayout(credential_buttons_layout)

        parent_layout.addWidget(google_connection_group)

    def _build_extra_language_options(self, layout: QFormLayout) -> None:
        """Add endpointing sensitivity selector below source language."""
        self.google_endpointing_select = QComboBox()
        self.google_endpointing_select.addItems(GOOGLE_ENDPOINTING_OPTIONS.keys())
        self.google_endpointing_select.setCurrentText(
            self._endpointing_label_for_value(self._google_settings.endpointing_sensitivity)
        )
        self.google_endpointing_select.setToolTip(
            'Adjusts how quickly the system decides that the speaker has finished speaking'
        )
        self.google_endpointing_select.setStatusTip('Faster Response = may cut off speech earlier.')
        layout.addRow('Response Speed', self.google_endpointing_select)

    def update_settings(self, google_settings: GoogleSettings) -> None:
        """Updates the Google settings in the widget."""
        region = google_settings.region
        self.google_region_select.setCurrentText(f'{region} ({GOOGLE_REGIONS[region]})')
        source_lang_combo = self._get_source_language_combo()
        source_lang_combo.setCurrentText(google_settings.source_language)
        self._credentials_path = google_settings.credentials_path
        self.google_endpointing_select.setCurrentText(
            self._endpointing_label_for_value(google_settings.endpointing_sensitivity)
        )
        self._apply_target_language_state(google_settings.target_languages)
        self._google_settings = google_settings
        self._check_google_credentials()

    # Backwards-compatible property aliases
    @property
    def google_source_lang(self) -> QComboBox:
        return self._get_source_language_combo()

    @property
    def google_engine_select(self) -> QComboBox:
        return self.engine_select

    @property
    def google_target_lang_checkboxes(self) -> Dict[str, object]:
        return self.target_lang_checkboxes

    @property
    def google_voice_selectors(self) -> Dict[str, QComboBox]:
        return self.voice_selectors

    def get_credentials_path(self) -> str:
        return self._credentials_path

    def get_region(self) -> str:
        return self.google_region_select.currentData()

    def get_endpointing_sensitivity(self) -> str:
        return GOOGLE_ENDPOINTING_OPTIONS[self.google_endpointing_select.currentText()]

    def _setup_ui(self) -> None:
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)

        self._build_connection_ui(main_v_layout)
        self._setup_language_ui(main_v_layout)
        self._init_target_state(self._google_settings.target_languages)

    def _check_google_credentials(self) -> None:
        status_text = 'Status: '
        if self._credentials_path and os.path.exists(self._credentials_path):
            status_text += "<font color='green'>Credentials OK.</font>"
        else:
            status_text += "<font color='red'>Credentials NOT found.</font>"
        self.credentials_status_label.setText(status_text)

    def _open_credentials_dialog(self) -> None:
        dialog = self.GoogleCredentialsDialog(self._credentials_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._credentials_path = dialog.get_credentials_path()
            self._check_google_credentials()
            LOGGER.info('Google credentials path updated.')

    @staticmethod
    def _endpointing_label_for_value(value: str) -> str:
        for label, option_value in GOOGLE_ENDPOINTING_OPTIONS.items():
            if option_value == value:
                return label
        return 'Fast'

    class GoogleCredentialsDialog(QDialog):
        """Dialog for selecting the Google Cloud Service Account JSON key file."""

        def __init__(self, current_path: str = '', parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setWindowTitle('Manage Google Cloud Credentials')
            self.setMinimumWidth(500)
            self._credentials_path = current_path
            self._setup_ui()

        def _setup_ui(self) -> None:
            main_layout = QVBoxLayout(self)
            form_layout = QFormLayout()

            path_layout = QHBoxLayout()
            self.path_input = QLineEdit()
            self.path_input.setMinimumWidth(380)
            self.path_input.setPlaceholderText('Path to Google Cloud Service Account JSON...')
            self.path_input.setText(self._credentials_path)
            self.path_input.setReadOnly(True)

            browse_button = QPushButton('Browse...')
            browse_button.clicked.connect(self._browse)

            path_layout.addWidget(self.path_input)
            path_layout.addWidget(browse_button)
            form_layout.addRow('Credentials JSON:', path_layout)
            main_layout.addLayout(form_layout)

            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)
            main_layout.addWidget(self.button_box)

        def _browse(self) -> None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Select Google Cloud Service Account JSON', '', 'JSON Files (*.json)'
            )
            if file_path:
                self.path_input.setText(file_path)

        def get_credentials_path(self) -> str:
            return self.path_input.text()
