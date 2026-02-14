import asyncio
import contextlib
import logging
from asyncio import AbstractEventLoop, Event
from typing import AsyncGenerator, List, Mapping, Optional, Tuple

import pyaudio
from pyaudio import Stream

from config.model.config_models import InputSettings
from constants import HOST_API_NAMES
from translation import SoundInput

LOGGER = logging.getLogger(__name__)


class Microphone(SoundInput):
    def __init__(self, input_settings: InputSettings):
        """Initializes the Microphone instance.

        Args:
            input_settings (InputSetting): Input settings object.
        """
        # Initialize audio
        self._pa = pyaudio.PyAudio()
        self._input_settings = input_settings
        self._audio_stream: Optional[Stream] = None
        self._loop: AbstractEventLoop = None
        self._input_queue = asyncio.Queue(maxsize=100)

        self._input_device_info = self._get_input_device(self._input_settings.input_device_index)
        self._buffer_frames = int(self._input_settings.input_sample_rate / 2)

    async def get_audio_stream(self, shutdown_event: Event) -> AsyncGenerator[bytes, None]:
        """Streams audio from the microphone to an asyncio.Queue.

        Yields:
            bytes: Audio data chunks.
        """
        self._loop = asyncio.get_running_loop()
        self._audio_stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self._input_settings.input_channels,
            rate=self._input_settings.input_sample_rate,
            input=True,
            frames_per_buffer=self._buffer_frames,
            input_device_index=self._input_device_info['index'],
            stream_callback=self._callback,
        )

        self._audio_stream.start_stream()

        LOGGER.debug('Audio stream started with device: %s', self._input_device_info['name'])

        try:
            while not shutdown_event.is_set():
                indata = await self._input_queue.get()
                yield indata
        except asyncio.CancelledError:
            LOGGER.debug('Audio stream cancelled.')

    def stop_audio_stream(self):
        """Stops the audio stream and closes the PyAudio instance."""

        if self._audio_stream is None:
            LOGGER.warning('Audio stream was not initialized.')
        else:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        self._pa.terminate()
        LOGGER.debug('Microphone stream stopped and PyAudio terminated.')

    def _callback(self, indata: bytes, *args, **kwargs) -> Tuple[bytes, int]:
        """Callback function for the audio stream.
        Args:
            indata (bytes): The audio data chunk.
        """
        if not self._loop or self._input_queue.full():
            return (None, pyaudio.paContinue)

        with contextlib.suppress(asyncio.QueueFull):
            self._loop.call_soon_threadsafe(self._input_queue.put_nowait, indata)

        return (None, pyaudio.paContinue)

    def _get_input_device(self, device_index: Optional[int]) -> Mapping:
        """Gets the input device information by index (preferred) or name.

        Args:
            device_name (Optional[str]): The name of the input device.
            device_index (Optional[int]): The index of the input device.

        Returns:
            Mapping: The input device information.
        """
        if device_index is not None:
            try:
                device = self._pa.get_device_info_by_index(device_index)
                if device['maxInputChannels'] > 0:
                    return device
            except Exception:
                LOGGER.warning(f'Input device with index {device_index} not found. Falling back to name/default.')

        return self._pa.get_default_input_device_info()

    @staticmethod
    def list_input_devices() -> List[Mapping]:
        """Lists all available input devices.

        Returns:
            List[Mapping]: A list of input device information dictionaries.
        """
        pa = pyaudio.PyAudio()
        devices = []
        for i in range(pa.get_device_count()):
            device = pa.get_device_info_by_index(i)
            # Only include devices with input channels and required host API
            # Note: On MacOs hostApi is not available, so we check for its presence before filtering
            if device['maxInputChannels'] > 0 and device.get('hostApi') is not None and device.get('hostApi') >= 0:
                host_api_id = device.get('hostApi')
                host_api_name = HOST_API_NAMES.get(host_api_id)
                devices.append({'name': device['name'], 'index': device['index'], 'host_api_name': host_api_name})

        pa.terminate()
        return devices
