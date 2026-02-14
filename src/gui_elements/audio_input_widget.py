from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QSpinBox, QVBoxLayout, QWidget

from config.model.config_models import InputSettings
from sound_inputs.microphone import Microphone


class AudioInputWidget(QWidget):
    def __init__(self, input_settings: InputSettings, parent=None):
        super().__init__(parent)
        self._input_settings = input_settings
        self._setup_ui()

    def update_settings(self, input_settings: InputSettings):
        """
        Updates the audio input settings in the widget.
        Args:
            input_settings (InputSettings): User specific input settings.
        """

        self.input_channels.setValue(input_settings.input_channels)
        self.input_sample_rate.setValue(input_settings.input_sample_rate)

        if input_settings.input_device_index is not None:
            index = self.input_device.findData(input_settings.input_device_index)
            if index >= 0:
                self.input_device.setCurrentIndex(index)
            elif input_settings.input_device:
                self.input_device.setCurrentText(input_settings.input_device)
        elif input_settings.input_device:
            self.input_device.setCurrentText(input_settings.input_device)

        self._input_settings = input_settings

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        input_group_box = QGroupBox('Audio Input Settings')
        input_layout = QFormLayout(
            input_group_box,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        devices = Microphone.list_input_devices()
        self.input_device = QComboBox()
        for device in devices:
            device_name = device['name']
            if device.get('host_api_name') is not None:
                device_name += f':({device["host_api_name"]})'
            self.input_device.addItem(device_name, device['index'])

        if self._input_settings.input_device_index is not None:
            index = self.input_device.findData(self._input_settings.input_device_index)
            if index >= 0:
                self.input_device.setCurrentIndex(index)
            elif self._input_settings.input_device:
                self.input_device.setCurrentText(self._input_settings.input_device)
        elif self._input_settings.input_device:
            self.input_device.setCurrentText(self._input_settings.input_device)

        tip_text = 'Select the input device for audio capture.'

        self.input_device.setStatusTip(tip_text)
        self.input_device.setToolTip(tip_text)

        self.input_channels = QSpinBox(minimum=1, maximum=2, value=self._input_settings.input_channels)
        self.input_channels.setStatusTip(
            'Number of audio input channels. One seems to work best. Change at your own risk!'
        )
        self.input_channels.setToolTip('Number of audio input channels. Usually 1 (mono) or 2 (stereo).')

        self.input_sample_rate = QSpinBox(
            minimum=8000, maximum=192000, singleStep=1000, value=self._input_settings.input_sample_rate
        )
        self.input_sample_rate.setStatusTip(
            'Sample rate of the audio input in Hz. Common values are 16000, 44100, 48000. Change at your own risk!'
        )
        self.input_sample_rate.setToolTip('Sample rate of the audio input in Hz.')

        input_layout.addRow('Input Device:', self.input_device)
        input_layout.addRow('Input Channels:', self.input_channels)
        input_layout.addRow('Input Sample Rate (Hz):', self.input_sample_rate)

        main_layout.addWidget(input_group_box, 1)
        self.setLayout(main_layout)
