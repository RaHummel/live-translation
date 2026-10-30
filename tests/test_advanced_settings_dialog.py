import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QDialogButtonBox

from config.model.config_models import SegmentationSettings
from constants import CHUNK_LEN, INPUT_CHANNELS, INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE
from gui_elements.advanced_settings_dialog import AdvancedSettings, AdvancedSettingsDialog


class TestAdvancedSettingsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _dialog(self, settings: AdvancedSettings) -> AdvancedSettingsDialog:
        dialog = AdvancedSettingsDialog(settings)
        self.addCleanup(dialog.deleteLater)
        return dialog

    @staticmethod
    def _custom_settings() -> AdvancedSettings:
        return AdvancedSettings(
            input_sample_rate=48000,
            input_channels=2,
            output_sample_rate=8000,
            chunk_len=512,
            segmentation=SegmentationSettings(
                use_interim_segmentation=True,
                min_segment_words=5,
                max_segment_words=20,
                max_speaking_rate=1.25,
                max_backlog_s=8.0,
            ),
        )

    def test_round_trips_settings(self):
        settings = self._custom_settings()

        self.assertEqual(self._dialog(settings).get_settings(), settings)

    def test_restore_defaults(self):
        dialog = self._dialog(self._custom_settings())

        dialog.restore_defaults()

        self.assertEqual(dialog.get_settings(), AdvancedSettings())
        self.assertEqual(
            (INPUT_SAMPLE_RATE, INPUT_CHANNELS, OUTPUT_SAMPLE_RATE, CHUNK_LEN),
            (
                dialog.input_sample_rate.value(),
                dialog.input_channels.value(),
                dialog.output_sample_rate.currentData(),
                dialog.chunk_len.value(),
            ),
        )

    def test_values_are_clamped_to_allowed_ranges(self):
        dialog = self._dialog(AdvancedSettings())

        dialog.chunk_len.setValue(10)
        dialog.max_speaking_rate.setValue(5.0)
        dialog.max_backlog_s.setValue(0.1)

        settings = dialog.get_settings()
        self.assertEqual(settings.chunk_len, 256)
        self.assertEqual(settings.segmentation.max_speaking_rate, 2.0)
        self.assertEqual(settings.segmentation.max_backlog_s, 1.5)

    def test_max_words_never_below_min_words_plus_gap(self):
        dialog = self._dialog(AdvancedSettings())
        dialog.max_segment_words.setValue(5)

        dialog.min_segment_words.setValue(10)

        self.assertEqual(dialog.max_segment_words.value(), 12)
        self.assertEqual(dialog.max_segment_words.minimum(), 12)

    def test_output_sample_rate_offers_only_supported_rates(self):
        dialog = self._dialog(AdvancedSettings())

        rates = [dialog.output_sample_rate.itemData(i) for i in range(dialog.output_sample_rate.count())]

        self.assertEqual(rates, [8000, 16000])

    def test_keeps_unsupported_configured_output_rate_selectable(self):
        settings = AdvancedSettings(output_sample_rate=24000)

        self.assertEqual(self._dialog(settings).get_settings().output_sample_rate, 24000)

    def test_word_limits_disabled_without_interim_segmentation(self):
        dialog = self._dialog(AdvancedSettings())

        dialog.use_interim_segmentation.setChecked(False)

        self.assertFalse(dialog.min_segment_words.isEnabled())
        self.assertFalse(dialog.max_segment_words.isEnabled())
        self.assertTrue(dialog.max_speaking_rate.isEnabled())
        self.assertTrue(dialog.max_backlog_s.isEnabled())

    def test_restore_defaults_button_is_wired(self):
        dialog = self._dialog(self._custom_settings())

        dialog.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).click()

        self.assertEqual(dialog.get_settings(), AdvancedSettings())

    def test_from_config_copies_segmentation(self):
        from config.config_manager import ConfigManager

        config = ConfigManager.create_user_config(
            {
                'input_settings': {'input_sample_rate': 44100, 'input_channels': 2},
                'output_settings': {'output_sample_rate': 8000, 'chunk_len': 2048},
                'translator_settings': {'segmentation': {'min_segment_words': 4}},
            }
        )

        settings = AdvancedSettings.from_config(config)

        self.assertEqual(
            (settings.input_sample_rate, settings.input_channels, settings.output_sample_rate, settings.chunk_len),
            (44100, 2, 8000, 2048),
        )
        self.assertEqual(settings.segmentation.min_segment_words, 4)
        self.assertIsNot(settings.segmentation, config.translator_settings.segmentation)
