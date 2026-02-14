import logging
import os

from PySide6.QtCore import QFile, QSize, Qt, QTextStream, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from config.config_manager import ConfigManager
from config.model.config_models import (
    AWSSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
    TranslatorSettings,
    UserConfig,
)
from controllers.translation_controller import TranslationController
from gui_elements.audio_input_widget import AudioInputWidget
from gui_elements.audio_output_widget import AudioOutputWidget
from gui_elements.live_output_widget import LiveOutputWidget
from gui_elements.text_edit_logger import QTextEditLogger
from gui_elements.translator_widget import TranslatorWidget
from translators.translation_callbacks import TranslationCallbacks

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    # Signals for thread-safe UI updates
    status_message_signal = Signal(str, int)
    status_label_signal = Signal(str)
    start_button_signal = Signal(bool)
    stop_button_signal = Signal(bool)

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.setWindowTitle('Live Translation')
        self.setMinimumSize(1200, 850)
        self._config_manager = config_manager
        self._text_edit_logger = self._get_edit_logger()

        # Actions are created here and reused
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()

        # Initialize the controller
        self._controller = TranslationController(
            callbacks=TranslationCallbacks(
                update_source_field=self.live_output_dashboard.update_source_transcription_field,
                update_target_field=self.live_output_dashboard.update_target_transcription_field,
            )
        )

        self._connect_signals()

        # Connect the target transcribe dashboard to the translator tab widget
        self.translator_tab_widget.add_target_lang_signal(self.live_output_dashboard.update_target_transcript_outputs)

        # Apply initial theme
        self._current_theme = getattr(self._config_manager.config, 'theme', 'light')
        self._apply_theme(self._current_theme)

    def _connect_signals(self):
        """Connects all signals to their respective slots."""
        # Connect UI signals
        self.status_message_signal.connect(self._statusBar.showMessage)
        self.status_message_signal.connect(self._statusBar.showMessage)
        self.status_label_signal.connect(self._update_status_label)
        self.start_button_signal.connect(self.start_action.setEnabled)
        self.start_button_signal.connect(self.start_action.setEnabled)
        self.stop_button_signal.connect(self.stop_action.setEnabled)

        # Connect controller signals
        self._controller.status_message_signal.connect(self.status_message_signal.emit)
        self._controller.status_label_signal.connect(self.status_label_signal.emit)
        self._controller.start_button_enabled.connect(self.start_button_signal.emit)
        self._controller.stop_button_enabled.connect(self.stop_button_signal.emit)

        LOGGER.debug('All signals connected.')

    def _create_actions(self):
        """Initializes all QActions for reuse."""
        self.load_action = QAction('&Load Configuration...', self)
        self.load_action.setShortcut('Ctrl+L')
        self.load_action.setStatusTip('Load configuration from a JSON file')
        self.load_action.triggered.connect(self._load_config)

        self.save_action = QAction('&Save Configuration...', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.setStatusTip('Save current configuration to a JSON file')
        self.save_action.triggered.connect(self._save_config)

        self.exit_action = QAction('&Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit the application')
        self.exit_action.triggered.connect(self.close)

        self.start_action = QAction('Start Translation', self)
        self.start_action.triggered.connect(self._handle_start_button)
        self.start_action.setStatusTip('Start the translation service')

        self.stop_action = QAction('Stop Translation', self)
        self.stop_action.triggered.connect(self._handle_stop_button)
        self.stop_action.setStatusTip('Stop the translation service')
        self.stop_action.setEnabled(False)

        self.toggle_theme_action = QAction('Toggle Theme (Dark/Light)', self)
        self.toggle_theme_action.setStatusTip('Switch between Dark and Light mode')
        self.toggle_theme_action.triggered.connect(self._toggle_theme)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        view_menu = menu_bar.addMenu('&View')
        view_menu.addAction(self.toggle_theme_action)

    def _create_tool_bar(self):
        tool_bar = QToolBar('File Actions')
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        tool_bar.setIconSize(QSize(32, 32))
        tool_bar.addAction(self.load_action)
        tool_bar.addAction(self.save_action)
        tool_bar.addSeparator()
        tool_bar.addAction(self.start_action)
        tool_bar.addAction(self.stop_action)
        tool_bar.addSeparator()
        self.status_label = QLabel('Status: Ready')
        self.status_label.setStyleSheet('font-weight: bold; padding: 0 10px;')
        tool_bar.addWidget(self.status_label)

    def _create_central_widget(self):
        config = self._config_manager.config
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        content_layout = QHBoxLayout()

        self.tabs_config = QTabWidget(tabPosition=QTabWidget.TabPosition.North)
        self.tabs_config.tabBar().setUsesScrollButtons(False)
        self.audio_tab_widget = AudioInputWidget(config.input_settings)
        self.translator_tab_widget = TranslatorWidget(config.translator_settings)
        self.output_tab_widget = AudioOutputWidget(config.output_settings)
        self.tabs_config.addTab(self.audio_tab_widget, 'Audio')
        self.tabs_config.addTab(self.translator_tab_widget, 'Translator')
        self.tabs_config.addTab(self.output_tab_widget, 'Output')
        content_layout.addWidget(self.tabs_config, 0.8)

        separator_line_v = QFrame(frameShape=QFrame.Shape.VLine, frameShadow=QFrame.Shadow.Sunken)
        content_layout.addWidget(separator_line_v)

        self.live_output_dashboard = LiveOutputWidget(config.translator_settings, self._text_edit_logger)
        content_layout.addWidget(self.live_output_dashboard, 1)
        main_layout.addLayout(content_layout, 1)

    def _get_edit_logger(self) -> QTextEditLogger:
        text_edit_logger = QTextEditLogger(self)
        logging.getLogger().addHandler(text_edit_logger)

        # Remove any existing StreamHandlers to avoid duplicate logs
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler):
                logging.getLogger().removeHandler(handler)

        return text_edit_logger

    def _create_status_bar(self):
        self._statusBar = QStatusBar()
        self.setStatusBar(self._statusBar)
        self._statusBar.showMessage('Application Ready', 3000)

    def _load_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select configuration file', '', 'JSON Files (*.json)')
        if not file_path:
            self._statusBar.showMessage('No configuration file selected.', 3000)
            return

        try:
            config = self._config_manager.load_config(file_path)
            self._populate_config_data(config)
            self._statusBar.showMessage(f'Configuration loaded from {file_path}', 3000)
            self._populate_config_data(config)
            self._statusBar.showMessage(f'Configuration loaded from {file_path}', 3000)
            self._update_status_label('Status: Config Loaded')
            LOGGER.debug(f'Configuration loaded from "{file_path}".')
            LOGGER.debug(f'Configuration loaded from "{file_path}".')
        except Exception as e:
            error_msg = f'Error loading configuration from "{file_path}": {e}'
            LOGGER.error(error_msg, exc_info=True)
            QMessageBox.critical(self, 'Configuration Load Error', error_msg)
            self._statusBar.showMessage('Configuration load failed.', 5000)
            self._statusBar.showMessage('Configuration load failed.', 5000)
            self._update_status_label('Status: Config Error')

    def _save_config(self):
        reply = QMessageBox.question(
            self,
            'Save Configuration',
            'Are you sure you want to overwrite the configuration file with the current settings?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self._statusBar.showMessage('Save operation cancelled.', 3000)
            LOGGER.debug('Configuration save cancelled by user.')
            return

        try:
            config_data = self._collect_config_data()
            self._config_manager.store_config(config_data)
            self._statusBar.showMessage('Configuration saved.', 3000)
            LOGGER.debug('Configuration saved successfully.')
        except Exception as e:
            error_msg = f'Error saving configuration: {e}'
            LOGGER.error(error_msg, exc_info=True)
            self._statusBar.showMessage(error_msg, 5000)
            QMessageBox.critical(self, 'Configuration Save Error', error_msg)

    def _populate_config_data(self, config: UserConfig):
        self.audio_tab_widget.update_settings(config.input_settings)
        self.translator_tab_widget.update_settings(config.translator_settings)
        self.output_tab_widget.update_settings(config.output_settings)
        self.live_output_dashboard.update_settings(config.translator_settings)
        LOGGER.debug('GUI widgets populated with new configuration data.')

    def _collect_config_data(self) -> UserConfig:
        """Collects all configuration data from the GUI widgets."""
        LOGGER.debug('Collecting configuration data from GUI.')
        try:
            input_settings = InputSettings(
                input_device=self.audio_tab_widget.input_device.currentText(),
                input_device_index=self.audio_tab_widget.input_device.currentData(),
                input_channels=self.audio_tab_widget.input_channels.value(),
                input_sample_rate=self.audio_tab_widget.input_sample_rate.value(),
            )
            output_settings = OutputSettings(
                output_method=self.output_tab_widget.output_method.currentText(),
                output_sample_rate=self.output_tab_widget.output_sample_rate.value(),
                chunk_len=self.output_tab_widget.chunk_len.value(),
                speaker_settings=SpeakerSettings(
                    output_device=self.output_tab_widget.speaker_widget.output_device.currentText(),
                    output_device_index=self.output_tab_widget.speaker_widget.output_device.currentData(),
                ),
                mumble_settings=MumbleSettings(
                    ip_address=self.output_tab_widget.mumble_widget.mumble_ip.text(),
                    port=int(self.output_tab_widget.mumble_widget.mumble_port.text()),
                    language_channel_mapping=self.output_tab_widget.mumble_widget.get_current_mappings(),
                ),
            )
            aws_widget = self.translator_tab_widget.aws_tab_widget
            target_languages = {
                lang: LanguageSettings(
                    voice_id=aws_widget.aws_voice_selectors[lang].currentText(),
                    show_transcript=self.live_output_dashboard.target_transcript_checkboxes[lang].isChecked(),
                )
                for lang, cb in aws_widget.aws_target_lang_checkboxes.items()
                if cb.isChecked()
            }
            translator_settings = TranslatorSettings(
                translator=self.translator_tab_widget.translator_select.currentText(),
                aws_settings=AWSSettings(
                    region=self.translator_tab_widget.aws_tab_widget.aws_region_select.currentData(),
                    source_language=self.translator_tab_widget.aws_tab_widget.aws_source_lang.currentText(),
                    show_source_transcript=self.live_output_dashboard.show_source_transcript_checkbox.isChecked(),
                    target_languages=target_languages,
                ),
            )
            return UserConfig(
                input_settings,
                output_settings,
                translator_settings,
                theme=self._current_theme,
            )
        except Exception as e:
            LOGGER.error('Error while collecting config data from GUI widgets.', exc_info=True)
            raise ValueError('Invalid configuration data in GUI. Please check all fields.') from e

    def _handle_start_button(self):
        """Delegates service startup to the controller."""
        try:
            self.live_output_dashboard.clear_transcripts()
            current_config = self._collect_config_data()
            self._controller.start_service(current_config)
        except Exception as e:
            QMessageBox.warning(self, 'Validation Error', str(e))

    def _handle_stop_button(self):
        """Delegates service stop to the controller."""
        self._controller.stop_service()

    def closeEvent(self, event):
        """Handles graceful shutdown when the main window is closed."""
        LOGGER.info('Application closing. Initiating graceful shutdown.')
        self.stop_action.setEnabled(False)
        self._controller.stop_service()
        event.accept()

    def _toggle_theme(self):
        """Switches between dark and light themes."""
        new_theme = 'light' if self._current_theme == 'dark' else 'dark'
        self._apply_theme(new_theme)

    def _apply_theme(self, theme_name: str):
        """Loads and applies the specified theme stylesheet."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_file = os.path.join(base_dir, 'styles', f'{theme_name}_theme.qss')
        file = QFile(style_file)
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(file)
            style_content = stream.readAll()

            # Replace placeholder with absolute path to styles directory (for icons)
            # Use forward slashes for QSS compatibility
            style_dir_abs = os.path.dirname(os.path.abspath(style_file)).replace('\\', '/')
            style_content = style_content.replace('%STYLE_DIR%', style_dir_abs)

            QApplication.instance().setStyleSheet(style_content)
            self._current_theme = theme_name
            self._update_icons()
            LOGGER.info(f'Switching to {theme_name} theme. Loaded from {style_file}')
        else:
            LOGGER.error(f'Failed to open stylesheet: {style_file}')
            self._statusBar.showMessage(f'Failed to load {theme_name} theme.', 3000)

    def _update_icons(self):
        """Updates icons based on the current theme."""
        suffix = '_white' if self._current_theme == 'dark' else ''
        icon_map = {
            self.load_action: f'open{suffix}.png',
            self.save_action: f'save{suffix}.png',
            self.start_action: f'start{suffix}.png',
            self.stop_action: f'stop{suffix}.png',
        }

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, 'styles', 'icons')

        for action, icon_name in icon_map.items():
            icon_path = os.path.join(icons_dir, icon_name)
            if os.path.exists(icon_path):
                action.setIcon(QIcon(icon_path))
            else:
                LOGGER.warning(f'Icon not found: {icon_path}')

    def _update_status_label(self, text: str):
        """Updates the status label text and color based on the content."""
        self.status_label.setText(text)

        # Default style
        style = 'font-weight: bold; padding: 0 10px;'

        lower_text = text.lower()
        if 'running' in lower_text:
            # Green for running
            style += ' color: #2ecc71;'
        elif 'error' in lower_text:
            # Red for errors
            style += ' color: #e74c3c;'

        self.status_label.setStyleSheet(style)
