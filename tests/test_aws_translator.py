import asyncio
import contextlib
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from amazon_transcribe.model import Alternative, Result, Transcript, TranscriptEvent

from config.model.config_models import (
    AWSSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
)
from translators.aws_translator import AWSTranslator

from .stubs import SoundOutputStub


class TestAWSTranslator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.aws_settings = AWSSettings(
            region='eu-central-1',
            source_language='de-DE',
            show_source_transcript=True,
            target_languages={'en-US': LanguageSettings(voice_id='Justin', engine='standard', show_transcript=True)},
        )
        self.input_settings = InputSettings(
            input_device='mic', input_device_index=0, input_sample_rate=16000, input_channels=1
        )
        self.output_settings = OutputSettings(
            output_method='speaker',
            output_sample_rate=16000,
            chunk_len=1024,
            speaker_settings=SpeakerSettings(output_device='spk', output_device_index=0),
            mumble_settings=MumbleSettings(ip_address='localhost', port=64738, language_channel_mapping={}),
        )

        with patch('boto3.client'), patch('translators.aws_translator.TranscribeStreamingClient'):
            self.translator = AWSTranslator(self.aws_settings, self.input_settings, self.output_settings)

    async def test_start_translation_logic(self):
        # Arrange
        self.translator._translate.translate_text = MagicMock(return_value={'TranslatedText': 'Hello'})
        self.translator._polly.synthesize_speech = MagicMock(return_value={'AudioStream': MagicMock()})

        mock_stream = MagicMock()
        mock_stream.input_stream.send_audio_event = AsyncMock()
        mock_stream.input_stream.end_stream = AsyncMock()
        mock_stream.output_stream = self._dummy_output_stream()
        self.translator._transcribe_client.start_stream_transcription = AsyncMock(return_value=mock_stream)

        shutdown_event = asyncio.Event()
        asyncio.get_running_loop().call_later(0.05, shutdown_event.set)

        sound_output_stub = SoundOutputStub()

        # Act
        await self.translator.start_translation({'en-US': sound_output_stub}, self._mock_mic_stream(), shutdown_event)

        # Assert
        mock_stream.input_stream.send_audio_event.assert_called_with(audio_chunk=b'dummy_audio_chunk')
        self.assertTrue(sound_output_stub.play_called)

    async def test_polly_engine_parameter(self):
        # Arrange
        self.translator._translate.translate_text = MagicMock(return_value={'TranslatedText': 'Hello'})
        self.translator._polly.synthesize_speech = MagicMock(return_value={'AudioStream': MagicMock()})

        # Set engine to 'neural'
        self.translator._aws_settings.target_languages['en-US'].engine = 'neural'

        mock_stream = MagicMock()
        mock_stream.input_stream.send_audio_event = AsyncMock()
        mock_stream.input_stream.end_stream = AsyncMock()
        mock_stream.output_stream = self._dummy_output_stream()
        self.translator._transcribe_client.start_stream_transcription = AsyncMock(return_value=mock_stream)

        shutdown_event = asyncio.Event()
        asyncio.get_running_loop().call_later(0.05, shutdown_event.set)

        sound_output_stub = SoundOutputStub()

        # Act
        await self.translator.start_translation({'en-US': sound_output_stub}, self._mock_mic_stream(), shutdown_event)

        # Assert
        self.translator._polly.synthesize_speech.assert_called_with(
            Engine='neural',
            LanguageCode='en-US',
            Text='Hello',
            VoiceId='Justin',
            SampleRate='16000',
            OutputFormat='pcm',
        )

    @staticmethod
    def _create_mock_event(transcript='Test'):
        event = MagicMock(spec=TranscriptEvent)
        event.transcript = MagicMock(spec=Transcript)
        result = MagicMock(spec=Result, is_partial=False, channel_id='ch_0')
        result.alternatives = [MagicMock(spec=Alternative, transcript=transcript)]
        event.transcript.results = [result]
        return event

    async def _dummy_output_stream(self):
        yield self._create_mock_event()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.Future()

    async def _mock_mic_stream(self):
        yield b'dummy_audio_chunk'
        await asyncio.sleep(0.1)
