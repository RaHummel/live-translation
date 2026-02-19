import logging

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import MumbleSettings
from constants import TRANSLATOR

LOGGER = logging.getLogger(__name__)


class MumbleWidget(QWidget):
    def __init__(self, mumble_settings: MumbleSettings, parent=None):
        super().__init__(parent)
        self._mumble_settings = mumble_settings
        self.channel_mapping = self._mumble_settings.language_channel_mapping
        self._setup_ui()

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

        self._mumble_settings = mumble_settings

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        mumble_group_box = QGroupBox('Mumble Server Settings')
        mumble_layout = QFormLayout(
            mumble_group_box,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        self.mumble_ip = QLineEdit('localhost')
        self.mumble_ip.setText(self._mumble_settings.ip_address)
        self.mumble_ip.setStatusTip('Enter the IP address or hostname of the Mumble server.')
        self.mumble_ip.setToolTip('e.g. localhost or 192.168.178.100')

        mumble_layout.addRow('Mumble Server IP:', self.mumble_ip)
        main_layout.addWidget(mumble_group_box)

        self.mumble_port = QLineEdit('64738')
        self.mumble_port.setText(str(self._mumble_settings.port))
        self.mumble_port.setStatusTip('Enter the port of the Mumble server.')
        self.mumble_port.setToolTip('Default: 64738')
        mumble_layout.addRow('Mumble Server Port:', self.mumble_port)

        channel_map_group_box = QGroupBox('Language to Mumble Channel Mapping')
        self._channel_map_layout = QVBoxLayout(channel_map_group_box)

        add_mapping_layout = QHBoxLayout()
        add_mapping_layout.setSpacing(5)

        self.lang_select_combo = QComboBox()
        all_target_langs = sorted(list(TRANSLATOR['aws'].keys()))
        self.lang_select_combo.addItems(all_target_langs)
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

        main_layout.addWidget(channel_map_group_box, 1)

        self.setLayout(main_layout)

    def _add_mapping(self):
        lang = self.lang_select_combo.currentText()
        channel_path = self.channel_path_input.text().strip()

        if not lang or not channel_path:
            print('Language or channel path cannot be empty.')
            return

        if lang in self.channel_mapping:
            print(f'Mapping for "{lang}" already exists. Updating.')

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
                    print(f'Error: Language "{lang}" not found in mapping.')
            except Exception as e:
                print(f'Error removing mapping "{text}": {e}')
        else:
            print('No item selected for removal.')

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

    def _update_mapping_list_widget(self):
        self.current_mappings_list.clear()
        self.current_mappings_list.clearSelection()
        for lang in sorted(self.channel_mapping.keys()):
            channel_path = self.channel_mapping[lang]
            self.current_mappings_list.addItem(f'{lang}: {channel_path}')

    def get_current_mappings(self):
        return self.channel_mapping
