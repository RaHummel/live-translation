from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict
import logging
import asyncio
from constants import INPUT_SAMPLE_RATE


LOGGER = logging.getLogger(__name__)


class SoundInput(ABC):
    @abstractmethod
    async def get_audio_stream(self) -> AsyncGenerator[bytes, None]:
        """Gets the audio stream from the input device.

        Returns:
            AsyncGenerator[bytes, None]: An asynchronous generator yielding audio chunks.
        """
        pass


class SoundOutput(ABC):
    @abstractmethod
    async def play(self, output_bytes: bytes) -> None:
        """Plays the output audio bytes.

        Args:
            output_bytes (bytes): The audio bytes to play.
        """
        pass


class Translator(ABC):
    @abstractmethod
    async def start_translation(
            self,
            source_language: str,
            target_language_mapping: Dict[str, SoundOutput],
            sample_rate: int,
            mic_stream: AsyncGenerator[bytes, None]) -> None:
        """Starts the translation process.

                Args:
                    source_language (str): The source language code.
                    target_language:mapping Dict[str, SoundOutput]: Mapping of target language code to SoundOutput.
                    sample_rate (int): The sample rate of the audio.
                    mic_stream (AsyncGenerator[bytes, None]): An asynchronous generator yielding audio chunks.
                    output_method (Callable[[bytes], None]): A callable to handle the output audio bytes.
                """
        pass


class Translation:
    def __init__(
            self,
            config,
            translator: Translator,
            sound_input: SoundInput,
            source_language: str,
            target_language_mapping: Dict[str, SoundOutput]) -> None:
        """Initializes the Translation instance.

        Args:
            config (dict): The configuration dictionary.
            translator (Translator): The translator instance.
            sound_input (SoundInput): The sound input instance.
            sound_output (SoundOutput): The sound output instance.
            source_language (str): The source language code.
            target_language (str): The target language code.
        """

        self._config = config
        self._translator = translator
        self._sound_input = sound_input
        self._source_language = source_language
        self._target_language_mapping = target_language_mapping

    def run(self):
        """Runs the translation loop."""
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._start_translation_loop())
        except KeyboardInterrupt:
            LOGGER.info('loop stopped')
        loop.close()

    async def _start_translation_loop(self):
        LOGGER.info("Translation started")
        output_bytes = await self._translator.start_translation(
            source_language=self._source_language,
            target_language_mapping=self._target_language_mapping,
            sample_rate=INPUT_SAMPLE_RATE,
            mic_stream=self._sound_input.get_audio_stream()
        )

