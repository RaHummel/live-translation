import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QStackedWidget, QVBoxLayout, QWidget

from config.model.config_models import InputSettings, OutputSettings
from constants import OUTPUT
from gui_elements.device_combo import select_device_in_combo
from gui_elements.mumble_widget import MumbleWidget
from gui_elements.speaker_widget import SpeakerWidget
from sound_inputs.microphone import Microphone

LOGGER = logging.getLogger(__name__)


class AudioWidget(QWidget):
    """Audio tab: input device on top, output method with settings below."""

    def __init__(self, input_settings: InputSettings, output_settings: OutputSettings, parent=None):
        super().__init__(parent)
        self._input_settings = input_settings
        self._output_settings = output_settings
        self._setup_ui()

    def update_settings(self, input_settings: InputSettings, output_settings: OutputSettings) -> None:
        select_device_in_combo(self.input_device, input_settings.input_device_index, input_settings.input_device)
        self._input_settings = input_settings

        if output_settings.output_method:
            self.output_method.setCurrentText(output_settings.output_method)
        self.mumble_widget.update_settings(output_settings.mumble_settings)
        self.speaker_widget.update_settings(output_settings.speaker_settings)
        self._output_settings = output_settings

    @staticmethod
    def _form_layout(group: QGroupBox) -> QFormLayout:
        return QFormLayout(
            group,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._build_input_group())
        main_layout.addWidget(self._build_output_group())

        self.output_stacked = QStackedWidget()
        self.speaker_widget = SpeakerWidget(self._output_settings.speaker_settings)
        self.mumble_widget = MumbleWidget(self._output_settings.mumble_settings)
        self._output_widget_map = {
            'speaker': self.speaker_widget,
            'mumble': self.mumble_widget,
        }
        self.output_stacked.addWidget(self.speaker_widget)
        self.output_stacked.addWidget(self.mumble_widget)

        if self._output_settings.output_method:
            self.output_method.setCurrentText(self._output_settings.output_method)
        self._update_output_fields(self.output_method.currentText())

        main_layout.addWidget(self.output_stacked, 0)
        main_layout.addStretch()

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox('Input')
        layout = self._form_layout(group)

        self.input_device = QComboBox()
        for device in Microphone.list_input_devices():
            device_name = device['name']
            if device.get('host_api_name') is not None:
                device_name += f' ({device["host_api_name"]})'
            self.input_device.addItem(device_name, device['index'])
        select_device_in_combo(
            self.input_device, self._input_settings.input_device_index, self._input_settings.input_device
        )
        tip_text = 'Select the input device for audio capture.'
        self.input_device.setStatusTip(tip_text)
        self.input_device.setToolTip(tip_text)
        layout.addRow('Input Device:', self.input_device)
        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox('Output')
        layout = self._form_layout(group)

        self.output_method = QComboBox()
        self.output_method.addItems(OUTPUT)
        self.output_method.setToolTip('Choose how the translated audio will be output.')
        self.output_method.setStatusTip('Select the output method for translated audio.')
        self.output_method.currentTextChanged.connect(self._update_output_fields)
        layout.addRow('Output Method:', self.output_method)
        return group

    def _update_output_fields(self, text: str) -> None:
        if not hasattr(self, 'output_stacked'):
            return
        widget = self._output_widget_map.get(text)
        if widget:
            self.output_stacked.setCurrentWidget(widget)
        else:
            LOGGER.error(f'Unknown output method selected: {text}. Defaulting to speaker widget.')
            self.output_stacked.setCurrentWidget(self.speaker_widget)
