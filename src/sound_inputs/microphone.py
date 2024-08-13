import asyncio
import pyaudio
from typing import Optional, AsyncGenerator, Mapping
from translation import SoundInput
from constants import INPUT_SAMPLE_RATE


class Microphone(SoundInput):
    def __init__(self, config: dict, input_device_name: Optional[str] = None):
        """Initializes the Microphone instance.

        Args:
            config (dict): The configuration dictionary.
            input_device_name (str, optional): The name of the input device. Defaults to None.
        """
        # Initialize audio
        self._pa = pyaudio.PyAudio()

        # Setup audio input
        device_name: str = input_device_name or config['inputDevice']
        self.input_device = self._get_input_device(device_name)
        self.input_channel_count = self.input_device['maxInputChannels']
        self.input_sample_rate = INPUT_SAMPLE_RATE
        self.input_dev_index = self.input_device['index']
        self.default_frames = int(self.input_sample_rate / 2)

    async def get_audio_stream(self) -> AsyncGenerator[bytes, None]:
        """Streams audio from the microphone to an asyncio.Queue.

        Yields:
            bytes: Audio data chunks.
        """
        loop = asyncio.get_event_loop()
        input_queue = asyncio.Queue()

        def callback(indata, frame_count, time_info, status):
            loop.call_soon_threadsafe(input_queue.put_nowait, indata)
            return indata, pyaudio.paContinue

        stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.input_channel_count,
            rate=self.input_sample_rate,
            input=True,
            frames_per_buffer=self.default_frames,
            input_device_index=self.input_dev_index,
            stream_callback=callback
        )
        stream.start_stream()

        while True:
            indata = await input_queue.get()
            yield indata

    def _get_input_device(self, device_name: str) -> Mapping:
        """Gets the input device information by name.

                Args:
                    device_name (str): The name of the input device.

                Returns:
                    Mapping: The input device information.

                Raises:
                    ValueError: If the input device is not found.
                """
        if device_name == "default":
            return self._pa.get_default_input_device_info()
        else:
            # Find device by name
            for i in range(self._pa.get_device_count()):
                device = self._pa.get_device_info_by_index(i)
                if device['name'] == device_name:
                    return device
        raise ValueError(f"Input device '{device_name}' not found")