from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QVBoxLayout, QWidget

from config.model.config_models import SpeakerSettings
from sound_outputs.speaker import Speaker


class SpeakerWidget(QWidget):
    def __init__(self, speaker_settings: SpeakerSettings, parent=None):
        super().__init__(parent)
        self._speaker_settings = speaker_settings
        self._setup_ui()

    def update_settings(self, speaker_settings: SpeakerSettings):
        """
        Updates the speaker settings in the widget.
        Args:
            speaker_settings (SpeakerSettings): User specific speaker settings.
        """
        if speaker_settings.output_device_index is not None:
            index = self.output_device.findData(speaker_settings.output_device_index)
            if index >= 0:
                self.output_device.setCurrentIndex(index)
            elif speaker_settings.output_device:
                self.output_device.setCurrentText(speaker_settings.output_device)
        elif speaker_settings.output_device:
            self.output_device.setCurrentText(speaker_settings.output_device)

        self._speaker_settings = speaker_settings

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

        if self._speaker_settings.output_device_index is not None:
            index = self.output_device.findData(self._speaker_settings.output_device_index)
            if index >= 0:
                self.output_device.setCurrentIndex(index)
            elif self._speaker_settings.output_device:
                self.output_device.setCurrentText(self._speaker_settings.output_device)
        elif self._speaker_settings.output_device:
            self.output_device.setCurrentText(self._speaker_settings.output_device)

        self.output_device.setToolTip('Select the speaker or output device for translated audio.')
        self.output_device.setStatusTip('Select the output device for audio playback.')
        speaker_layout.addRow('Output Device:', self.output_device)

        main_layout.addWidget(speaker_group_box, 1)
        self.setLayout(main_layout)
