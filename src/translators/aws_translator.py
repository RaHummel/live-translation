import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Awaitable, Callable, Dict, List, Optional

import boto3
from amazon_transcribe.client import StartStreamTranscriptionEventStream, TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import Result, TranscriptEvent
from botocore.response import StreamingBody

from config.model.config_models import AWSSettings, InputSettings, OutputSettings
from translation import SoundOutput, Translator
from translators.translation_callbacks import TranslationCallbacks

LOGGER = logging.getLogger(__name__)


class TranscriptEventHandler(TranscriptResultStreamHandler):
    """Handles incoming transcript events from AWS Transcribe and triggers translation + TTS."""

    def __init__(
        self,
        output_stream,
        polly_tts: Callable[[str, str], Awaitable[None]],
        aws_settings: AWSSettings,
        executor: ThreadPoolExecutor,
        translate_client,
        translation_callbacks: Optional[TranslationCallbacks] = None,
    ):
        super().__init__(output_stream)
        self._polly_tts = polly_tts
        self._aws_settings = aws_settings
        self._executor = executor
        self._translate = translate_client
        self._translation_callbacks = translation_callbacks

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results: List[Result] = transcript_event.transcript.results
        if (
            results
            and results[0].alternatives
            and hasattr(results[0], 'is_partial')
            and not results[0].is_partial
            and results[0].channel_id == 'ch_0'
        ):
            transcript = results[0].alternatives[0].transcript
            if self._translation_callbacks is not None:
                self._translation_callbacks.update_source_field(transcript)

            tasks = [
                asyncio.create_task(self._translate_and_tts(transcript, language))
                for language in self._aws_settings.target_languages
            ]
            await asyncio.gather(*tasks)

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

        if self._translation_callbacks is not None:
            self._translation_callbacks.update_target_field(language, translated_text)

        await self._polly_tts(translated_text, language)
        LOGGER.debug(f'Translation and TTS processed for language: {language}')


class AWSTranslator(Translator):
    def __init__(
        self,
        aws_settings: AWSSettings,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        translation_callbacks: Optional[TranslationCallbacks] = None,
    ):
        """Initializes the AWSTranslator instance.

        Args:
            aws_settings (AWSSettings): Configuration settings for AWS services.
            input_settings (InputSettings): Input settings for the translator.
            output_settings (OutputSettings): Output settings for the translator.
            translation_callbacks (TranslationCallbacks, optional): Callbacks for the translated text.
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
            )

            handler = TranscriptEventHandler(
                self._transcription_stream.output_stream,
                self._aws_polly_tts,
                self._aws_settings,
                self._executor,
                self._translate,
                self._translation_callbacks,
            )

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

            self._executor.shutdown(wait=False)
            LOGGER.debug('AWS Translator shutdown complete.')

    async def _write_chunks(self, mic_stream: AsyncGenerator[bytes, None]):
        if self._transcription_stream is None:
            return
        async for chunk in mic_stream:
            await self._transcription_stream.input_stream.send_audio_event(audio_chunk=chunk)

    async def _aws_polly_tts(self, text: str, language: str):
        """Converts text to speech using AWS Polly and plays it."""
        LOGGER.debug(f"Synthesizing speech for text: '{text[:50]}...' in language: {language}")

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                self._executor,
                lambda: self._polly.synthesize_speech(
                    Engine=self._aws_settings.target_languages[language].engine,
                    LanguageCode=language,
                    Text=text,
                    VoiceId=self._aws_settings.target_languages[language].voice_id,
                    SampleRate=str(self._output_settings.output_sample_rate),
                    OutputFormat='pcm',
                ),
            )

            output_bytes: StreamingBody = response['AudioStream']
            LOGGER.debug(f'Received audio stream from Polly for language: {language}.')
            await self._language_to_output[language].play(output_bytes)
            LOGGER.debug(f'Audio playback initiated for language: {language}.')
        except Exception as e:
            LOGGER.error(f'Error during Polly TTS or playback for language {language}: {e}', exc_info=True)
