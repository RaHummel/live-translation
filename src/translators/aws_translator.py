import asyncio
import io
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Dict, List, Optional
from xml.sax.saxutils import escape

import boto3
from amazon_transcribe.client import StartStreamTranscriptionEventStream, TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import Result, TranscriptEvent
from botocore.exceptions import ClientError

from config.model.config_models import AWSSettings, InputSettings, OutputSettings, SegmentationSettings
from translation import SoundOutput, Translator
from translators.segment_pipeline import SegmentPipeline
from translators.translation_callbacks import TranslationCallbacks
from utils.audio_utils import pcm_duration_seconds, tail_pause_seconds, trim_silence

LOGGER = logging.getLogger(__name__)

# Seconds queued segments may still be processed when the translation is stopped.
_SHUTDOWN_DRAIN_TIMEOUT_S = 2.0


class TranscriptEventHandler(TranscriptResultStreamHandler):
    """Feeds partial and final AWS Transcribe results into the segment pipeline."""

    def __init__(self, output_stream, pipeline: SegmentPipeline):
        super().__init__(output_stream)
        self._pipeline = pipeline

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results: List[Result] = transcript_event.transcript.results
        if not results or results[0].channel_id != 'ch_0':
            return

        result = results[0]
        alternatives = result.alternatives
        if not alternatives:
            return

        transcript = alternatives[0].transcript
        if getattr(result, 'is_partial', False):
            self._pipeline.on_interim(transcript)
        else:
            self._pipeline.on_final(transcript)


