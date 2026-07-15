import logging
import socket
import sys

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config.config_manager import ConfigManager
from config.model.config_models import MumbleSettings
from constants import MUMBLE_DEFAULT_PORT, TRANSLATOR
from sound_outputs.mumble_installer import FirewallRuleWorker, MumbleInstaller
from utils.language_names import display_name, sorted_by_display_name
from utils.mumble_paths import find_murmur_binary, resolve_murmur_dir
from utils.qt_worker import run_in_thread
from utils.windows_firewall import firewall_rules_exist

LOGGER = logging.getLogger(__name__)


class MumbleWidget(QWidget):
    start_server_requested = Signal()
    stop_server_requested = Signal()

    def __init__(self, mumble_settings: MumbleSettings, parent=None):
        super().__init__(parent)
        self._mumble_settings = mumble_settings
        self.channel_mapping = self._mumble_settings.language_channel_mapping
        self._murmur_dir = ConfigManager.get_app_config_dir() / 'murmur'
        self._setup_ui()

    @property
    def use_custom_server(self) -> bool:
        return self._custom_server_checkbox.isChecked()

    def update_settings(self, mumble_settings: MumbleSettings):
        """
        Updates the Mumble settings in the widget.
        Args:
            mumble_settings (MumbleSettings): User specific Mumble settings.
        """
        self.mumble_ip.setText(mumble_settings.ip_address)
        self.mumble_port.setText(str(mumble_settings.port))
        self.channel_mapping = mumble_settings.language_channel_mapping
        self._update_mapping_list_widget()
        self._custom_server_checkbox.setChecked(mumble_settings.use_custom_server)
        self._mumble_settings = mumble_settings

    def set_server_running(self, running: bool):
        """Update button enabled states to reflect the current server state."""
        self._start_server_btn.setEnabled(not running)
        self._stop_server_btn.setEnabled(running)
        if running:
            self._set_status_label('Running', '#2ecc71', address=self._embedded_server_address())
        else:
            self._set_status_label('Stopped', '#e74c3c')

    def set_server_status(self, status: str):
        """Update the status label text directly from MumbleServerController.status_changed."""
        lower = status.lower()
        if 'running' in lower:
            color = '#2ecc71'
            address = self._embedded_server_address()
        elif 'error' in lower or 'stopped' in lower:
            color = '#e74c3c'
            address = None
        else:
            color = '#f39c12'  # orange for transitional states (starting, stopping)
            address = None
        self._set_status_label(status, color, address=address)

    def eventFilter(self, obj, event):
        if (
            obj is self.current_mappings_list
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)
        ):
            selected_items = self.current_mappings_list.selectedItems()
            if selected_items:
                self._perform_removal(selected_items[0])
                return True
        return super().eventFilter(obj, event)

    def get_current_mappings(self):
        return self.channel_mapping

    def _is_murmur_installed(self) -> bool:
        return find_murmur_binary(resolve_murmur_dir(self._murmur_dir)) is not None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Embedded server section (always visible, default mode) ---
        embedded_group = QGroupBox('Mumble Server')
        embedded_layout = QVBoxLayout(embedded_group)

        self._custom_server_checkbox = QCheckBox('Use custom Mumble server')
        self._custom_server_checkbox.setToolTip('Connect to an existing Mumble server instead of the local one.')
        self._custom_server_checkbox.setStatusTip('When enabled, manually configure IP, port and channel mappings.')
        self._install_btn = QPushButton()
        self._install_btn.setToolTip('Download and install the Mumble server locally.')
        self._install_btn.setStatusTip('Downloads the Mumble server from GitHub Releases.')

        self._firewall_btn = QPushButton()
        self._firewall_btn.setToolTip('Add Windows Firewall rules so other machines can reach the server.')
        self._firewall_btn.setStatusTip(
            'Opens a Windows administrator prompt (UAC) to add inbound firewall rules for the Mumble port.'
        )
        self._firewall_btn.setVisible(sys.platform == 'win32')

        checkbox_row = QHBoxLayout()
        checkbox_row.addWidget(self._custom_server_checkbox)
        checkbox_row.addWidget(self._install_btn)
        checkbox_row.addWidget(self._firewall_btn)
        checkbox_row.addStretch()
        embedded_layout.addLayout(checkbox_row)

        # Server control buttons (only shown when binary is installed)
        server_control_row = QHBoxLayout()
        self._start_server_btn = QPushButton('Start Server')
        self._start_server_btn.setToolTip('Manually start the local Mumble server.')
        self._start_server_btn.setStatusTip('Start the local Mumble Server process.')
        self._stop_server_btn = QPushButton('Stop Server')
        self._stop_server_btn.setToolTip('Manually stop the local Mumble server.')
        self._stop_server_btn.setStatusTip('Stop the local Mumble Server process.')
        self._server_status_label = QLabel()
        self._server_status_label.setObjectName('serverStatusLabel')
        self._server_status_label.setTextFormat(Qt.TextFormat.RichText)
        self._server_status_label.setStyleSheet('font-size: 13px; padding: 0 8px;')
        self._set_status_label('Stopped', '#e74c3c')
        server_control_row.addWidget(self._start_server_btn)
        server_control_row.addWidget(self._stop_server_btn)
        server_control_row.addWidget(self._server_status_label)
        server_control_row.addStretch()
        embedded_layout.addLayout(server_control_row)

        embedded_layout.addStretch()

        self._update_install_button()
        self._update_firewall_button()

        main_layout.addWidget(embedded_group)

        # --- Custom / manual server section (hidden by default) ---
        self._manual_server_group = QGroupBox('Custom Mumble Server Settings')
        mumble_layout = QFormLayout(
            self._manual_server_group,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        self.mumble_ip = QLineEdit('localhost')
        self.mumble_ip.setText(self._mumble_settings.ip_address)
        self.mumble_ip.setStatusTip('Enter the IP address or hostname of the Mumble server.')
        self.mumble_ip.setToolTip('e.g. localhost or 192.168.178.100')
        mumble_layout.addRow('Mumble Server IP:', self.mumble_ip)

        self.mumble_port = QLineEdit('64738')
        self.mumble_port.setText(str(self._mumble_settings.port))
        self.mumble_port.setStatusTip('Enter the port of the Mumble server.')
        self.mumble_port.setToolTip('Default: 64738')
        mumble_layout.addRow('Mumble Server Port:', self.mumble_port)

        main_layout.addWidget(self._manual_server_group)

        # --- Channel mapping section (hidden by default) ---
        self._channel_map_group = QGroupBox('Language to Mumble Channel Mapping')
        self._channel_map_layout = QVBoxLayout(self._channel_map_group)

        add_mapping_layout = QHBoxLayout()
        add_mapping_layout.setSpacing(5)

        self.lang_select_combo = QComboBox()
        all_target_langs = sorted_by_display_name(self._get_language_keys())
        for lang in all_target_langs:
            self.lang_select_combo.addItem(display_name(lang), lang)
        self.lang_select_combo.setToolTip('Select the target language for the mapping.')
        self.lang_select_combo.setStatusTip('Select the language for which you want to add a channel mapping.')
        add_mapping_layout.addWidget(self.lang_select_combo)

        self.channel_path_input = QLineEdit()
        self.channel_path_input.setPlaceholderText('Arabic/Translator')
        self.channel_path_input.setToolTip('Enter the path to the Mumble channel (e.g."Channel/Subchannel").')
        self.channel_path_input.setStatusTip(
            'Enter the path to channel to which the AI Translator should join. Separate subchannels with a slash "/".'
        )
        add_mapping_layout.addWidget(self.channel_path_input, 1)

        add_button = QPushButton('Add Mapping')
        add_button.setMaximumWidth(120)
        add_button.setToolTip('Adds the selected language-channel mapping.')
        add_button.setStatusTip('Add the selected language-channel mapping to the list.')
        add_button.clicked.connect(self._add_mapping)
        add_mapping_layout.addWidget(add_button)

        self._channel_map_layout.addLayout(add_mapping_layout)

        self.current_mappings_list = QListWidget()
        self.current_mappings_list.setToolTip('Current Language-Channel Mappings.')
        self.current_mappings_list.setStatusTip('Select an item and press Delete or Backspace to remove it.')
        self.current_mappings_list.installEventFilter(self)
        self._channel_map_layout.addWidget(self.current_mappings_list)
        self._update_mapping_list_widget()

        main_layout.addWidget(self._channel_map_group)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Connect signals — after all widgets are built
        self._custom_server_checkbox.toggled.connect(self._on_custom_server_toggled)
        self._install_btn.clicked.connect(self._on_install_clicked)
        self._firewall_btn.clicked.connect(self._on_firewall_clicked)
        self._start_server_btn.clicked.connect(self.start_server_requested.emit)
        self._stop_server_btn.clicked.connect(self.stop_server_requested.emit)

        # Apply initial visibility explicitly (setChecked(False) on unchecked box won't fire toggled)
        self._custom_server_checkbox.setChecked(self._mumble_settings.use_custom_server)
        self._on_custom_server_toggled(self._mumble_settings.use_custom_server)

    def _on_custom_server_toggled(self, checked: bool):
        self._manual_server_group.setVisible(checked)
        self._channel_map_group.setVisible(checked)
        # Install/firewall buttons only relevant in embedded mode
        self._install_btn.setVisible(not checked)
        self._firewall_btn.setVisible(not checked and sys.platform == 'win32')
        self._update_server_control_buttons()

    def _update_install_button(self):
        if self._is_murmur_installed():
            self._install_btn.setText('Mumble Server installed ✓')
            self._install_btn.setEnabled(False)
        else:
            self._install_btn.setText('Install Mumble Server')
            self._install_btn.setEnabled(True)
        self._update_server_control_buttons()

    def _update_firewall_button(self):
        """Refresh the firewall button's text/enabled state (Windows only)."""
        if sys.platform != 'win32':
            return
        if firewall_rules_exist(MUMBLE_DEFAULT_PORT):
            self._firewall_btn.setText('Firewall rule added ✓')
            self._firewall_btn.setEnabled(False)
        else:
            self._firewall_btn.setText('Add Firewall Rule')
            self._firewall_btn.setEnabled(True)

    def _update_server_control_buttons(self):
        """Show server control buttons only when embedded mode is active and binary is installed."""
        show = not self._custom_server_checkbox.isChecked() and self._is_murmur_installed()
        self._start_server_btn.setVisible(show)
        self._stop_server_btn.setVisible(show)
        self._server_status_label.setVisible(show)

    def _embedded_server_address(self) -> str:
        """Returns the host:port at which the local embedded Mumble server is reachable from other machines."""
        return f'{self._get_local_ip()}:{MUMBLE_DEFAULT_PORT}'

    def _set_status_label(self, status: str, color: str, address: str | None = None):
        """Render status label: 'Server Status:' in normal color, status value in given color."""
        suffix = f' ({address})' if address else ''
        self._server_status_label.setText(
            f'Server Status: <span style="font-weight: bold; color: {color};">{status}</span>{suffix}'
        )

    def _on_install_clicked(self):
        self._install_btn.setEnabled(False)
        self._install_btn.setText('Downloading… 0%')

        self._installer = MumbleInstaller(self._murmur_dir)
        self._installer.progress.connect(self._on_install_progress)
        self._install_thread = run_in_thread(
            self, self._installer, self._installer.run, self._installer.finished, self._on_install_finished
        )

    def _on_install_progress(self, pct: int):
        self._install_btn.setText(f'Downloading… {pct}%')

    def _on_firewall_clicked(self):
        self._firewall_btn.setEnabled(False)
        self._firewall_btn.setText('Adding…')

        self._firewall_worker = FirewallRuleWorker(MUMBLE_DEFAULT_PORT)
        self._firewall_thread = run_in_thread(
            self,
            self._firewall_worker,
            self._firewall_worker.run,
            self._firewall_worker.finished,
            self._on_firewall_finished,
        )

    def _on_firewall_finished(self, success: bool, error_msg: str):
        self._update_firewall_button()
        if not success:
            QMessageBox.critical(
                self,
                'Firewall Rule Failed',
                f'Could not add the Windows Firewall rules:\n\n{error_msg}',
            )

    def _on_install_finished(self, success: bool, error_msg: str):
        if success:
            self._update_install_button()
        else:
            self._install_btn.setText('Install Mumble Server')
            self._install_btn.setEnabled(True)
            QMessageBox.critical(
                self,
                'Install Failed',
                f'Could not install Mumble Server:\n\n{error_msg}',
            )

    def _add_mapping(self):
        lang = self.lang_select_combo.currentData()
        channel_path = self.channel_path_input.text().strip()

        if not lang or not channel_path:
            LOGGER.warning('Language or channel path cannot be empty.')
            return

        if lang in self.channel_mapping:
            LOGGER.info(f'Mapping for "{lang}" already exists. Updating.')

        self.channel_mapping[lang] = channel_path
        self._update_mapping_list_widget()
        self.channel_path_input.clear()

    def _perform_removal(self, item_to_remove: QListWidgetItem):
        if item_to_remove:
            text = item_to_remove.text()
            try:
                lang = text.split(':', 1)[0].strip()
                if lang in self.channel_mapping:
                    del self.channel_mapping[lang]
                    self._update_mapping_list_widget()
                else:
                    LOGGER.warning(f'Language "{lang}" not found in mapping.')
            except Exception as e:
                LOGGER.error(f'Error removing mapping "{text}": {e}')
        else:
            LOGGER.debug('No item selected for removal.')

    def _update_mapping_list_widget(self):
        self.current_mappings_list.clear()
        self.current_mappings_list.clearSelection()
        for lang in sorted(self.channel_mapping.keys()):
            channel_path = self.channel_mapping[lang]
            self.current_mappings_list.addItem(f'{lang}: {channel_path}')

    @staticmethod
    def _get_local_ip() -> str:
        """Best-effort determination of the machine's LAN IP address (not 127.0.0.1)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't actually send any traffic, just used to let the OS pick the outbound interface.
            sock.connect(('8.8.8.8', 80))
            return sock.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())
        finally:
            sock.close()

    @staticmethod
    def _get_language_keys() -> set:
        """
        Get a set of all unique language keys from the TRANSLATOR dictionary.
        """
        lang_keys = set()
        for engine in TRANSLATOR.values():
            for lang_dict in engine.values():
                for lang in lang_dict:
                    lang_keys.add(lang)
        return lang_keys
