from dataclasses import dataclass, field, replace
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import SegmentationSettings, UserConfig
from constants import (
    CHUNK_LEN,
    CHUNK_LEN_RANGE,
    INPUT_CHANNELS,
    INPUT_CHANNELS_RANGE,
    INPUT_SAMPLE_RATE,
    INPUT_SAMPLE_RATE_RANGE,
    MAX_BACKLOG_S_RANGE,
    MAX_SEGMENT_WORDS_RANGE,
    MAX_SPEAKING_RATE_RANGE,
    MIN_SEGMENT_WORDS_RANGE,
    OUTPUT_SAMPLE_RATE,
    OUTPUT_SAMPLE_RATES,
    SEGMENT_WORDS_MIN_GAP,
)


@dataclass
class AdvancedSettings:
    """Expert settings that are hidden from the main window and edited in :class:`AdvancedSettingsDialog`."""

    input_sample_rate: int = INPUT_SAMPLE_RATE
    input_channels: int = INPUT_CHANNELS
    output_sample_rate: int = OUTPUT_SAMPLE_RATE
    chunk_len: int = CHUNK_LEN
    segmentation: SegmentationSettings = field(default_factory=SegmentationSettings)

    @classmethod
    def from_config(cls, config: UserConfig) -> 'AdvancedSettings':
        return cls(
            input_sample_rate=config.input_settings.input_sample_rate,
            input_channels=config.input_settings.input_channels,
            output_sample_rate=config.output_settings.output_sample_rate,
            chunk_len=config.output_settings.chunk_len,
            segmentation=replace(config.translator_settings.segmentation),
        )


