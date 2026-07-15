import asyncio
import io
import unittest
import wave
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

EndpointingSensitivity = cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity


class TestGoogleTranslator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # google.auth.default() would otherwise hit the real metadata server / network
        # on every GoogleTranslator() construction, which is what made these tests slow.
        auth_patcher = patch('google.auth.default', return_value=(MagicMock(), 'demo-project'))
        auth_patcher.start()
        self.addCleanup(auth_patcher.stop)

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

    def _build_translator(self) -> GoogleTranslator:
        with (
            patch('translators.google_translator.translate.TranslationServiceAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.texttospeech.TextToSpeechAsyncClient', return_value=AsyncMock()),
        ):
            return GoogleTranslator(self.google_settings, self.input_settings, self.output_settings)

    # -- _get_endpointing_sensitivity -----------------------------------------------------

    def test_get_endpointing_sensitivity_maps_configured_values(self):
        translator = self._build_translator()

        cases = {
            'standard': EndpointingSensitivity.ENDPOINTING_SENSITIVITY_STANDARD,
            'short': EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT,
            'supershort': EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SUPERSHORT,
            'unknown-value': EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT,  # fallback
        }
        for configured_value, expected in cases.items():
            with self.subTest(configured_value=configured_value):
                translator._google_settings.endpointing_sensitivity = configured_value
                self.assertEqual(translator._get_endpointing_sensitivity(), expected)

    # -- _normalize_language_code -----------------------------------------------------------

    def test_normalize_language_code_strips_region_suffix(self):
        self.assertEqual(GoogleTranslator._normalize_language_code('de-DE'), 'de')
        self.assertEqual(GoogleTranslator._normalize_language_code('en-US'), 'en')
        self.assertEqual(GoogleTranslator._normalize_language_code('fr'), 'fr')

    # -- _run_streaming_recognition ----------------------------------------------------------

    async def test_run_streaming_recognition_builds_request_and_dispatches_translation(self):
        captured = {}
        shutdown_event = asyncio.Event()

        class FakeSpeechClient:
            async def streaming_recognize(self, requests):
                first_request = await anext(requests)
                captured['first_request'] = first_request

                async def response_iter():
                    result = SimpleNamespace(
                        alternatives=[SimpleNamespace(transcript='Hallo Welt')],
                        is_final=True,
                    )
                    yield SimpleNamespace(results=[result])

                return response_iter()

        translator = self._build_translator()
        translator._speech_client = FakeSpeechClient()
        translator._project_id = 'demo-project'
        translator._translation_callbacks = MagicMock()
        translator._translate_and_tts = AsyncMock(side_effect=lambda _t, _l: shutdown_event.set())

        async def mic_stream():
            yield b'audio'
            await shutdown_event.wait()

        await translator._run_streaming_recognition(mic_stream(), shutdown_event)

        streaming_config = captured['first_request'].streaming_config
        self.assertEqual(captured['first_request'].recognizer, 'projects/demo-project/locations/eu/recognizers/_')
        self.assertEqual(streaming_config.config.language_codes, ['de-DE'])
        self.assertEqual(streaming_config.config.model, 'chirp_3')
        self.assertFalse(streaming_config.streaming_features.interim_results)
        self.assertEqual(
            streaming_config.streaming_features.endpointing_sensitivity,
            EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT,
        )

        translator._translation_callbacks.update_source_field.assert_called_once_with('Hallo Welt')
        translator._translate_and_tts.assert_awaited_once_with('Hallo Welt', 'en-US')

    async def test_run_streaming_recognition_ignores_non_final_and_empty_results(self):
        shutdown_event = asyncio.Event()

        class FakeSpeechClient:
            async def streaming_recognize(self, requests):
                await anext(requests)

                async def response_iter():
                    yield SimpleNamespace(results=[])
                    yield SimpleNamespace(
                        results=[SimpleNamespace(alternatives=[SimpleNamespace(transcript='...')], is_final=False)]
                    )
                    shutdown_event.set()

                return response_iter()

        translator = self._build_translator()
        translator._speech_client = FakeSpeechClient()
        translator._project_id = 'demo-project'
        translator._translate_and_tts = AsyncMock()

        async def mic_stream():
            yield b'audio'
            await shutdown_event.wait()

        await translator._run_streaming_recognition(mic_stream(), shutdown_event)

        translator._translate_and_tts.assert_not_awaited()

    async def test_run_streaming_recognition_returns_early_without_project_id(self):
        translator = self._build_translator()
        translator._speech_client = MagicMock()
        translator._project_id = None

        shutdown_event = asyncio.Event()

        async def mic_stream():
            yield b'audio'

        # Should return immediately instead of looping/hanging.
        await asyncio.wait_for(
            translator._run_streaming_recognition(mic_stream(), shutdown_event),
            timeout=1,
        )

    # -- _translate_and_tts ------------------------------------------------------------------

    async def test_translate_and_tts_uses_async_translate_v3_client(self):
        translator = self._build_translator()

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

    async def test_translate_and_tts_skips_tts_when_translation_is_empty(self):
        translator = self._build_translator()

        translator._project_id = 'demo-project'
        translator._google_tts = AsyncMock()
        translator._translate_client = MagicMock()
        translator._translate_client.translate_text = AsyncMock(
            return_value=SimpleNamespace(translations=[SimpleNamespace(translated_text='')])
        )

        await translator._translate_and_tts('Hallo Welt', 'en-US')

        translator._google_tts.assert_not_awaited()

    async def test_translate_and_tts_does_nothing_without_project_id(self):
        translator = self._build_translator()

        translator._project_id = None
        translator._translate_client = MagicMock()
        translator._translate_client.translate_text = AsyncMock()

        await translator._translate_and_tts('Hallo Welt', 'en-US')

        translator._translate_client.translate_text.assert_not_awaited()

    # -- _google_tts -------------------------------------------------------------------------

    async def test_google_tts_strips_wav_header_before_playback(self):
        translator = self._build_translator()

        raw_pcm = b'\x01\x02\x03\x04'
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(raw_pcm)

        translator._tts_client = AsyncMock()
        translator._tts_client.synthesize_speech = AsyncMock(
            return_value=SimpleNamespace(audio_content=wav_buffer.getvalue())
        )

        sound_output = AsyncMock()
        translator._language_to_output = {'en-US': sound_output}

        await translator._google_tts('Hello world', 'en-US')

        sound_output.play.assert_awaited_once()
        played_stream = sound_output.play.await_args.args[0]
        self.assertEqual(played_stream.read(), raw_pcm)

    # -- start_translation -------------------------------------------------------------------

    async def test_start_translation_initializes_and_tears_down_clients(self):
        translator = self._build_translator()
        shutdown_event = asyncio.Event()
        shutdown_event.set()  # trigger immediate shutdown branch

        async def mic_stream():
            return
            yield  # pragma: no cover - makes this an async generator

        with (
            patch('translators.google_translator.speech.SpeechAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.translate.TranslationServiceAsyncClient', return_value=MagicMock()),
            patch('translators.google_translator.texttospeech.TextToSpeechAsyncClient', return_value=AsyncMock()),
        ):
            await translator.start_translation({}, mic_stream(), shutdown_event)

        self.assertIsNone(translator._speech_client)
        self.assertIsNone(translator._translate_client)
        self.assertIsNone(translator._tts_client)
