from typing import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import SpeakerSettings
from gui_elements.audio_input_widget import select_device_in_combo
from sound_outputs.speaker import Speaker
from utils.language_names import display_name, sorted_by_display_name


class SpeakerWidget(QWidget):
    def __init__(self, speaker_settings: SpeakerSettings, parent=None):
        super().__init__(parent)
        self._speaker_settings = speaker_settings
        self._channel_mapping = dict(speaker_settings.language_channel_mapping)
        self._target_languages = set(self._channel_mapping)
        self._devices_by_index: dict[int, Mapping] = {}
        self._setup_ui()

    def update_settings(self, speaker_settings: SpeakerSettings):
        """
        Updates the speaker settings in the widget.
        Args:
            speaker_settings (SpeakerSettings): User specific speaker settings.
        """
        self._store_visible_mappings()
        self._channel_mapping = dict(speaker_settings.language_channel_mapping)
        self._target_languages = set(self._channel_mapping)
        select_device_in_combo(self.output_device, speaker_settings.output_device_index, speaker_settings.output_device)
        self._rebuild_mapping_table()
        self._speaker_settings = speaker_settings

    def set_target_languages(self, languages: set[str]) -> None:
        """Show channel assignments for the active translator's target languages."""
        self._store_visible_mappings()
        self._target_languages = set(languages)
        self._rebuild_mapping_table()

    def get_channel_mapping(self) -> dict[str, int]:
        self._store_visible_mappings()
        return {language: self._channel_mapping[language] for language in self._target_languages}

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        speaker_group_box = QGroupBox('Speaker Output Settings')
        speaker_layout = QFormLayout(
            speaker_group_box,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        devices = Speaker.list_output_devices()
        self.output_device = QComboBox()
        for device in devices:
            self.output_device.addItem(device['name'], device['index'])
            self._devices_by_index[device['index']] = device

        select_device_in_combo(
            self.output_device, self._speaker_settings.output_device_index, self._speaker_settings.output_device
        )

        self.output_device.setToolTip('Select the speaker or output device for translated audio.')
        self.output_device.setStatusTip('Select the output device for audio playback.')
        self.output_device.currentIndexChanged.connect(self._rebuild_mapping_table)
        speaker_layout.addRow('Output Device:', self.output_device)

        self.channel_mapping_table = QTableWidget(0, 2)
        self.channel_mapping_table.setHorizontalHeaderLabels(['Target Language', 'Physical Output Channel'])
        self.channel_mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.channel_mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.channel_mapping_table.verticalHeader().setVisible(False)
        self.channel_mapping_table.setToolTip(
            'Assign every translated language to a distinct physical channel of the selected audio device.'
        )
        speaker_layout.addRow('Language Routing:', self.channel_mapping_table)
        self._rebuild_mapping_table()

        main_layout.addWidget(speaker_group_box, 1)
        self.setLayout(main_layout)

    def _selected_device_channel_count(self) -> int:
        device = self._devices_by_index.get(self.output_device.currentData(), {})
        return max(1, int(device.get('max_output_channels', 1)))

    def _store_visible_mappings(self) -> None:
        if not hasattr(self, 'channel_mapping_table'):
            return
        for row in range(self.channel_mapping_table.rowCount()):
            language_item = self.channel_mapping_table.item(row, 0)
            channel_combo = self.channel_mapping_table.cellWidget(row, 1)
            if language_item is not None and isinstance(channel_combo, QComboBox):
                self._channel_mapping[language_item.data(Qt.ItemDataRole.UserRole)] = int(channel_combo.currentData())

    def _rebuild_mapping_table(self, _index: int | None = None) -> None:
        if not hasattr(self, 'channel_mapping_table'):
            return
        self._store_visible_mappings()
        channel_count = self._selected_device_channel_count()
        self.channel_mapping_table.setRowCount(0)
        used_channels = {
            channel
            for language, channel in self._channel_mapping.items()
            if language in self._target_languages and 1 <= channel <= channel_count
        }

        for language in sorted_by_display_name(self._target_languages):
            row = self.channel_mapping_table.rowCount()
            self.channel_mapping_table.insertRow(row)
            language_item = QTableWidgetItem(display_name(language))
            language_item.setData(Qt.ItemDataRole.UserRole, language)
            language_item.setFlags(language_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.channel_mapping_table.setItem(row, 0, language_item)

            channel_combo = QComboBox()
            for channel in range(1, channel_count + 1):
                channel_combo.addItem(f'Channel {channel}', channel)
            configured_channel = self._channel_mapping.get(language)
            if configured_channel is None or configured_channel > channel_count:
                configured_channel = next(
                    (channel for channel in range(1, channel_count + 1) if channel not in used_channels), 1
                )
                self._channel_mapping[language] = configured_channel
            used_channels.add(configured_channel)
            channel_combo.setCurrentIndex(max(0, channel_combo.findData(configured_channel)))
            self.channel_mapping_table.setCellWidget(row, 1, channel_combo)
