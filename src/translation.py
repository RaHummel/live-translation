import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from typing import AsyncGenerator, Dict, Optional, Protocol

LOGGER = logging.getLogger(__name__)


class AudioReadableStream(Protocol):
    def read(self, amt: Optional[int] = None) -> bytes:
        """Reads up to amt bytes from an audio stream-like source."""

    def close(self) -> None:
        """Closes the stream and frees related resources."""


class SoundInput(ABC):
    @abstractmethod
    def get_audio_stream(self, shutdown_event: asyncio.Event) -> AsyncGenerator[bytes, None]:
        """Gets the audio stream from the input device.

        Args:
            shutdown_event (asyncio.Event): An event to signal shutdown.
        Returns:
            AsyncGenerator[bytes, None]: An asynchronous generator yielding audio chunks.
        """
        pass

    @abstractmethod
    def stop_audio_stream(self):
        """Stops the audio stream and cleans up resources."""
        pass


class SoundOutput(ABC):
    @abstractmethod
    async def play(self, output_bytes: AudioReadableStream) -> None:
        """Plays the output audio bytes.

        Args:
            output_bytes (AudioReadableStream): The audio stream to play.
        """
        pass

    @abstractmethod
    def stop_audio_stream(self) -> None:
        """Stops the audio stream and cleans up resources."""
        pass


class Translator(ABC):
    @abstractmethod
    async def start_translation(
        self,
        language_to_output: Dict[str, SoundOutput],
        mic_stream: AsyncGenerator[bytes, None],
        shutdown_event: asyncio.Event,
    ) -> None:
        """Starts the translation process.

        Args:
            language_to_output: Dict[str, SoundOutput]: Mapping of target language code to SoundOutput.
            mic_stream (AsyncGenerator[bytes, None]): An asynchronous generator yielding audio chunks.
            shutdown_event (asyncio.Event): An event to signal shutdown.
        """
        pass


class Translation:
    timeout: float = 5.0  # Timeout for stopping the translation process

    def __init__(
        self, translator: Translator, sound_input: SoundInput, target_language_mapping: Dict[str, SoundOutput]
    ) -> None:
        """Initializes the Translation instance."""
        self._translator = translator
        self._sound_input = sound_input
        self._target_language_mapping = target_language_mapping

        self._loop: Optional[AbstractEventLoop] = None
        self._main_task: Optional[asyncio.Task] = None
        self._shutdown_event: asyncio.Event = asyncio.Event()

    def run(self):
        """Starts the translation process in a new asyncio event loop running in a background thread."""
        LOGGER.debug('Starting a new asyncio event loop in a background thread.')
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._shutdown_event.clear()

        try:
            self._loop.run_until_complete(self._run_translation())
        except Exception as e:
            LOGGER.error(f'Translation loop encountered an error: {e}', exc_info=True)
        finally:
            LOGGER.debug('Asyncio event loop is shutting down.')
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            LOGGER.debug('Asyncio event loop closed.')

    def stop(self):
        """
        Stops the translation process.
        This method is called from the main GUI thread and must be thread-safe.
        """
        LOGGER.info('Stopping the translation process...')
        if self._loop and self._loop.is_running():
            self._shutdown_event.set()
            LOGGER.debug('Cancellation scheduled for the main task.')

            future = asyncio.run_coroutine_threadsafe(self._wait_for_main_task(Translation.timeout), self._loop)
            try:
                future.result(Translation.timeout + 1)
            except Exception as e:
                LOGGER.warning(f'Exception while waiting for main task: {e}')
        else:
            LOGGER.warning('Cannot stop translation: Loop is not running.')

    async def _run_translation(self):
        """Single async entry point: runs the full translation pipeline and cleans up on exit."""
        self._main_task = asyncio.current_task()
        LOGGER.info('Translation process started.')
        try:
            await self._translator.start_translation(
                language_to_output=self._target_language_mapping,
                mic_stream=self._sound_input.get_audio_stream(self._shutdown_event),
                shutdown_event=self._shutdown_event,
            )
            LOGGER.info('Translation process completed successfully.')
        except asyncio.CancelledError:
            LOGGER.debug('Main translation task was cancelled.')
        finally:
            self._clean_up()

    async def _wait_for_main_task(self, timeout: float):
        if self._main_task and not self._main_task.done():
            try:
                await asyncio.wait_for(self._main_task, timeout=timeout)
                LOGGER.debug('Main task finished gracefully.')
            except asyncio.TimeoutError:
                LOGGER.warning('Main task did not finish in time, cancelling...')
                self._main_task.cancel()
                try:
                    await self._main_task
                except asyncio.CancelledError:
                    LOGGER.debug('Main task was force-cancelled.')

    def _clean_up(self):
        """Performs all the necessary cleanup actions. Ensures resources are closed gracefully."""
        LOGGER.debug('Cleaning up all components...')
        self._sound_input.stop_audio_stream()
        for output in self._target_language_mapping.values():
            output.stop_audio_stream()

        LOGGER.debug('All components have been cleaned up.')
