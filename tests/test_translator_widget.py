import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication

from config.model.config_models import AWSSettings, GoogleSettings, TranslatorSettings
from gui_elements.translator_widget import TranslatorWidget


class TestTranslatorWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _create_translator_settings(self, translator: str) -> TranslatorSettings:
        return TranslatorSettings(
            translator=translator,
            aws_settings=AWSSettings(
                region='eu-central-1',
                source_language='de-DE',
                show_source_transcript=True,
                target_languages={},
            ),
            google_settings=GoogleSettings(
                credentials_path='',
                source_language='de-DE',
                show_source_transcript=True,
                target_languages={},
                endpointing_sensitivity='short',
            ),
        )

    @patch('gui_elements.aws_widget.AWSWidget._check_aws_credentials', return_value=None)
    def test_initializes_google_widget_for_google_provider(self, _mock_check_credentials):
        widget = TranslatorWidget(self._create_translator_settings('google'))
        self.addCleanup(widget.deleteLater)

        self.assertIs(widget.translator_stacked.currentWidget(), widget.google_tab_widget)

    @patch('gui_elements.aws_widget.AWSWidget._check_aws_credentials', return_value=None)
    def test_update_settings_switches_to_google_widget(self, _mock_check_credentials):
        widget = TranslatorWidget(self._create_translator_settings('aws'))
        self.addCleanup(widget.deleteLater)

        widget.update_settings(self._create_translator_settings('google'))

        self.assertEqual(widget.translator_select.currentText(), 'google')
        self.assertIs(widget.translator_stacked.currentWidget(), widget.google_tab_widget)

    @patch('gui_elements.aws_widget.AWSWidget._check_aws_credentials', return_value=None)
    def test_google_widget_endpointing_dropdown_is_configurable(self, _mock_check_credentials):
        settings = self._create_translator_settings('google')
        settings.google_settings.endpointing_sensitivity = 'supershort'

        widget = TranslatorWidget(settings)
        self.addCleanup(widget.deleteLater)

        self.assertEqual(widget.google_tab_widget.get_endpointing_sensitivity(), 'supershort')

    @patch('gui_elements.aws_widget.AWSWidget._check_aws_credentials', return_value=None)
    def test_emits_provider_changed_signal_on_switch(self, _mock_check_credentials):
        widget = TranslatorWidget(self._create_translator_settings('aws'))
        self.addCleanup(widget.deleteLater)

        seen = []
        widget.add_provider_changed_signal(seen.append)

        widget.translator_select.setCurrentText('google')

        self.assertIn('google', seen)
