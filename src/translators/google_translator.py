import asyncio
import io
import json
import logging
import os
import wave
from typing import AsyncGenerator, Dict, Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.cloud import speech_v2 as speech
from google.cloud import texttospeech, translate
from google.cloud.speech_v2.types import cloud_speech

from config.model.config_models import GoogleSettings, InputSettings, OutputSettings
from constants import GOOGLE_STT_REGIONS
from translation import SoundOutput, Translator
from translators.translation_callbacks import TranslationCallbacks

LOGGER = logging.getLogger(__name__)


def _resolve_project_id(credentials_path: str) -> Optional[str]:
    """Determine the Google Cloud project ID from a credentials file or application default credentials."""
    if credentials_path and os.path.exists(credentials_path):
        try:
            with open(credentials_path, 'r', encoding='utf-8') as f:
                project_id = json.load(f).get('project_id')
            if project_id:
                LOGGER.debug(f'Resolved project_id from credentials file: {project_id}')
                return project_id
        except Exception as e:
            LOGGER.debug(f'Could not read project_id from credentials file: {e}')

    try:
        import google.auth

        _, project_id = google.auth.default()
        if project_id:
            LOGGER.debug(f'Resolved project_id from google.auth: {project_id}')
        return project_id
    except Exception as e:
        LOGGER.debug(f'Could not determine project_id from google.auth: {e}')
        return None


