import asyncio
from typing import AsyncGenerator, Dict

from botocore.response import StreamingBody

from translation import SoundInput, SoundOutput, Translator


class SoundOutputStub(SoundOutput):
    def __init__(self):
        self.play_called = False
        self.played_bytes = None
        self.stop_called = False

    async def play(self, output_bytes: StreamingBody) -> None:
        self.play_called = True
        self.played_bytes = output_bytes

    def stop_audio_stream(self) -> None:
        self.stop_called = True


class SoundInputStub(SoundInput):
    def __init__(self):
        self.stop_called = False

    async def get_audio_stream(self, shutdown_event):
        yield b'test'

    def stop_audio_stream(self):
        self.stop_called = True


class TranslatorStub(Translator):
    def __init__(self):
        self.start_translation_called = False

    async def start_translation(
        self,
        language_to_output: Dict[str, SoundOutput],
        mic_stream: AsyncGenerator[bytes, None],
        shutdown_event: asyncio.Event,
    ) -> None:
        self.start_translation_called = True
        await shutdown_event.wait()


class TranslationStub:
    def __init__(self, translator, sound_input, target_language_mapping):
        self.translator = translator
        self.sound_input = sound_input
        self.target_language_mapping = target_language_mapping
        self.run_called = False
        self.stop_called = False

    def run(self):
        self.run_called = True

    def stop(self):
        self.stop_called = True
