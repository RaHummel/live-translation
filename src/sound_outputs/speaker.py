import logging
from typing import Mapping
from translation import SoundOutput
from constants import OUTPUT_SAMPLE_RATE, CHUNK_LEN
import pyaudio


LOGGER = logging.getLogger(__name__)


class Speaker(SoundOutput):

    def __init__(self, config: dict):
        """Initializes the Speaker instance.

       Args:
           config (Dict): The configuration dictionary.
           output_device_name (Optional[str]): The name of the output device. Defaults to None.
       """
        # Initialize audio
        self.pa = pyaudio.PyAudio()

        # Setup audio output
        device_name = config['output']['speaker']['outputDevice']
        self._output_device = self._get_output_device(device_name)
        self._output_dev_index = self._output_device['index']

        LOGGER.debug('Speaker client with %s initialized', self._output_device['name'])

    def play(self, output_bytes: bytes):
        """Streams audio data to the speakers.

        Args:
            output_bytes (bytes): The audio bytes to play.
        """
        chunk_len = CHUNK_LEN
        channels = 1
        sample_rate = OUTPUT_SAMPLE_RATE

        if output_bytes:
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=self._output_dev_index
            )
            while True:
                data = output_bytes.read(chunk_len)
                stream.write(data)

                if not data:
                    output_bytes.close()
                    stream.stop_stream()
                    stream.close()
                    break

    def _get_output_device(self, device_name: str) -> Mapping:
        """Gets the output device information by name.

        Args:
            device_name (str): The name of the output device.

        Returns:
            Mapping: The output device information.

        Raises:
            ValueError: If the output device is not found.
        """
        if device_name == "default":
            return self.pa.get_default_output_device_info()
        else:
            # Find device by name
            for i in range(self.pa.get_device_count()):
                device = self.pa.get_device_info_by_index(i)
                if device['name'] == device_name:
                    return device
        raise ValueError(f"Output device '{device_name}' not found")