class AdvancedSettingsDialog(QDialog):
    """Dialog for audio and segmentation settings most users never need to change."""

    def __init__(self, settings: AdvancedSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle('Advanced Settings')
        self.setMinimumWidth(460)
        self._setup_ui()
        self.set_settings(settings)

    def get_settings(self) -> AdvancedSettings:
        return AdvancedSettings(
            input_sample_rate=self.input_sample_rate.value(),
            input_channels=self.input_channels.value(),
            output_sample_rate=int(self.output_sample_rate.currentData()),
            chunk_len=self.chunk_len.value(),
            segmentation=SegmentationSettings(
                use_interim_segmentation=self.use_interim_segmentation.isChecked(),
                min_segment_words=self.min_segment_words.value(),
                max_segment_words=self.max_segment_words.value(),
                max_speaking_rate=self.max_speaking_rate.value(),
                max_backlog_s=self.max_backlog_s.value(),
            ),
        )

    def set_settings(self, settings: AdvancedSettings) -> None:
        self.input_sample_rate.setValue(settings.input_sample_rate)
        self.input_channels.setValue(settings.input_channels)
        index = self.output_sample_rate.findData(settings.output_sample_rate)
        if index < 0:
            self.output_sample_rate.addItem(str(settings.output_sample_rate), settings.output_sample_rate)
            index = self.output_sample_rate.count() - 1
        self.output_sample_rate.setCurrentIndex(index)
        self.chunk_len.setValue(settings.chunk_len)

        segmentation = settings.segmentation
        self.use_interim_segmentation.setChecked(segmentation.use_interim_segmentation)
        self.min_segment_words.setValue(segmentation.min_segment_words)
        self.max_segment_words.setValue(segmentation.max_segment_words)
        self.max_speaking_rate.setValue(segmentation.max_speaking_rate)
        self.max_backlog_s.setValue(segmentation.max_backlog_s)
        self._update_segment_fields_enabled()

    def restore_defaults(self) -> None:
        self.set_settings(AdvancedSettings())

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._build_audio_group())
        main_layout.addWidget(self._build_segmentation_group())

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        restore_button = self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        restore_button.clicked.connect(self.restore_defaults)
        main_layout.addWidget(self.button_box)

    @staticmethod
    def _form_layout(group: QGroupBox) -> QFormLayout:
        return QFormLayout(
            group,
            labelAlignment=Qt.AlignmentFlag.AlignLeft,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

    def _build_audio_group(self) -> QGroupBox:
        group = QGroupBox('Audio')
        layout = self._form_layout(group)

        self.input_sample_rate = QSpinBox(
            minimum=INPUT_SAMPLE_RATE_RANGE[0], maximum=INPUT_SAMPLE_RATE_RANGE[1], singleStep=1000
        )
        self.input_sample_rate.setToolTip(
            'Sample rate of the captured audio in Hz. 16000 is sufficient for speech recognition.'
        )
        layout.addRow('Input Sample Rate (Hz):', self.input_sample_rate)

        self.input_channels = QSpinBox(minimum=INPUT_CHANNELS_RANGE[0], maximum=INPUT_CHANNELS_RANGE[1])
        self.input_channels.setToolTip('Number of captured audio channels. 1 (mono) works best.')
        layout.addRow('Input Channels:', self.input_channels)

        self.output_sample_rate = QComboBox()
        for rate in OUTPUT_SAMPLE_RATES:
            self.output_sample_rate.addItem(str(rate), rate)
        self.output_sample_rate.setToolTip('Sample rate of the synthesized speech in Hz. AWS supports 8000 or 16000.')
        layout.addRow('Output Sample Rate (Hz):', self.output_sample_rate)

        self.chunk_len = QSpinBox(minimum=CHUNK_LEN_RANGE[0], maximum=CHUNK_LEN_RANGE[1], singleStep=16)
        self.chunk_len.setToolTip(
            'Audio output buffer size in frames. Smaller values reduce latency but increase processing overhead.'
        )
        layout.addRow('Audio Buffer Length (frames):', self.chunk_len)
        return group

    def _build_segmentation_group(self) -> QGroupBox:
        group = QGroupBox('Segmentation')
        layout = self._form_layout(group)

        self.use_interim_segmentation = QCheckBox('Translate before the speaker pauses')
        self.use_interim_segmentation.setToolTip(
            'Cuts interim transcripts into segments at punctuation or the word limit, so fast speakers are '
            'translated without waiting for the end of the utterance.'
        )
        self.use_interim_segmentation.toggled.connect(self._update_segment_fields_enabled)
        layout.addRow(self.use_interim_segmentation)

        self.min_segment_words = QSpinBox(minimum=MIN_SEGMENT_WORDS_RANGE[0], maximum=MIN_SEGMENT_WORDS_RANGE[1])
        self.min_segment_words.setToolTip('A segment is only sent at a punctuation mark once it has this many words.')
        self.min_segment_words.valueChanged.connect(self._sync_max_segment_minimum)
        layout.addRow('Min. Words per Segment:', self.min_segment_words)

        self.max_segment_words = QSpinBox(minimum=MAX_SEGMENT_WORDS_RANGE[0], maximum=MAX_SEGMENT_WORDS_RANGE[1])
        self.max_segment_words.setToolTip(
            'A segment is cut at the latest after this many words, even without a punctuation mark.'
        )
        layout.addRow('Max. Words per Segment:', self.max_segment_words)

        self.max_speaking_rate = QDoubleSpinBox(
            minimum=MAX_SPEAKING_RATE_RANGE[0], maximum=MAX_SPEAKING_RATE_RANGE[1], singleStep=0.05, decimals=2
        )
        self.max_speaking_rate.setToolTip(
            'Upper limit for the speech speed-up used to catch up with a growing backlog. 1.0 disables it.'
        )
        layout.addRow('Max. Speaking Rate:', self.max_speaking_rate)

        self.max_backlog_s = QDoubleSpinBox(
            minimum=MAX_BACKLOG_S_RANGE[0], maximum=MAX_BACKLOG_S_RANGE[1], singleStep=0.5, decimals=1, suffix=' s'
        )
        self.max_backlog_s.setToolTip('Backlog at which the maximum speaking rate is reached.')
        layout.addRow('Backlog for Max. Rate:', self.max_backlog_s)
        return group

    def _sync_max_segment_minimum(self, min_words: int) -> None:
        self.max_segment_words.setMinimum(max(MAX_SEGMENT_WORDS_RANGE[0], min_words + SEGMENT_WORDS_MIN_GAP))

    def _update_segment_fields_enabled(self) -> None:
        enabled = self.use_interim_segmentation.isChecked()
        self.min_segment_words.setEnabled(enabled)
        self.max_segment_words.setEnabled(enabled)
