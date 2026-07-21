import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QSpinBox, QStackedWidget, QVBoxLayout, QWidget

from config.model.config_models import OutputSettings
from constants import OUTPUT
from gui_elements.mumble_widget import MumbleWidget
from gui_elements.speaker_widget import SpeakerWidget

LOGGER = logging.getLogger(__name__)


class AudioOutputWidget(QWidget):
    def __init__(self, output_settings: OutputSettings, parent=None):
        super().__init__(parent)
        self._output_settings = output_settings
        self._setup_ui()

    def update_settings(self, output_settings: OutputSettings):
        """
        Updates the output settings in the widget.
        """
        if output_settings.output_method:
            self.output_method.setCurrentText(output_settings.output_method)

        self.output_sample_rate.setValue(output_settings.output_sample_rate)
        self.chunk_len.setValue(output_settings.chunk_len)

        self.mumble_widget.update_settings(output_settings.mumble_settings)
        self.speaker_widget.update_settings(output_settings.speaker_settings)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        general_settings_group = QGroupBox('General Output Settings')
        general_settings_layout = QFormLayout(
            general_settings_group,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        self.output_method = QComboBox()
        self.output_method.addItems(OUTPUT)
        self.output_method.setToolTip('Choose how the translated audio will be output.')
        self.output_method.setStatusTip('Select the output method for translated audio.')
        self.output_method.currentTextChanged.connect(self._update_output_fields)
        general_settings_layout.addRow('Output Method:', self.output_method)

        self.output_sample_rate = QSpinBox(
            minimum=8000,
            maximum=16000,
            singleStep=8000,
            value=self._output_settings.output_sample_rate,
        )
        self.output_sample_rate.setToolTip('Sample rate for audio output in Hz.')
        self.output_sample_rate.setStatusTip(
            'Sample rate for audio output. AWS only supports 8000 or 16000. Change at your own risk!'
        )
        general_settings_layout.addRow('Output Sample Rate (Hz):', self.output_sample_rate)

        self.chunk_len = QSpinBox(minimum=256, maximum=4096, singleStep=16, value=self._output_settings.chunk_len)
        self.chunk_len.setToolTip(
            'Audio buffer size (chunk length) in samples. Smaller values reduce latency but increase Network usage.'
        )
        self.chunk_len.setStatusTip('Audio buffer length in samples. Adjust for latency and performance.')
        general_settings_layout.addRow('Audio Buffer Length (samples):', self.chunk_len)

        main_layout.addWidget(general_settings_group)

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

        main_layout.addWidget(self.output_stacked, 0)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def _update_output_fields(self, text: str):
        widget = self._output_widget_map.get(text)
        if widget:
            self.output_stacked.setCurrentWidget(widget)
        else:
            LOGGER.error(f'Unknown output method selected: {text}. Defaulting to speaker widget.')
            self.output_stacked.setCurrentWidget(self.speaker_widget)