class AWSTranslator(Translator):
    def __init__(
        self,
        aws_settings: AWSSettings,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        translation_callbacks: Optional[TranslationCallbacks] = None,
        segmentation_settings: Optional[SegmentationSettings] = None,
    ):
        """Initializes the AWSTranslator instance.

        Args:
            aws_settings (AWSSettings): Configuration settings for AWS services.
            input_settings (InputSettings): Input settings for the translator.
            output_settings (OutputSettings): Output settings for the translator.
            translation_callbacks (TranslationCallbacks, optional): Callbacks for the translated text.
            segmentation_settings (SegmentationSettings, optional): Segmentation and backlog control settings.
        """
        self._aws_settings = aws_settings
        self._input_settings = input_settings
        self._output_settings = output_settings
        self._translation_callbacks = translation_callbacks

        # Setup AWS services
        region = self._aws_settings.region
        self._transcribe_client = TranscribeStreamingClient(region=region)
        self._polly = boto3.client('polly', region_name=region)
        self._translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)

        # Create a shared executor for all AWS operations to limit thread overhead
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='AWSWorker')

        # self._output: Optional[Callable[]] = None
        self._language_to_output: Dict[str, SoundOutput] = {}
        self._transcription_stream: Optional[StartStreamTranscriptionEventStream] = None
        self._write_chunks_task: Optional[asyncio.Task[None]] = None
        self._handler_task: Optional[asyncio.Task[None]] = None

        # Segmentation, ordered per-language output and backlog control.
        self._pipeline = SegmentPipeline(
            settings=segmentation_settings or SegmentationSettings(),
            target_languages=aws_settings.target_languages,
            speak=lambda text, language: self._translate_and_tts(text, language),
            translation_callbacks=translation_callbacks,
        )

        LOGGER.debug('AWS Translator initialized')

    async def start_translation(
        self,
        language_to_output: Dict[str, SoundOutput],
        mic_stream: AsyncGenerator[bytes, None],
        shutdown_event: asyncio.Event,
    ):
        self._language_to_output = language_to_output

        try:
            self._transcription_stream = await self._transcribe_client.start_stream_transcription(
                language_code=self._aws_settings.source_language,
                media_sample_rate_hz=self._input_settings.input_sample_rate,
                media_encoding='pcm',
                # Less revision of already transcribed words in partial results.
                enable_partial_results_stabilization=True,
                partial_results_stability='high',
            )

            self._pipeline.start()
            handler = TranscriptEventHandler(self._transcription_stream.output_stream, self._pipeline)

            LOGGER.info('AWS Translator started.')

            # Create tasks for the two coroutines
            self._write_chunks_task = asyncio.create_task(self._write_chunks(mic_stream))
            self._handler_task = asyncio.create_task(handler.handle_events())
            shutdown_wait_task = asyncio.create_task(shutdown_event.wait())

            _done, pending = await asyncio.wait(
                [self._write_chunks_task, self._handler_task, shutdown_wait_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cleanup pending local tasks.
            # We cancel the audio writing immediately, but we might want to let the handler
            # continue if we are shutting down gracefully.
            for task in pending:
                if task is not self._handler_task:
                    task.cancel()

            LOGGER.debug('Exit condition met in start_translation.')

        except asyncio.CancelledError:
            LOGGER.debug('Translation process was cancelled.')
        except Exception as e:
            LOGGER.error(f'An unexpected error occurred during translation: {e}', exc_info=True)
        finally:
            if self._transcription_stream and self._transcription_stream.input_stream:
                try:
                    LOGGER.debug('Ending transcription stream gracefully.')
                    await self._transcription_stream.input_stream.end_stream()
                except Exception as e:
                    LOGGER.warning(f'Failed to end transcription stream gracefully: {e}')

            # Give the handler task a small moment to process final events before hard cancellation
            if self._handler_task and not self._handler_task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(self._handler_task), timeout=2.0)
                except asyncio.TimeoutError, asyncio.CancelledError:
                    LOGGER.debug('Forcing cancellation of handler task.')
                    self._handler_task.cancel()

            await self._pipeline.stop(drain_timeout=_SHUTDOWN_DRAIN_TIMEOUT_S)
            self._executor.shutdown(wait=False)
            LOGGER.debug('AWS Translator shutdown complete.')

    async def _write_chunks(self, mic_stream: AsyncGenerator[bytes, None]):
        if self._transcription_stream is None:
            return
        async for chunk in mic_stream:
            await self._transcription_stream.input_stream.send_audio_event(audio_chunk=chunk)

    async def _translate_and_tts(self, transcript: str, language: str):
        """Translates the transcript and performs TTS."""
        loop = asyncio.get_running_loop()
        trans_result = await loop.run_in_executor(
            self._executor,
            lambda: self._translate.translate_text(
                Text=transcript,
                SourceLanguageCode=self._aws_settings.source_language,
                TargetLanguageCode=language,
            ),
        )
        translated_text = trans_result.get('TranslatedText')
        if not translated_text:
            LOGGER.warning(f'AWS Translate returned empty translation for language: {language}')
            return

        if self._translation_callbacks is not None:
            self._translation_callbacks.update_target_field(language, translated_text)

        await self._aws_polly_tts(translated_text, language)
        LOGGER.debug(f'Translation and TTS processed for language: {language}')

    async def _aws_polly_tts(self, text: str, language: str):
        """Converts text to speech using AWS Polly and plays it."""
        LOGGER.debug(f"Synthesizing speech for text: '{text[:50]}...' in language: {language}")

        try:
            speaking_rate = self._pipeline.speaking_rate_for(language)
            try:
                pcm = await self._synthesize(text, language, speaking_rate)
            except ClientError as e:
                if speaking_rate == 1.0:
                    raise
                LOGGER.warning(f'Polly rejected speaking rate ({e}); disabling rate control for {language}.')
                self._pipeline.disable_speaking_rate(language)
                speaking_rate = 1.0
                pcm = await self._synthesize(text, language, speaking_rate)

            # Polly returns signed 16-bit little endian mono PCM.
            sample_rate = self._output_settings.output_sample_rate
            pcm = trim_silence(pcm, sample_rate, tail_s=tail_pause_seconds(text, speaking_rate))
            if not pcm:
                LOGGER.debug(f'Polly returned no audible audio for {language}, skipping playback.')
                return

            self._pipeline.register_playout(language, pcm_duration_seconds(pcm, sample_rate))
            LOGGER.debug(f'Received audio stream from Polly for language: {language}.')
            await self._language_to_output[language].play(io.BytesIO(pcm))
            LOGGER.debug(f'Audio playback initiated for language: {language}.')
        except Exception as e:
            LOGGER.error(f'Error during Polly TTS or playback for language {language}: {e}', exc_info=True)

    async def _synthesize(self, text: str, language: str, speaking_rate: float) -> bytes:
        """Synthesizes ``text`` with Polly; uses SSML prosody only if the rate differs from normal."""
        language_settings = self._aws_settings.target_languages[language]
        request = {
            'Engine': language_settings.engine,
            'LanguageCode': language,
            'Text': text,
            'VoiceId': language_settings.voice_id,
            'SampleRate': str(self._output_settings.output_sample_rate),
            'OutputFormat': 'pcm',
        }
        if speaking_rate != 1.0:
            request['Text'] = self._to_ssml(text, speaking_rate)
            request['TextType'] = 'ssml'

        def synthesize() -> bytes:
            response = self._polly.synthesize_speech(**request)
            stream = response['AudioStream']
            try:
                return stream.read()
            finally:
                stream.close()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, synthesize)

    @staticmethod
    def _to_ssml(text: str, speaking_rate: float) -> str:
        return f'<speak><prosody rate="{round(speaking_rate * 100)}%">{escape(text)}</prosody></speak>'
