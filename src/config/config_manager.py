import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from config.model.config_models import (
    AWSSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
    TranslatorSettings,
    UserConfig,
)
from constants import CHUNK_LEN, INPUT_CHANNELS, INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE

LOGGER = logging.getLogger(__name__)


class ConfigManager:
    """
    A class to manage configuration settings.
    """

    def __init__(self):
        self._config_path = self._get_config_path()
        self.config: UserConfig = self.load_config()

    def store_config(self, config_data: UserConfig):
        """
        Store the configuration data to a file.

        Args:
            config_data (UserConfig): The configuration data to store.
        """
        json_data = asdict(config_data)
        with open(self._config_path, 'w') as file:
            json.dump(json_data, file, indent=2)

    def load_config(self) -> UserConfig:
        """
        Load the configuration data from a file.

        Returns:
            UserConfig: The loaded configuration data.
        """
        raw_config = {}
        try:
            with open(self._config_path, 'r') as file:
                raw_config = json.load(file)
        except FileNotFoundError:
            LOGGER.debug('Using default settings')
        except json.JSONDecodeError as e:
            LOGGER.error(f'Error decoding configuration file: {e}. Using default settings.')

        return ConfigManager.create_user_config(raw_config)

    @staticmethod
    def _get_config_path() -> Path:
        """
        Get the configuration file path based on the operating system.
        Creates the directory if it doesn't exist.

        Returns:
            Path: The full path to the config.json file.
        """
        # Use platform-specific directories
        if os.name == 'nt':  # Windows
            config_dir = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / 'LiveTranslation'
        else:  # Linux, macOS, etc.
            config_dir = Path(os.path.expanduser('~')) / '.config' / 'live-translation'

        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir / 'config.json'

    @staticmethod
    def create_user_config(raw_config: dict) -> UserConfig:
        """
        Create a UserConfig instance from a raw configuration dictionary.

        Args:
            raw_config (dict): The raw configuration data.

        Returns:
            UserConfig: An instance of UserConfig populated with the raw data.
        """
        raw_input_settings = raw_config.get('input_settings', {})
        input_settings = InputSettings(
            input_device=raw_input_settings.get('input_device', 'default'),
            input_device_index=raw_input_settings.get('input_device_index', None),
            input_sample_rate=raw_input_settings.get('input_sample_rate', INPUT_SAMPLE_RATE),
            input_channels=raw_input_settings.get('input_channels', INPUT_CHANNELS),
        )

        raw_output_settings = raw_config.get('output_settings', {})
        output_settings = OutputSettings(
            output_method=raw_output_settings.get('output_method', None),
            output_sample_rate=raw_output_settings.get('output_sample_rate', OUTPUT_SAMPLE_RATE),
            chunk_len=raw_output_settings.get('chunk_len', CHUNK_LEN),
            speaker_settings=SpeakerSettings(
                output_device=raw_output_settings.get('speaker_settings', {}).get('output_device', 'default'),
                output_device_index=raw_output_settings.get('speaker_settings', {}).get('output_device_index', None),
            ),
            mumble_settings=MumbleSettings(
                ip_address=raw_output_settings.get('mumble_settings', {}).get('ip_address', 'localhost'),
                port=raw_output_settings.get('mumble_settings', {}).get('port', 64738),
                language_channel_mapping=raw_output_settings.get('mumble_settings', {}).get(
                    'language_channel_mapping', {}
                ),
            ),
        )

        raw_aws_settings = raw_config.get('translator_settings', {}).get('aws_settings', {})
        translator_settings = TranslatorSettings(
            translator=raw_config.get('translator_settings', {}).get('translator', 'aws'),
            aws_settings=AWSSettings(
                region=raw_aws_settings.get('region', 'eu-central-1'),
                source_language=raw_aws_settings.get('source_language', 'de-DE'),
                show_source_transcript=raw_aws_settings.get('show_source_transcript', False),
                target_languages={
                    lang: LanguageSettings(
                        voice_id=val['voice_id'],
                        show_transcript=val.get('show_transcript', False),
                    )
                    for lang, val in raw_aws_settings.get('target_languages', {}).items()
                },
            ),
        )

        return UserConfig(input_settings, output_settings, translator_settings)
