import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication

from config.model.config_models import AWSSettings, GoogleSettings, LanguageSettings, TranslatorSettings
from gui_elements.live_output_widget import LiveOutputWidget


class TestLiveOutputWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _translator_settings(self, translator: str) -> TranslatorSettings:
        return TranslatorSettings(
            translator=translator,
            aws_settings=AWSSettings(
                region='eu-central-1',
                source_language='de-DE',
                show_source_transcript=False,
                target_languages={},
            ),
            google_settings=GoogleSettings(
                credentials_path='',
                source_language='de-DE',
                show_source_transcript=True,
                target_languages={
                    'en-US': LanguageSettings(voice_id='en-US-Wavenet-A', show_transcript=True, engine='wavenet'),
                },
            ),
        )

    def test_initializes_from_google_settings_when_google_selected(self):
        widget = LiveOutputWidget(self._translator_settings('google'))
        self.addCleanup(widget.deleteLater)

        self.assertTrue(widget.show_source_transcript_checkbox.isChecked())
        self.assertIn('en-US', widget.target_transcript_widgets)

    def test_update_settings_applies_google_target_transcripts(self):
        widget = LiveOutputWidget(self._translator_settings('aws'))
        self.addCleanup(widget.deleteLater)

        widget.update_settings(self._translator_settings('google'))

        self.assertTrue(widget.show_source_transcript_checkbox.isChecked())
        self.assertIn('en-US', widget.target_transcript_widgets)

    def test_update_settings_removes_targets_not_in_selected_provider(self):
        widget = LiveOutputWidget(self._translator_settings('google'))
        self.addCleanup(widget.deleteLater)

        widget.update_settings(self._translator_settings('aws'))

        self.assertFalse(widget.show_source_transcript_checkbox.isChecked())
        self.assertNotIn('en-US', widget.target_transcript_widgets)
