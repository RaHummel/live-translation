import asyncio  # New import
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Mapping, Optional

import pyaudio

from config.model.config_models import OutputSettings
from translation import AudioReadableStream, SoundOutput

LOGGER = logging.getLogger(__name__)


class Speaker(SoundOutput):
    def __init__(self, output_settings: OutputSettings):
        """Initializes the Speaker instance.

        Args:
            output_settings (OutputSettings): Output settings object.
        """
        self._pa = pyaudio.PyAudio()
        self._output_settings = output_settings
        self._audio_stream: Optional[pyaudio.Stream] = None
        self._is_playing: bool = False
        self._stream_initialized: bool = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='SpeakerAudio')

        self._queue: asyncio.Queue[AudioReadableStream] = asyncio.Queue()
        self._consumer_task: Optional[asyncio.Task] = None

        # Setup audio output
        self._output_device = self._get_output_device(self._output_settings.speaker_settings.output_device_index)
        self._device_index = self._output_device['index']

        if self._output_device['maxOutputChannels'] < 1:
            LOGGER.error(f'Output device: {self._output_device["name"]} has 0 output channels. Not supported.')
            raise ValueError('Output device channels must be greater than 0.')

        LOGGER.debug(
            'Speaker client for device "%s" (index: %d) initialized.', self._output_device['name'], self._device_index
        )

    def _ensure_audio_stream_initialized(self) -> pyaudio.Stream:
        """Lazily creates and starts a persistent PyAudio output stream on first use."""
        if self._audio_stream is None or not self._stream_initialized:
            self._audio_stream = self._pa.open(
                format=pyaudio.paInt16,
                rate=self._output_settings.output_sample_rate,
                channels=1,
                output=True,
                output_device_index=self._device_index,
                frames_per_buffer=self._output_settings.chunk_len,
            )
            self._audio_stream.start_stream()
            self._stream_initialized = True
            LOGGER.debug('PyAudio speaker stream initialized and started.')
        elif not self._audio_stream.is_active():
            self._audio_stream.start_stream()
            LOGGER.debug('PyAudio speaker stream restarted.')

        return self._audio_stream

    async def play(self, output_stream: AudioReadableStream):
        """Enqueues audio for sequential playback. Starts the consumer task on first call."""
        await self._queue.put(output_stream)
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = asyncio.create_task(self._consume_queue())

    async def _consume_queue(self):
        """Sequentially plays all queued audio streams."""
        audio_stream = self._ensure_audio_stream_initialized()
        while not self._queue.empty():
            output_stream = await self._queue.get()
            self._is_playing = True
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self._executor, self._play_blocking, output_stream, audio_stream)
            except asyncio.CancelledError:
                LOGGER.debug('Audio playback task was cancelled.')
                break
            except Exception as e:
                LOGGER.error(f'Error during audio playback: {e}', exc_info=True)
            finally:
                self._is_playing = False
                self._queue.task_done()
                LOGGER.debug('Audio playback completed or terminated.')

    def _play_blocking(self, output_stream: AudioReadableStream, audio_stream: pyaudio.Stream):
        """
        Synchronous helper method to read from StreamingBody and write to PyAudio stream.
        This runs in a separate thread via ThreadPoolExecutor.
        """
        LOGGER.debug('Blocking audio playback started in executor thread.')
        try:
            while audio_stream.is_active() and self._is_playing:  # Check both PyAudio and internal flag
                data = output_stream.read(self._output_settings.chunk_len)
                if not data:
                    LOGGER.debug('End of audio data from StreamingBody detected.')
                    break  # No more data to read

                audio_stream.write(data)

        except Exception as e:
            LOGGER.error(f'Error in blocking audio playback loop: {e}', exc_info=True)
        finally:
            LOGGER.debug('Blocking audio playback loop finished.')
            # Note: Do not close streams here, let the async `play` method handle it for consistency.

    def stop_audio_stream(self):
        """Signals the currently playing audio stream to stop and clears the queue."""
        # Clear pending queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break

        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
            self._consumer_task = None

        if self._is_playing:
            LOGGER.debug('Requesting speaker audio stream to stop.')
            self._is_playing = False
        else:
            LOGGER.debug('No active audio stream to stop.')

        # Close the persistent PyAudio stream only at final stop
        if self._audio_stream and self._stream_initialized:
            try:
                if self._audio_stream.is_active():
                    self._audio_stream.stop_stream()
                    LOGGER.debug('PyAudio stream stopped.')
                self._audio_stream.close()
                self._audio_stream = None
                self._stream_initialized = False
                LOGGER.debug('PyAudio stream closed and cleaned up.')
            except Exception as e:
                LOGGER.error(f'Error closing PyAudio stream: {e}', exc_info=True)

        if self._pa:
            self._pa.terminate()
            LOGGER.debug('PyAudio instance terminated.')

    def _get_output_device(self, device_index: Optional[int]) -> Mapping:
        """Gets the output device information by index (preferred) or name."""
        if device_index is not None:
            try:
                device = self._pa.get_device_info_by_index(device_index)
                if device['maxOutputChannels'] > 0:
                    return device
            except Exception:
                LOGGER.warning(f'Output device with index {device_index} not found. Falling back to name/default.')

        return self._pa.get_default_output_device_info()

    @staticmethod
    def list_output_devices() -> List[Mapping]:
        """Lists all available output devices."""
        pa = pyaudio.PyAudio()
        devices: List[Mapping] = []
        for i in range(pa.get_device_count()):
            device = pa.get_device_info_by_index(i)
            if device['maxOutputChannels'] > 0:
                devices.append({'name': device['name'], 'index': device['index']})
        pa.terminate()
        return devices
