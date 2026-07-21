import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from config.model.config_models import (
    AWSSettings,
    GoogleSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
    TranslatorSettings,
    UserConfig,
)
from constants import (
    CHUNK_LEN,
    GOOGLE_ENDPOINTING_OPTIONS,
    GOOGLE_STT_REGIONS,
    INPUT_CHANNELS,
    INPUT_SAMPLE_RATE,
    OUTPUT_SAMPLE_RATE,
)

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
    def get_app_config_dir() -> Path:
        """
        Get the application configuration directory based on the operating system.
        Creates the directory if it doesn't exist.

        Returns:
            Path: The full path to the app configuration directory.
        """
        # Use platform-specific directories
        if os.name == 'nt':  # Windows
            config_dir = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / 'LiveTranslation'
        else:  # Linux, macOS, etc.
            config_dir = Path(os.path.expanduser('~')) / '.config' / 'live-translation'

        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir

    @staticmethod
    def _get_config_path() -> Path:
        """
        Get the full path to the config.json file.

        Returns:
            Path: The full path to the config.json file.
        """
        config_dir = ConfigManager.get_app_config_dir()

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
        return UserConfig(
            input_settings=ConfigManager._parse_input_settings(raw_config.get('input_settings', {})),
            output_settings=ConfigManager._parse_output_settings(raw_config.get('output_settings', {})),
            translator_settings=ConfigManager._parse_translator_settings(raw_config.get('translator_settings', {})),
        )

    @staticmethod
    def _parse_input_settings(raw: dict) -> InputSettings:
        """
        Parse the input settings from the raw configuration.

        Args:
            raw (dict): The raw input settings data.

        Returns:
            InputSettings: The parsed input settings.
        """
        return InputSettings(
            input_device=raw.get('input_device', 'default'),
            input_device_index=raw.get('input_device_index'),
            input_sample_rate=raw.get('input_sample_rate', INPUT_SAMPLE_RATE),
            input_channels=raw.get('input_channels', INPUT_CHANNELS),
        )

    @staticmethod
    def _parse_output_settings(raw: dict) -> OutputSettings:
        """
        Parse the output settings from the raw configuration.

        Args:
            raw (dict): The raw output settings data.

        Returns:
            OutputSettings: The parsed output settings.
        """
        raw_speaker = raw.get('speaker_settings', {})
        raw_mumble = raw.get('mumble_settings', {})
        return OutputSettings(
            output_method=raw.get('output_method'),
            output_sample_rate=raw.get('output_sample_rate', OUTPUT_SAMPLE_RATE),
            chunk_len=raw.get('chunk_len', CHUNK_LEN),
            speaker_settings=SpeakerSettings(
                output_device=raw_speaker.get('output_device', 'default'),
                output_device_index=raw_speaker.get('output_device_index', None),
            ),
            mumble_settings=MumbleSettings(
                ip_address=raw_mumble.get('ip_address', 'localhost'),
                port=raw_mumble.get('port', 64738),
                language_channel_mapping=raw_mumble.get('language_channel_mapping', {}),
                use_custom_server=raw_mumble.get('use_custom_server', False),
                superuser_password=raw_mumble.get('superuser_password', None),
            ),
        )

    @staticmethod
    def _parse_language_settings(raw: dict) -> dict[str, LanguageSettings]:
        """
        Parse the language settings from the raw configuration.

        Args:
            raw (dict): The raw language settings data.

        Returns:
            dict[str, LanguageSettings]: The parsed language settings.
        """
        return {
            lang: LanguageSettings(
                voice_id=val['voice_id'],
                engine=val.get('engine', 'standard'),
                show_transcript=val.get('show_transcript', False),
            )
            for lang, val in raw.items()
        }

    @staticmethod
    def _parse_aws_settings(raw: dict) -> AWSSettings:
        """
        Parse the AWS settings from the raw configuration.

        Args:
            raw (dict): The raw AWS settings data.

        Returns:
            AWSSettings: The parsed AWS settings.
        """
        return AWSSettings(
            region=raw.get('region', 'eu-central-1'),
            source_language=raw.get('source_language', 'de-DE'),
            show_source_transcript=raw.get('show_source_transcript', True),
            target_languages=ConfigManager._parse_language_settings(raw.get('target_languages', {})),
        )

    @staticmethod
    def _parse_google_settings(raw: dict) -> GoogleSettings:
        """
        Parse the Google settings from the raw configuration.

        Args:
            raw (dict): The raw Google settings data.

        Returns:
            GoogleSettings: The parsed Google settings.
        """

        endpointing = raw.get('endpointing_sensitivity', 'short')
        if endpointing not in GOOGLE_ENDPOINTING_OPTIONS.values():
            endpointing = 'short'

        region = raw.get('region', 'eu')
        if region not in GOOGLE_STT_REGIONS:
            region = 'eu'

        return GoogleSettings(
            credentials_path=raw.get('credentials_path', ''),
            source_language=raw.get('source_language', 'de-DE'),
            show_source_transcript=raw.get('show_source_transcript', False),
            target_languages=ConfigManager._parse_language_settings(raw.get('target_languages', {})),
            endpointing_sensitivity=endpointing,
            region=region,
        )

    @staticmethod
    def _parse_translator_settings(raw: dict) -> TranslatorSettings:
        """
        Parse the translator settings from the raw configuration.

        Args:
            raw (dict): The raw translator settings data.

        Returns:
            TranslatorSettings: The parsed translator settings.
        """
        return TranslatorSettings(
            translator=raw.get('translator', 'aws'),
            aws_settings=ConfigManager._parse_aws_settings(raw.get('aws_settings', {})),
            google_settings=ConfigManager._parse_google_settings(raw.get('google_settings', {})),
        )
