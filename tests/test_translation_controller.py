import unittest
from unittest.mock import MagicMock, patch

from config.model.config_models import (
    AWSSettings,
    InputSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
    TranslatorSettings,
    UserConfig,
)
from controllers.translation_controller import TranslationController
from translators.translation_callbacks import TranslationCallbacks

from .stubs import SoundInputStub, SoundOutputStub, TranslatorStub


class TestTranslationController(unittest.TestCase):
    def setUp(self):
        self.mock_callbacks = MagicMock(spec=TranslationCallbacks)
        self.controller = TranslationController(self.mock_callbacks)

        # Mock signals to verify emissions
        self.controller.status_message_signal = MagicMock()
        self.controller.status_label_signal = MagicMock()
        self.controller.start_button_enabled = MagicMock()
        self.controller.stop_button_enabled = MagicMock()

        # Dummy config
        self.config = UserConfig(
            input_settings=InputSettings('mic', 0, 16000, 1),
            output_settings=OutputSettings(
                'speaker', 16000, 1024, SpeakerSettings('spk', 0), MumbleSettings('localhost', 64738, {})
            ),
            translator_settings=TranslatorSettings(
                'aws', AWSSettings('us-central-1', 'en-US', True, {'de-DE': MagicMock()})
            ),
        )

    @patch('controllers.translation_controller.AWSTranslator')
    @patch('controllers.translation_controller.Speaker')
    @patch('controllers.translation_controller.Microphone')
    @patch('controllers.translation_controller.Translation')
    @patch('controllers.translation_controller.threading.Thread')
    def test_start_service_success_speaker(self, mock_thread, mock_translation, mock_mic, mock_speaker, mock_aws):
        # Arrange
        translator_stub = TranslatorStub()
        speaker_stub = SoundOutputStub()
        microphone_stub = SoundInputStub()
        mock_translation_inst = MagicMock()

        mock_aws.return_value = translator_stub
        mock_speaker.return_value = speaker_stub
        mock_mic.return_value = microphone_stub
        mock_translation.return_value = mock_translation_inst

        # Act
        self.controller.start_service(self.config)

        # Assert
        mock_aws.assert_called_once()
        mock_speaker.assert_called_once()
        mock_mic.assert_called_once()
        mock_translation.assert_called_once_with(translator_stub, microphone_stub, {'de-DE': speaker_stub})

        # Verify thread started
        mock_thread.assert_called_once_with(
            target=mock_translation_inst.run, daemon=True, name='TranslationServiceThread'
        )
        self.assertTrue(mock_thread.return_value.start.called)
        self.controller.status_label_signal.emit.assert_any_call('Status: Running')

    def test_start_service_unsupported_translator(self):
        self.config.translator_settings.translator = 'unsupported'

        self.controller.start_service(self.config)

        self.controller.status_label_signal.emit.assert_any_call('Status: Error')
        self.controller.status_message_signal.emit.assert_called()

    @patch('controllers.translation_controller.threading.Thread')
    def test_stop_service_starts_shutdown_thread(self, mock_thread):
        self.controller.stop_service()

        mock_thread.assert_called_once()
        self.assertTrue(mock_thread.return_value.start.called)
        self.controller.status_label_signal.emit.assert_any_call('Status: Stopping...')

    def test_shutdown_and_join_logic(self):
        mock_translation_inst = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        self.controller._translation = mock_translation_inst
        self.controller._translation_thread = mock_thread

        self.controller._shutdown_and_join()

        mock_translation_inst.stop.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=10)
        self.controller.status_label_signal.emit.assert_any_call('Status: Stopped')
