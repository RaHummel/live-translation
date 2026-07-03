import logging
import threading
from typing import Dict, Optional

from PySide6.QtCore import QObject, Signal

from config.model.config_models import UserConfig
from sound_inputs.microphone import Microphone
from sound_outputs.mumble import MumbleClient
from sound_outputs.speaker import Speaker
from translation import SoundOutput, Translation, Translator
from translators.aws_translator import AWSTranslator
from translators.google_translator import GoogleTranslator
from translators.translation_callbacks import TranslationCallbacks

LOGGER = logging.getLogger(__name__)


class TranslationController(QObject):
    """
    Controller responsible for orchestrating the translation service.
    Handles component initialization, thread management, and lifecycle events.
    """

    # Signals to communicate with the UI
    status_message_signal = Signal(str, int)
    status_label_signal = Signal(str)
    start_button_enabled = Signal(bool)
    stop_button_enabled = Signal(bool)
    update_source_field_signal = Signal(str)
    update_target_field_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._callbacks = TranslationCallbacks(
            update_source_field=self.update_source_field_signal.emit,
            update_target_field=self.update_target_field_signal.emit,
        )
        self._translation_thread: Optional[threading.Thread] = None
        self._translation: Optional[Translation] = None

    def start_service(self, config: UserConfig):
        """Initializes and starts the translation service in a separate thread."""
        self.status_message_signal.emit('Translation service starting...', 3000)
        self.start_button_enabled.emit(False)
        self.stop_button_enabled.emit(True)
        self.status_label_signal.emit('Status: Starting...')
        LOGGER.debug('Initiating translation service setup.')

        try:
            translator, target_languages = self._create_translator(config)
            lang_to_output = self._create_outputs(config, target_languages)
            microphone = Microphone(config.input_settings)
            LOGGER.debug('Microphone input initialized.')

            self._translation = Translation(translator, microphone, lang_to_output)
            self._translation_thread = threading.Thread(
                target=self._translation.run, daemon=True, name='TranslationServiceThread'
            )
            self._translation_thread.start()
            LOGGER.info('Translation service thread started.')

            self.status_label_signal.emit('Status: Running')
            self.status_message_signal.emit('Translation service is now running!', 3000)

        except Exception as e:
            error_msg = f'Failed to start translation service: {e}'
            self.status_message_signal.emit(error_msg, 7000)
            self.status_label_signal.emit('Status: Error')
            LOGGER.critical(error_msg, exc_info=True)
            self._reset_gui_state_on_error()

    def stop_service(self):
        """Initiates a non-blocking shutdown of the translation service."""
        self.status_message_signal.emit('Translation service stopping...', 5000)
        self.start_button_enabled.emit(False)
        self.stop_button_enabled.emit(False)
        self.status_label_signal.emit('Status: Stopping...')
        LOGGER.debug('Initiating translation service shutdown.')

        shutdown_thread = threading.Thread(target=self._shutdown_and_join, daemon=True)
        shutdown_thread.start()

    def _create_translator(self, config: UserConfig) -> tuple[Translator, dict]:
        """Instantiates the correct Translator based on config and returns it with its target language dict."""
        translator_type = config.translator_settings.translator

        if translator_type == 'aws':
            aws_settings = config.translator_settings.aws_settings
            if aws_settings is None:
                raise ValueError('AWS translator selected but AWS settings are not configured.')

            translator = AWSTranslator(aws_settings, config.input_settings, config.output_settings, self._callbacks)
            LOGGER.debug('AWS Translator initialized.')
            return translator, aws_settings.target_languages

        if translator_type == 'google':
            google_settings = config.translator_settings.google_settings
            if google_settings is None:
                raise ValueError('Google translator selected but Google settings are not configured.')

            translator = GoogleTranslator(
                google_settings, config.input_settings, config.output_settings, self._callbacks
            )
            LOGGER.debug('Google Translator initialized.')

            return translator, google_settings.target_languages

        raise ValueError(f'Translator type "{translator_type}" not supported.')

    def _create_outputs(self, config: UserConfig, target_languages: dict) -> Dict[str, SoundOutput]:
        """Instantiates and connects the correct SoundOutput instances for each target language."""
        output_method = config.output_settings.output_method
        lang_to_output: Dict[str, SoundOutput] = {}

        if output_method == 'speaker':
            if len(target_languages) != 1:
                raise ValueError('Speaker output requires exactly one target language.')

            lang_to_output[next(iter(target_languages))] = Speaker(config.output_settings)
            LOGGER.debug('Speaker output initialized.')

        elif output_method == 'mumble':
            if not target_languages:
                raise ValueError('Mumble output requires at least one target language.')

            for lang in target_languages:
                client = MumbleClient(config.output_settings, lang)
                client.connect()
                lang_to_output[lang] = client
                LOGGER.debug('Mumble client initialized and connected for language: %s', lang)

        else:
            raise ValueError(f'Unsupported output method "{output_method}" selected.')

        return lang_to_output

    def _shutdown_and_join(self):
        """Runs in a separate thread to cleanly stop the translation service."""
        if self._translation and self._translation_thread and self._translation_thread.is_alive():
            try:
                self._translation.stop()
                LOGGER.debug('Signaled translation service to stop. Waiting for thread to join...')
                self._translation_thread.join(timeout=10)
                if self._translation_thread.is_alive():
                    LOGGER.warning('Translation thread did not terminate within timeout. Forcing cleanup.')
            except Exception as e:
                LOGGER.error(f'Error during thread shutdown: {e}', exc_info=True)

        LOGGER.info('Translation service stopped')
        self.status_label_signal.emit('Status: Stopped')
        self.status_message_signal.emit('Translation service stopped.', 3000)
        self.start_button_enabled.emit(True)
        self.stop_button_enabled.emit(False)

    def _reset_gui_state_on_error(self):
        """Resets the GUI state after a startup failure."""
        self.start_button_enabled.emit(True)
        self.stop_button_enabled.emit(False)
