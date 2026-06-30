import json
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from config.config_manager import ConfigManager
from config.model.config_models import (
    AWSSettings,
    InputSettings,
    OutputSettings,
    TranslatorSettings,
    UserConfig,
)


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.mock_config_path = Path('/tmp/fake_config.json')
        self.patcher = patch('config.config_manager.ConfigManager._get_config_path', return_value=self.mock_config_path)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_load_config_file_not_found(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            cm = ConfigManager()

        self.assertIsInstance(cm.config, UserConfig)
        self.assertEqual(cm.config.input_settings.input_device, 'default')

    def test_load_config_success(self):
        fake_config = {
            'input_settings': {'input_device': 'mic1'},
            'output_settings': {'output_method': 'speaker', 'speaker_settings': {'output_device': 'speaker1'}},
            'translator_settings': {
                'translator': 'aws',
                'aws_settings': {'region': 'eu-central-1'},
                'google_settings': {'endpointing_sensitivity': 'supershort'},
            },
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(fake_config))):
            cm = ConfigManager()

        self.assertIsInstance(cm.config, UserConfig)
        self.assertEqual(cm.config.input_settings.input_device, 'mic1')
        self.assertEqual(cm.config.translator_settings.aws_settings.region, 'eu-central-1')
        self.assertEqual(cm.config.translator_settings.google_settings.endpointing_sensitivity, 'supershort')

    def test_store_config(self):
        cm = ConfigManager()
        new_config = cm.config
        new_config.input_settings.input_device = 'new_mic'

        with patch('builtins.open', mock_open()) as mocked_file:
            cm.store_config(new_config)
            mocked_file.assert_called_once_with(self.mock_config_path, 'w')

    def test_create_user_config_defaults(self):
        config = ConfigManager.create_user_config({})

        self.assertIsInstance(config, UserConfig)
        self.assertIsInstance(config.input_settings, InputSettings)
        self.assertIsInstance(config.output_settings, OutputSettings)
        self.assertIsInstance(config.translator_settings, TranslatorSettings)
        self.assertIsNotNone(config.translator_settings.aws_settings)
        self.assertIsNotNone(config.translator_settings.google_settings)

    def test_create_user_config_with_provider_settings(self):
        raw = {
            'translator_settings': {
                'translator': 'aws',
                'aws_settings': {
                    'region': 'eu-central-1',
                    'source_language': 'de-DE',
                    'show_source_transcript': False,
                },
                'google_settings': {
                    'credentials_path': '',
                    'source_language': 'de-DE',
                    'show_source_transcript': False,
                    'endpointing_sensitivity': 'short',
                },
            }
        }
        config = ConfigManager.create_user_config(raw)

        self.assertIsInstance(config.translator_settings.aws_settings, AWSSettings)
        self.assertEqual(config.translator_settings.google_settings.endpointing_sensitivity, 'short')
