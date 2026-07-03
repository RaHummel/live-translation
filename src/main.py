import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtWidgets import QApplication

from config.config_manager import ConfigManager
from config.model.config_models import UserConfig
from main_window import MainWindow
from sound_inputs.microphone import Microphone
from sound_outputs.mumble import MumbleClient
from sound_outputs.speaker import Speaker
from translation import Translation
from translators.aws_translator import AWSTranslator
from translators.google_translator import GoogleTranslator


def get_log_file_path() -> Path:
    """Get a fixed OS-specific log file path and ensure the log directory exists."""
    log_dir = ConfigManager.get_app_config_dir() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / 'live-translation.log'


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise, set to INFO.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        get_log_file_path(),
        maxBytes=1_048_576,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)

    # Replace existing handlers to avoid duplicates when app restarts in-process.
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    # Reduce verbosity of noisy third-party libraries
    if verbose:
        logging.getLogger('botocore').setLevel(logging.INFO)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)


def run_cli_mode(arguments, usr_config: UserConfig):
    """
    Executes the main logic of the translation service in CLI mode.
    This function encapsulates the existing CLI code.

    Args:
        arguments: Parsed command-line arguments.
        usr_config (UserConfig): User configuration object.
    """
    LOGGER = logging.getLogger(__name__)
    LOGGER.info('Starting Translation Service in CLI mode...')

    # Override config with CLI arguments if provided
    if arguments.source_lang:
        usr_config.translator_settings.aws_settings.source_language = arguments.source_lang

    input_method = 'mic'  # Currently only microphone is supported
    output_method = usr_config.output_settings.output_method
    translator_type = usr_config.translator_settings.translator

    # Determine target languages: CLI takes precedence over config
    target_langs = arguments.target_lang
    if not target_langs:
        target_langs = list(usr_config.translator_settings.aws_settings.target_languages.keys())

    if translator_type == 'aws':
        # Ensure target languages from CLI are in the config
        for lang in target_langs:
            if lang not in usr_config.translator_settings.aws_settings.target_languages:
                raise ValueError(f'Target language {lang} not found in config')

        translator = AWSTranslator(
            usr_config.translator_settings.aws_settings,
            usr_config.input_settings,
            usr_config.output_settings,
        )
    elif translator_type == 'google':
        # Ensure target languages from CLI are in the config
        for lang in target_langs:
            if lang not in usr_config.translator_settings.google_settings.target_languages:
                raise ValueError(f'Target language {lang} not found in config')

        translator = GoogleTranslator(
            usr_config.translator_settings.google_settings,
            usr_config.input_settings,
            usr_config.output_settings,
        )
    else:
        raise ValueError(f'Unsupported translator: {translator_type}')

    if input_method == 'mic':
        sound_input = Microphone(usr_config.input_settings)
    else:
        raise ValueError(f'Unsupported input method: {input_method}')

    if output_method == 'speaker' and len(target_langs) > 1:
        raise ValueError('Multiple target_lang for speaker output not supported')

    target_language_mapping = {}

    for language in target_langs:
        if output_method == 'mumble':
            sound_output = MumbleClient(usr_config.output_settings, language)
            sound_output.connect()
        elif output_method == 'speaker':
            sound_output = Speaker(usr_config.output_settings)
        else:
            raise ValueError(f'Unsupported output method: {output_method}')

        target_language_mapping[language] = sound_output

    translation = Translation(translator, sound_input, target_language_mapping)

    try:
        translation.run()
    finally:
        LOGGER.info('Translation stopped')
        for output in target_language_mapping.values():
            output.stop_audio_stream()


def run_gui_mode(conf_manager: ConfigManager):
    """
    Starts the graphical user interface.

    Args:
        conf_manager (ConfigManager): The configuration manager instance.
    """
    LOGGER = logging.getLogger(__name__)
    LOGGER.info('Starting Translation Service in GUI mode...')
    app = QApplication(sys.argv)
    window = MainWindow(conf_manager)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translation service script.')

    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Run the application in command-line interface (CLI) mode without a graphical user interface.',
    )
    parser.add_argument('-sl', '--source_lang', help='Source language (e.g. de-DE)')
    parser.add_argument(
        '-tl',
        '--target_lang',
        nargs='+',
        help='Target language(s) (e.g. en-US ru-RU)',
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    configure_logging(verbose=args.verbose)

    config_manager = ConfigManager()

    if args.no_gui:
        run_cli_mode(args, config_manager.config)
    else:
        run_gui_mode(config_manager)
