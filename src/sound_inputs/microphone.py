import asyncio
import logging
from asyncio import AbstractEventLoop, Event
from typing import AsyncGenerator, List, Mapping, Optional

import sounddevice

from config.model.config_models import InputSettings
from translation import SoundInput
from utils.audio_devices import get_audio_device, list_audio_devices

LOGGER = logging.getLogger(__name__)


class Microphone(SoundInput):
    def __init__(self, input_settings: InputSettings):
        """Initializes the Microphone instance.

        Args:
            input_settings (InputSetting): Input settings object.
        """
        self._input_settings = input_settings
        self._audio_stream: Optional[sounddevice.RawInputStream] = None
        self._loop: Optional[AbstractEventLoop] = None
        self._input_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)

        self._input_device_info = self._get_input_device(self._input_settings.input_device_index)
        if self._input_settings.input_channels > self._input_device_info['max_input_channels']:
            raise ValueError(
                f'Input device supports {self._input_device_info["max_input_channels"]} channels, '
                f'but {self._input_settings.input_channels} were requested.'
            )
        # Use ~100ms audio chunks to reduce end-of-utterance latency for streaming STT.
        self._buffer_frames = int(self._input_settings.input_sample_rate / 10)

    async def get_audio_stream(self, shutdown_event: Event) -> AsyncGenerator[bytes, None]:
        """Streams audio from the microphone to an asyncio.Queue.

        Yields:
            bytes: Audio data chunks.
        """
        self._loop = asyncio.get_running_loop()
        self._audio_stream = sounddevice.RawInputStream(
            dtype='int16',
            channels=self._input_settings.input_channels,
            samplerate=self._input_settings.input_sample_rate,
            blocksize=self._buffer_frames,
            device=self._input_device_info['index'],
            callback=self._callback,
        )

        self._audio_stream.start()

        LOGGER.debug('Audio stream started with device: %s', self._input_device_info['name'])

        try:
            while not shutdown_event.is_set():
                indata = await self._input_queue.get()
                yield indata
        except asyncio.CancelledError:
            LOGGER.debug('Audio stream cancelled.')

    def stop_audio_stream(self):
        """Stops and closes the sounddevice input stream."""

        if self._audio_stream is None:
            LOGGER.warning('Audio stream was not initialized.')
        else:
            self._audio_stream.stop()
            self._audio_stream.close()

        self._audio_stream = None
        LOGGER.debug('Microphone stream stopped.')

    def _callback(self, indata, _frames=None, _time_info=None, status=None) -> None:
        """Callback function for the audio stream.
        Args:
            indata (bytes): The audio data chunk.
        """
        if status:
            LOGGER.warning('Microphone stream status: %s', status)
        if self._loop is None:
            return

        self._loop.call_soon_threadsafe(self._enqueue_audio, bytes(indata))

    def _enqueue_audio(self, data: bytes) -> None:
        if self._input_queue.full():
            LOGGER.warning('Input audio queue is full, dropping audio chunk.')
            return
        self._input_queue.put_nowait(data)

    def _get_input_device(self, device_index: Optional[int]) -> Mapping:
        """Gets the input device information by index (preferred) or name.

        Args:
            device_name (Optional[str]): The name of the input device.
            device_index (Optional[int]): The index of the input device.

        Returns:
            Mapping: The input device information.
        """
        return get_audio_device(device_index, 'input')

    @staticmethod
    def list_input_devices() -> List[Mapping]:
        """Lists all available input devices.

        Returns:
            List[Mapping]: A list of input device information dictionaries.
        """
        return list_audio_devices('input')
