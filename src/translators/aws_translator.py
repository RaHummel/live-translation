from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import boto3
import asyncio
from translation import Translator
from constants import OUTPUT_SAMPLE_RATE
from amazon_transcribe.client import TranscribeStreamingClient, StartStreamTranscriptionEventStream
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent


class AWSTranslator(Translator):
    def __init__(self, config: dict):
        self._config = config
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Setup AWS services
        region: str = self._config['translator']['aws']['region']
        self._transcribe_client = TranscribeStreamingClient(region=region)
        self._polly = boto3.client('polly', region_name=region)
        self.translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)

        self.source_language: Optional[str] = None
        self.target_language: Optional[str] = None
        self._output: callable = None

    async def start_translation(
            self,
            source_language: str,
            target_language: str,
            sample_rate: int,
            mic_stream,
            output_method: callable):
        self.source_language = self._config['translator']['aws']['source_language'][source_language]
        self.target_language = self._config['translator']['aws']['target_language'][target_language]
        self._output = output_method

        transcription_stream = await self._transcribe_client.start_stream_transcription(
            language_code=self.source_language,
            media_sample_rate_hz=sample_rate,
            media_encoding="pcm"
        )

        handler = self.MyEventHandler(transcription_stream.output_stream,  self)
        await asyncio.gather(self._write_chunks(transcription_stream, mic_stream), handler.handle_events())

    async def _write_chunks(self, stream: StartStreamTranscriptionEventStream, mic_stream):
        async for chunk in mic_stream:
            await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()

    def aws_polly_tts(self, text: str):
        """Converts text to speech using AWS Polly."""
        response = self._polly.synthesize_speech(
            Engine='standard',
            LanguageCode=self.target_language['language_code'],
            Text=text,
            VoiceId=self.target_language['voice_id'],
            SampleRate=str(OUTPUT_SAMPLE_RATE),
            OutputFormat="pcm"
        )

        output_bytes = response['AudioStream']

        if self._output is not None:
            self._output(output_bytes)

    class MyEventHandler(TranscriptResultStreamHandler):
        def __init__(self, output_stream, transcription_service, ):
            super().__init__(output_stream)
            self._transcription_service = transcription_service
            self._source_language = self._transcription_service.source_language
            self._target_language = self._transcription_service.target_language

        async def handle_transcript_event(self, transcript_event: TranscriptEvent):
            results = transcript_event.transcript.results

            if len(results) > 0 and len(results[0].alternatives) > 0:
                transcript = results[0].alternatives[0].transcript
                print("transcript:", transcript)

                if hasattr(results[0], "is_partial") and not results[0].is_partial:
                    if results[0].channel_id == "ch_0":
                        trans_result = self._transcription_service.translate.translate_text(
                            Text=transcript,
                            SourceLanguageCode=self._source_language,
                            TargetLanguageCode=self._target_language['language_code']
                        )
                        translated_text = trans_result.get("TranslatedText")
                        print("translated text:", translated_text)
                        await asyncio.get_event_loop().run_in_executor(
                            self._transcription_service.executor,
                            self._transcription_service.aws_polly_tts,
                            translated_text
                        )

