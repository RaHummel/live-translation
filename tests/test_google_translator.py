import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from google.cloud.speech_v2.types import cloud_speech

from config.model.config_models import (
    GoogleSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SpeakerSettings,
)
from translators.google_translator import GoogleTranslator


class TestGoogleTranslator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.google_settings = GoogleSettings(
            credentials_path='',
            source_language='de-DE',
            show_source_transcript=True,
            target_languages={
                'en-US': LanguageSettings(
                    voice_id='en-US-Standard-A',
                    engine='standard',
                    show_transcript=True,
                )
            },
            endpointing_sensitivity='short',
        )
        self.input_settings = InputSettings(
            input_device='mic',
            input_device_index=0,
            input_sample_rate=16000,
            input_channels=1,
        )
        self.output_settings = OutputSettings(
            output_method='speaker',
            output_sample_rate=16000,
            chunk_len=1024,
            speaker_settings=SpeakerSettings(output_device='spk', output_device_index=0),
            mumble_settings=MumbleSettings(ip_address='localhost', port=64738, language_channel_mapping={}),
        )

    async def test_streaming_recognition_uses_short_endpointing_sensitivity(self):
        captured = {}

        class FakeSpeechClient:
            async def streaming_recognize(self, requests):
                first_request = await anext(requests)
                captured['streaming_config'] = first_request.streaming_config

                async def response_iter():
                    result = SimpleNamespace(
                        alternatives=[SimpleNamespace(transcript='Hallo Welt')],
                        is_final=True,
                    )
                    yield SimpleNamespace(results=[result])

                return response_iter()

        with (
            patch('translators.google_translator.translate.TranslationServiceAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.texttospeech.TextToSpeechAsyncClient', return_value=AsyncMock()),
        ):
            translator = GoogleTranslator(self.google_settings, self.input_settings, self.output_settings)

        translator._speech_client = FakeSpeechClient()
        translator._project_id = 'demo-project'
        translator._is_running = True
        translator._translate_and_tts = AsyncMock(side_effect=lambda _transcript, _language: shutdown_event.set())

        shutdown_event = asyncio.Event()

        async def mic_stream():
            yield b'audio'
            await shutdown_event.wait()

        await translator._run_streaming_recognition(mic_stream(), shutdown_event)

        streaming_features = captured['streaming_config'].streaming_features
        self.assertFalse(streaming_features.interim_results)
        self.assertEqual(
            streaming_features.endpointing_sensitivity,
            cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT,
        )

    async def test_streaming_recognition_uses_supershort_endpointing_sensitivity(self):
        captured = {}

        class FakeSpeechClient:
            async def streaming_recognize(self, requests):
                first_request = await anext(requests)
                captured['streaming_config'] = first_request.streaming_config

                async def response_iter():
                    result = SimpleNamespace(
                        alternatives=[SimpleNamespace(transcript='Hallo Welt')],
                        is_final=True,
                    )
                    yield SimpleNamespace(results=[result])

                return response_iter()

        self.google_settings.endpointing_sensitivity = 'supershort'

        with (
            patch('translators.google_translator.translate.TranslationServiceAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.texttospeech.TextToSpeechAsyncClient', return_value=AsyncMock()),
        ):
            translator = GoogleTranslator(self.google_settings, self.input_settings, self.output_settings)

        translator._speech_client = FakeSpeechClient()
        translator._project_id = 'demo-project'
        translator._is_running = True
        translator._translate_and_tts = AsyncMock(side_effect=lambda _transcript, _language: shutdown_event.set())

        shutdown_event = asyncio.Event()

        async def mic_stream():
            yield b'audio'
            await shutdown_event.wait()

        await translator._run_streaming_recognition(mic_stream(), shutdown_event)

        streaming_features = captured['streaming_config'].streaming_features
        self.assertEqual(
            streaming_features.endpointing_sensitivity,
            cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SUPERSHORT,
        )

    async def test_translate_and_tts_uses_async_translate_v3_client(self):
        with (
            patch('translators.google_translator.translate.TranslationServiceAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.texttospeech.TextToSpeechAsyncClient', return_value=AsyncMock()),
        ):
            translator = GoogleTranslator(self.google_settings, self.input_settings, self.output_settings)

        translator._project_id = 'demo-project'
        translator._google_tts = AsyncMock()
        translator._translate_client = MagicMock()
        translator._translate_client.translate_text = AsyncMock(
            return_value=SimpleNamespace(
                translations=[SimpleNamespace(translated_text='Hello world')],
            )
        )

        await translator._translate_and_tts('Hallo Welt', 'en-US')

        translator._translate_client.translate_text.assert_awaited_once()
        kwargs = translator._translate_client.translate_text.await_args.kwargs
        self.assertEqual(kwargs['parent'], 'projects/demo-project/locations/global')
        self.assertEqual(kwargs['contents'], ['Hallo Welt'])
        self.assertEqual(kwargs['mime_type'], 'text/plain')
        self.assertEqual(kwargs['source_language_code'], 'de')
        self.assertEqual(kwargs['target_language_code'], 'en')
        translator._google_tts.assert_awaited_once_with('Hello world', 'en-US')