class GoogleTranslator(Translator):
    def __init__(
        self,
        google_settings: GoogleSettings,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        translation_callbacks: Optional[TranslationCallbacks] = None,
    ):
        """Initializes the GoogleTranslator instance."""
        self._google_settings = google_settings
        self._input_settings = input_settings
        self._output_settings = output_settings
        self._translation_callbacks = translation_callbacks

        if google_settings.credentials_path and os.path.exists(google_settings.credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_settings.credentials_path
            LOGGER.debug(f'Set GOOGLE_APPLICATION_CREDENTIALS to {google_settings.credentials_path}')

        self._project_id = _resolve_project_id(google_settings.credentials_path)

        # Async clients must be created in the active translation loop.
        self._speech_client: Optional[speech.SpeechAsyncClient] = None
        self._translate_client: Optional[translate.TranslationServiceAsyncClient] = None
        self._tts_client: Optional[texttospeech.TextToSpeechAsyncClient] = None

        self._language_to_output: Dict[str, SoundOutput] = {}

        LOGGER.debug('Google Translator initialized')

    async def start_translation(
        self,
        language_to_output: Dict[str, SoundOutput],
        mic_stream: AsyncGenerator[bytes, None],
        shutdown_event: asyncio.Event,
    ):
        self._language_to_output = language_to_output

        try:
            # Chirp models require regional endpoints
            region = self._google_settings.region
            client_options = ClientOptions(api_endpoint=f'{region}-speech.googleapis.com')
            self._speech_client = speech.SpeechAsyncClient(client_options=client_options)
            self._translate_client = translate.TranslationServiceAsyncClient()
            self._tts_client = texttospeech.TextToSpeechAsyncClient()

            LOGGER.info('Google Translator started.')

            stt_task = asyncio.create_task(self._run_streaming_recognition(mic_stream, shutdown_event))
            shutdown_wait_task = asyncio.create_task(shutdown_event.wait())

            _done, pending = await asyncio.wait(
                [stt_task, shutdown_wait_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

        except asyncio.CancelledError:
            LOGGER.debug('Translation process was cancelled.')
        except Exception as e:
            LOGGER.error(f'An unexpected error occurred during Google translation: {e}', exc_info=True)
        finally:
            self._speech_client = None
            self._translate_client = None
            self._tts_client = None
            LOGGER.debug('Google Translator shutdown complete.')

    @staticmethod
    def _normalize_language_code(language_code: str) -> str:
        """Maps locale-like codes to a broadly supported base language for Google Translate."""
        return language_code.split('-')[0]

    def _get_endpointing_sensitivity(self):
        endpointing_map = {
            'standard': (
                cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_STANDARD
            ),
            'short': (cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT),
            'supershort': (
                cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SUPERSHORT
            ),
        }
        configured_value = self._google_settings.endpointing_sensitivity
        return endpointing_map.get(
            configured_value,
            cloud_speech.StreamingRecognitionFeatures.EndpointingSensitivity.ENDPOINTING_SENSITIVITY_SHORT,
        )

    async def _generator_wrapper(
        self,
        mic_stream: AsyncGenerator[bytes, None],
        shutdown_event: asyncio.Event,
        streaming_config: cloud_speech.StreamingRecognitionConfig,
    ):
        """Wraps the mic stream to yield properly formatted StreamingRecognizeRequests."""
        try:
            recognizer_path = f'projects/{self._project_id}/locations/{self._google_settings.region}/recognizers/_'
            LOGGER.debug(f'Sending first request with recognizer: {recognizer_path}')
            yield cloud_speech.StreamingRecognizeRequest(recognizer=recognizer_path, streaming_config=streaming_config)

            async for chunk in mic_stream:
                if shutdown_event.is_set():
                    LOGGER.debug('Shutdown event set, stopping request generator.')
                    break
                yield cloud_speech.StreamingRecognizeRequest(recognizer=recognizer_path, audio=chunk)
        except Exception as e:
            LOGGER.error(f'Error in Google STT request generator: {e}', exc_info=True)
        finally:
            LOGGER.debug('Google STT request generator finished.')

    async def _run_streaming_recognition(self, mic_stream: AsyncGenerator[bytes, None], shutdown_event: asyncio.Event):
        """Runs the Google Cloud Speech-to-Text streaming recognition in a continuous loop."""
        while not shutdown_event.is_set():
            try:
                if not self._project_id:
                    LOGGER.error('Google Project ID is missing. Speech V2 requires a project ID.')
                    return

                recognition_config = cloud_speech.RecognitionConfig(
                    explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                        encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=self._input_settings.input_sample_rate,
                        audio_channel_count=self._input_settings.input_channels,
                    ),
                    language_codes=[self._google_settings.source_language],
                    model=GOOGLE_STT_REGIONS.get(self._google_settings.region, 'chirp_3'),
                    features=cloud_speech.RecognitionFeatures(
                        enable_automatic_punctuation=True,
                    ),
                )

                streaming_config = cloud_speech.StreamingRecognitionConfig(
                    config=recognition_config,
                    streaming_features=cloud_speech.StreamingRecognitionFeatures(
                        interim_results=False,
                        endpointing_sensitivity=self._get_endpointing_sensitivity(),
                    ),
                )

                requests = self._generator_wrapper(mic_stream, shutdown_event, streaming_config)

                if self._speech_client is None:
                    LOGGER.error('Google Speech client is not initialized.')
                    return

                LOGGER.debug('Initiating streaming_recognize call...')
                responses = await self._speech_client.streaming_recognize(requests=requests)
                LOGGER.debug('streaming_recognize call successful, awaiting responses...')

                async for response in responses:
                    if not response.results:
                        continue

                    result = response.results[0]
                    if not result.alternatives:
                        continue

                    if result.is_final:
                        transcript = result.alternatives[0].transcript
                        LOGGER.debug(f'Final transcript received: {transcript}')
                        if self._translation_callbacks is not None:
                            self._translation_callbacks.update_source_field(transcript)

                        for language in self._google_settings.target_languages:
                            asyncio.create_task(self._translate_and_tts(transcript, language))

                        # Yield control to allow other tasks to run
                        await asyncio.sleep(0)

            except asyncio.CancelledError:
                LOGGER.debug('STT streaming task cancelled.')
                break
            except Exception as e:
                error_str = str(e)
                if 'RPC already finished' in error_str:
                    LOGGER.debug('STT stream closed by server (normal for short model), restarting...')
                elif 'Max duration' in error_str or 'ABORTED' in error_str:
                    LOGGER.debug('STT stream hit 5-minute server limit, restarting...')
                else:
                    LOGGER.error(f'Error in Google STT streaming: {e}', exc_info=True)
                await asyncio.sleep(0.1)
            finally:
                LOGGER.debug('Google STT streaming recognition stream session finished.')

    async def _translate_and_tts(self, transcript: str, language: str):
        """Translates the transcript and performs Text-to-Speech."""
        try:
            if not self._project_id:
                LOGGER.error('Google Project ID is missing. Cannot call Translate API.')
                return

            if self._translate_client is None:
                LOGGER.error('Google Translate client is not initialized.')
                return

            parent = f'projects/{self._project_id}/locations/global'

            response = await self._translate_client.translate_text(
                parent=parent,
                contents=[transcript],
                mime_type='text/plain',
                source_language_code=self._normalize_language_code(self._google_settings.source_language),
                target_language_code=self._normalize_language_code(language),
            )

            translated_text = response.translations[0].translated_text if response.translations else ''
            if not translated_text:
                LOGGER.warning(f'Google Translate returned empty translation for language: {language}')
                return

            if self._translation_callbacks is not None:
                self._translation_callbacks.update_target_field(language, translated_text)

            await self._google_tts(translated_text, language)
            LOGGER.debug(f'Translation and TTS processed for language: {language}')

        except Exception as e:
            LOGGER.error(f'Error during Google Translate/TTS for {language}: {e}')

    async def _google_tts(self, text: str, language: str):
        """Converts text to speech using Google Cloud TTS and queues playback."""
        LOGGER.debug(f"Synthesizing speech for text: '{text[:50]}...' in language: {language}")

        try:
            if self._tts_client is None:
                LOGGER.error('Google TTS client is not initialized.')
                return

            lang_settings = self._google_settings.target_languages[language]
            voice_id = lang_settings.voice_id

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(language_code=language, name=voice_id)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=self._output_settings.output_sample_rate,
            )

            response = await self._tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # LINEAR16 enthält WAV-Header → strippen, sonst Klack am Anfang
            wav_buffer = io.BytesIO(response.audio_content)
            with wave.open(wav_buffer) as wf:
                raw_pcm = wf.readframes(wf.getnframes())
            await self._language_to_output[language].play(io.BytesIO(raw_pcm))

        except GoogleAPIError as e:
            LOGGER.error(f'Google API Error in TTS for {language}: {e}')
        except Exception as e:
            LOGGER.error(f'Error during Google TTS or playback for language {language}: {e}', exc_info=True)
