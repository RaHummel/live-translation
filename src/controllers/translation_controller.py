import logging
import threading
from typing import Dict, Optional

from PySide6.QtCore import QObject, Signal

from config.model.config_models import UserConfig
from sound_inputs.microphone import Microphone
from sound_outputs.mumble import MumbleClient
from sound_outputs.speaker import Speaker
from translation import SoundOutput, Translation
from translators.aws_translator import AWSTranslator
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

    def __init__(self, callbacks: TranslationCallbacks):
        super().__init__()
        self._callbacks = callbacks
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
            lang_to_output: Dict[str, SoundOutput] = {}

            # --- Initialize Translator ---
            translator_type = config.translator_settings.translator
            if translator_type == 'aws':
                target_languages = config.translator_settings.aws_settings.target_languages
                translator = AWSTranslator(
                    config.translator_settings.aws_settings,
                    config.input_settings,
                    config.output_settings,
                    self._callbacks,
                )
                LOGGER.debug('AWS Translator initialized.')
            else:
                raise ValueError(f'Translator type "{translator_type}" not supported.')

            # --- Initialize Output Method ---
            output_method = config.output_settings.output_method
            if output_method == 'speaker':
                if len(target_languages) != 1:
                    raise ValueError('Speaker output requires exactly one target language.')
                lang_to_output[next(iter(target_languages))] = Speaker(config.output_settings)
                LOGGER.debug('Speaker output initialized.')
            elif output_method == 'mumble':
                if not target_languages:
                    raise ValueError('Mumble output requires at least one target language.')
                for lang in target_languages:
                    sound_output = MumbleClient(config.output_settings, lang)
                    sound_output.connect()
                    lang_to_output[lang] = sound_output
                    LOGGER.debug('Mumble client initialized and connected for language: %s', lang)
            else:
                raise ValueError(f'Unsupported output method "{output_method}" selected.')

            # --- Initialize Microphone Input ---
            microphone = Microphone(config.input_settings)
            LOGGER.debug('Microphone input initialized.')

            # --- Initialize Translation Core ---
            self._translation = Translation(translator, microphone, lang_to_output)

            # --- Start Translation in a Separate Thread ---
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

        # Use a separate thread to handle the blocking join operation
        shutdown_thread = threading.Thread(target=self._shutdown_and_join, daemon=True)
        shutdown_thread.start()

    def _shutdown_and_join(self):
        """Helper method to run in a separate thread for a clean shutdown."""
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
