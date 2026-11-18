import asyncio
import contextlib
import io
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from amazon_transcribe.model import Alternative, Result, Transcript, TranscriptEvent
from botocore.exceptions import ClientError

from config.model.config_models import (
    AWSSettings,
    InputSettings,
    LanguageSettings,
    MumbleSettings,
    OutputSettings,
    SegmentationSettings,
    SpeakerSettings,
)
from translators.aws_translator import AWSTranslator, TranscriptEventHandler

from .stubs import SoundOutputStub

ONE_SECOND_PCM = b'\x00\x10' * 16000
# 1 s of silence at 16 kHz, used to check how much trailing pause is kept.
ONE_SECOND_SILENCE = b'\x00\x00' * 16000


def polly_response(**_kwargs):
    return {'AudioStream': io.BytesIO(ONE_SECOND_PCM)}


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
        self.segmentation_settings = SegmentationSettings(max_speaking_rate=1.4, max_backlog_s=5.0)

        with patch('boto3.client'), patch('translators.aws_translator.TranscribeStreamingClient'):
            self.translator = AWSTranslator(
                self.aws_settings,
                self.input_settings,
                self.output_settings,
                segmentation_settings=self.segmentation_settings,
            )

        self.translator._translate.translate_text = MagicMock(return_value={'TranslatedText': 'Hello'})
        self.translator._polly.synthesize_speech = MagicMock(side_effect=polly_response)

    # -- start_translation -------------------------------------------------------------------

    async def test_start_translation_logic(self):
        mock_stream = self._mock_transcription_stream()
        shutdown_event = asyncio.Event()
        asyncio.get_running_loop().call_later(0.05, shutdown_event.set)
        sound_output_stub = SoundOutputStub()

        await self.translator.start_translation({'en-US': sound_output_stub}, self._mock_mic_stream(), shutdown_event)

        mock_stream.input_stream.send_audio_event.assert_called_with(audio_chunk=b'dummy_audio_chunk')
        self.assertTrue(sound_output_stub.play_called)
        self.assertEqual(sound_output_stub.played_bytes.read(), ONE_SECOND_PCM)

        kwargs = self.translator._transcribe_client.start_stream_transcription.await_args.kwargs
        self.assertTrue(kwargs['enable_partial_results_stabilization'])
        self.assertEqual(kwargs['partial_results_stability'], 'high')

    async def test_polly_engine_parameter(self):
        self.translator._aws_settings.target_languages['en-US'].engine = 'neural'
        self._mock_transcription_stream()
        shutdown_event = asyncio.Event()
        asyncio.get_running_loop().call_later(0.05, shutdown_event.set)

        await self.translator.start_translation({'en-US': SoundOutputStub()}, self._mock_mic_stream(), shutdown_event)

        self.translator._polly.synthesize_speech.assert_called_with(
            Engine='neural',
            LanguageCode='en-US',
            Text='Hello',
            VoiceId='Justin',
            SampleRate='16000',
            OutputFormat='pcm',
        )

    # -- TranscriptEventHandler --------------------------------------------------------------

    async def test_handler_routes_partial_and_final_results_to_pipeline(self):
        pipeline = MagicMock()
        handler = TranscriptEventHandler(MagicMock(), pipeline)

        await handler.handle_transcript_event(self._create_mock_event('Das ist', is_partial=True))
        await handler.handle_transcript_event(self._create_mock_event('Das ist gut.', is_partial=False))

        pipeline.on_interim.assert_called_once_with('Das ist')
        pipeline.on_final.assert_called_once_with('Das ist gut.')

    async def test_handler_ignores_other_channels_and_empty_results(self):
        pipeline = MagicMock()
        handler = TranscriptEventHandler(MagicMock(), pipeline)

        await handler.handle_transcript_event(self._create_mock_event('Hallo', channel_id='ch_1'))
        empty = self._create_mock_event('Hallo')
        empty.transcript.results = []
        await handler.handle_transcript_event(empty)

        pipeline.on_interim.assert_not_called()
        pipeline.on_final.assert_not_called()

    async def test_partials_are_segmented_and_spoken_in_order_without_respeak(self):
        spoken = []

        async def record(text, language):
            spoken.append((text, language))

        self.translator._translate_and_tts = record
        handler = TranscriptEventHandler(MagicMock(), self.translator._pipeline)

        await handler.handle_transcript_event(self._create_mock_event('Das ist der erste Satz.', is_partial=True))
        await handler.handle_transcript_event(
            self._create_mock_event('Das ist der erste Satz. Und dann geht', is_partial=True)
        )
        await handler.handle_transcript_event(
            self._create_mock_event('Das ist der erste Satz. Und dann geht es weiter.', is_partial=False)
        )
        await asyncio.wait_for(self.translator._pipeline.join(), timeout=1)
        await self.translator._pipeline.stop()

        self.assertEqual(
            spoken,
            [('Das ist der erste Satz.', 'en-US'), ('Und dann geht es weiter.', 'en-US')],
        )

    # -- Polly / backlog control -------------------------------------------------------------

    async def test_polly_uses_plain_text_without_backlog_and_registers_playout(self):
        sound_output = SoundOutputStub()
        self.translator._language_to_output = {'en-US': sound_output}
        self.translator._pipeline.register_playout = MagicMock()

        await self.translator._aws_polly_tts('Hello', 'en-US')

        kwargs = self.translator._polly.synthesize_speech.call_args.kwargs
        self.assertEqual(kwargs['Text'], 'Hello')
        self.assertNotIn('TextType', kwargs)
        language, duration = self.translator._pipeline.register_playout.call_args.args
        self.assertEqual(language, 'en-US')
        self.assertAlmostEqual(duration, 1.0)
        self.assertTrue(sound_output.play_called)

    async def test_polly_trailing_pause_follows_punctuation_and_speaking_rate(self):
        sound_output = SoundOutputStub()
        self.translator._language_to_output = {'en-US': sound_output}
        self.translator._pipeline.register_playout = MagicMock()
        self.translator._pipeline.backlog_seconds = MagicMock(return_value=10.0)  # → rate 1.4
        self.translator._polly.synthesize_speech = MagicMock(
            return_value={'AudioStream': io.BytesIO(ONE_SECOND_PCM + ONE_SECOND_SILENCE)}
        )

        await self.translator._aws_polly_tts('Hello.', 'en-US')

        _language, duration = self.translator._pipeline.register_playout.call_args.args
        self.assertAlmostEqual(duration, 1.0 + 0.30 / 1.4, places=3)

    async def test_polly_skips_playback_for_silent_audio(self):
        sound_output = SoundOutputStub()
        self.translator._language_to_output = {'en-US': sound_output}
        self.translator._polly.synthesize_speech = MagicMock(
            return_value={'AudioStream': io.BytesIO(b'\x00\x00' * 1600)}
        )

        await self.translator._aws_polly_tts('Hello', 'en-US')

        self.assertFalse(sound_output.play_called)

    async def test_polly_uses_ssml_prosody_rate_when_backlog_builds_up(self):
        self.translator._language_to_output = {'en-US': SoundOutputStub()}
        self.translator._pipeline.backlog_seconds = MagicMock(return_value=10.0)

        await self.translator._aws_polly_tts('Tom & Jerry <3', 'en-US')

        kwargs = self.translator._polly.synthesize_speech.call_args.kwargs
        self.assertEqual(kwargs['TextType'], 'ssml')
        self.assertEqual(kwargs['Text'], '<speak><prosody rate="140%">Tom &amp; Jerry &lt;3</prosody></speak>')

    async def test_polly_falls_back_to_plain_text_when_ssml_rate_is_rejected(self):
        sound_output = SoundOutputStub()
        self.translator._language_to_output = {'en-US': sound_output}
        self.translator._pipeline.backlog_seconds = MagicMock(return_value=10.0)
        rejected = ClientError({'Error': {'Code': 'InvalidSsmlException', 'Message': 'no'}}, 'SynthesizeSpeech')
        self.translator._polly.synthesize_speech = MagicMock(side_effect=[rejected, polly_response()])

        await self.translator._aws_polly_tts('Hello', 'en-US')

        calls = self.translator._polly.synthesize_speech.call_args_list
        self.assertEqual(calls[0].kwargs['TextType'], 'ssml')
        self.assertNotIn('TextType', calls[1].kwargs)
        self.assertTrue(self.translator._pipeline.speaking_rate_disabled('en-US'))
        self.assertTrue(sound_output.play_called)

    async def test_translate_and_tts_skips_tts_for_empty_translation(self):
        self.translator._translate.translate_text = MagicMock(return_value={'TranslatedText': ''})
        self.translator._aws_polly_tts = AsyncMock()

        await self.translator._translate_and_tts('Hallo', 'en-US')

        self.translator._aws_polly_tts.assert_not_awaited()

    # -- helpers -----------------------------------------------------------------------------

    def _mock_transcription_stream(self):
        mock_stream = MagicMock()
        mock_stream.input_stream.send_audio_event = AsyncMock()
        mock_stream.input_stream.end_stream = AsyncMock()
        mock_stream.output_stream = self._dummy_output_stream()
        self.translator._transcribe_client.start_stream_transcription = AsyncMock(return_value=mock_stream)
        return mock_stream

    @staticmethod
    def _create_mock_event(transcript='Test', is_partial=False, channel_id='ch_0'):
        event = MagicMock(spec=TranscriptEvent)
        event.transcript = MagicMock(spec=Transcript)
        result = MagicMock(spec=Result, is_partial=is_partial, channel_id=channel_id)
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
