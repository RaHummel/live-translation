import asyncio  # New import
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Mapping, Optional

import pyaudio
from botocore.response import StreamingBody

from config.model.config_models import OutputSettings
from translation import SoundOutput

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
        self._is_playing: bool = False  # New flag to track playing state
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='SpeakerAudio')  # For blocking I/O

        # Setup audio output
        self._output_device = self._get_output_device(self._output_settings.speaker_settings.output_device_index)
        self._device_index = self._output_device['index']

        if self._output_device['maxOutputChannels'] < 1:
            LOGGER.error(f'Output device: {self._output_device["name"]} has 0 output channels. Not supported.')
            raise ValueError('Output device channels must be greater than 0.')

        LOGGER.debug(
            'Speaker client for device "%s" (index: %d) initialized.', self._output_device['name'], self._device_index
        )

    async def play(self, output_stream: StreamingBody):
        """
        Asynchronously streams audio data from a StreamingBody to the speakers.
        Uses a ThreadPoolExecutor to handle blocking I/O from the StreamingBody and PyAudio.

        Args:
            output_stream (StreamingBody): The audio stream to play (e.g., from AWS Polly).
        """
        if self._is_playing:
            LOGGER.warning('Speaker is already playing audio. Skipping new request.')
            return

        self._is_playing = True

        # Open the PyAudio stream. This is a synchronous call.
        try:
            self._audio_stream = self._pa.open(
                format=pyaudio.paInt16,
                rate=self._output_settings.output_sample_rate,
                channels=1,
                output=True,
                output_device_index=self._device_index,
                frames_per_buffer=self._output_settings.chunk_len,
            )

            self._audio_stream.start_stream()
            LOGGER.debug('PyAudio speaker stream started.')

            loop = asyncio.get_running_loop()

            # Use run_in_executor for the blocking read/write operations
            await loop.run_in_executor(self._executor, self._play_blocking, output_stream, self._audio_stream)

        except asyncio.CancelledError:
            LOGGER.debug('Audio playback task was cancelled.')
        except Exception as e:
            LOGGER.error(f'Error during audio playback: {e}', exc_info=True)
        finally:
            self._is_playing = False
            if self._audio_stream:
                if self._audio_stream.is_active():
                    self._audio_stream.stop_stream()
                    LOGGER.debug('PyAudio stream stopped gracefully.')
                self._audio_stream.close()
                LOGGER.debug('PyAudio stream closed.')

            # The StreamingBody should also be closed, ideally by the caller or here as a fallback
            if output_stream and hasattr(output_stream, 'close'):
                try:
                    output_stream.close()
                    LOGGER.debug('StreamingBody closed.')
                except Exception as e:
                    LOGGER.debug(f'Failed to close StreamingBody: {e}')

            LOGGER.debug('Audio playback completed or terminated.')

    def _play_blocking(self, output_stream: StreamingBody, audio_stream: pyaudio.Stream):
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
        """
        Signals the currently playing audio stream to stop.
        This is a synchronous method to be called from the main thread (e.g., UI).
        It sets a flag that the `_play_blocking` method will observe.
        """
        if self._is_playing:
            LOGGER.debug('Requesting speaker audio stream to stop.')
            self._is_playing = False  # Signal the _play_blocking loop to exit
        else:
            LOGGER.debug('No active audio stream to stop.')

        # Terminate PyAudio instance. This should ideally be done once at application shutdown.
        # Calling it here immediately stops all streams and prevents further playback.
        # Consider moving this to a dedicated `shutdown` method for the Speaker class.
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
        devices = []
        for i in range(pa.get_device_count()):
            device = pa.get_device_info_by_index(i)
            if device['maxOutputChannels'] > 0:
                devices.append({'name': device['name'], 'index': device['index']})
        pa.terminate()
        return devices
