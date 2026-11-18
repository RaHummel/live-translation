import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QDialog

from config.config_manager import ConfigManager
from config.model.config_models import SegmentationSettings
from gui_elements.advanced_settings_dialog import AdvancedSettings


class TestMainWindowAdvancedSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        config_dir_patch = patch.object(ConfigManager, 'get_app_config_dir', return_value=Path(tmp_dir.name))
        config_dir_patch.start()
        self.addCleanup(config_dir_patch.stop)
        for target in (
            'gui_elements.aws_widget.AWSWidget._check_aws_credentials',
            'main_window.MainWindow._apply_theme',
        ):
            patcher = patch(target, return_value=None)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _window(self, raw_config: dict):
        from main_window import MainWindow

        manager = ConfigManager()
        manager.config = ConfigManager.create_user_config(raw_config)
        window = MainWindow(manager)
        window._current_theme = 'light'
        self.addCleanup(window.deleteLater)
        return window

    def test_collect_keeps_config_only_endpointing_sensitivity(self):
        window = self._window({'translator_settings': {'google_settings': {'endpointing_sensitivity': 'supershort'}}})

        config = window._collect_config_data()

        self.assertEqual(config.translator_settings.google_settings.endpointing_sensitivity, 'supershort')

    def test_collect_uses_advanced_settings(self):
        window = self._window({})
        window._advanced_settings = AdvancedSettings(
            input_sample_rate=48000,
            input_channels=2,
            output_sample_rate=8000,
            chunk_len=512,
            segmentation=SegmentationSettings(min_segment_words=6, max_segment_words=18),
        )

        config = window._collect_config_data()

        self.assertEqual(config.input_settings.input_sample_rate, 48000)
        self.assertEqual(config.input_settings.input_channels, 2)
        self.assertEqual(config.output_settings.output_sample_rate, 8000)
        self.assertEqual(config.output_settings.chunk_len, 512)
        self.assertEqual(config.translator_settings.segmentation.min_segment_words, 6)
        self.assertEqual(config.translator_settings.segmentation.max_segment_words, 18)

    def test_accepted_dialog_replaces_advanced_settings(self):
        window = self._window({})
        new_settings = AdvancedSettings(chunk_len=2048)

        with patch('main_window.AdvancedSettingsDialog') as dialog_cls:
            dialog_cls.DialogCode = QDialog.DialogCode
            dialog_cls.return_value.exec.return_value = QDialog.DialogCode.Accepted
            dialog_cls.return_value.get_settings.return_value = new_settings
            window.translator_tab_widget.advanced_settings_button.click()

        self.assertEqual(window._advanced_settings, new_settings)

    def test_advanced_settings_locked_while_running(self):
        window = self._window({})

        window.start_button_signal.emit(False)

        self.assertFalse(window.advanced_settings_action.isEnabled())
        self.assertFalse(window.translator_tab_widget.advanced_settings_button.isEnabled())

        window.start_button_signal.emit(True)

        self.assertTrue(window.advanced_settings_action.isEnabled())
        self.assertTrue(window.translator_tab_widget.advanced_settings_button.isEnabled())

    def test_load_config_populates_gui_and_hidden_settings(self):
        window = self._window({})
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        file_path = Path(tmp_dir.name) / 'other.json'
        file_path.write_text(
            json.dumps(
                {
                    'output_settings': {'output_method': 'mumble', 'chunk_len': 2048},
                    'translator_settings': {
                        'translator': 'google',
                        'google_settings': {'endpointing_sensitivity': 'standard'},
                        'segmentation': {'min_segment_words': 7},
                    },
                }
            )
        )

        with patch('main_window.QFileDialog.getOpenFileName', return_value=(str(file_path), '')):
            window.load_action.trigger()

        self.assertEqual(window.status_label.text(), 'Status: Config Loaded')
        self.assertEqual(window.audio_tab_widget.output_method.currentText(), 'mumble')
        self.assertEqual(window.translator_tab_widget.translator_select.currentText(), 'google')
        config = window._collect_config_data()
        self.assertEqual(config.output_settings.chunk_len, 2048)
        self.assertEqual(config.translator_settings.google_settings.endpointing_sensitivity, 'standard')
        self.assertEqual(config.translator_settings.segmentation.min_segment_words, 7)

    def test_load_config_shows_error_for_broken_file(self):
        window = self._window({})
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        file_path = Path(tmp_dir.name) / 'broken.json'
        file_path.write_text('{broken')

        with (
            patch('main_window.QFileDialog.getOpenFileName', return_value=(str(file_path), '')),
            patch('main_window.QMessageBox.critical') as critical,
        ):
            window.load_action.trigger()

        critical.assert_called_once()
        self.assertEqual(window.status_label.text(), 'Status: Config Error')
