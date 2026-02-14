import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from botocore.response import StreamingBody
from pymumble_py3 import Mumble
from pymumble_py3.constants import PYMUMBLE_CONN_STATE_CONNECTED

from config.model.config_models import OutputSettings
from translation import SoundOutput

LOGGER = logging.getLogger(__name__)


class MumbleClient(SoundOutput):
    username_postfix = 'ai_translator'
    # Single executor for all MumbleClient instances to limit thread creation
    _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='MumbleAudio')

    def __init__(self, output_settings: OutputSettings, language: str):
        """Initializes the MumbleClient instance.

        Args:
            output_settings (OutputSettings): Output settings object.
            language (str): The language code.
        """

        self._output_settings = output_settings
        self._channel_name = self._output_settings.mumble_settings.language_channel_mapping[language]

        self._mumble = Mumble(
            host=self._output_settings.mumble_settings.ip_address,
            port=self._output_settings.mumble_settings.port,
            user=language + '_' + MumbleClient.username_postfix,
            password='',
            reconnect=True,
        )

        LOGGER.debug('Mumble client initialized')

    def connect(self):
        """Connects to the Mumble server and moves to the target channel"""
        LOGGER.info('Connect to Mumble server')
        self._mumble.start()
        # Wait for the connection to be established
        self._mumble.is_ready()

        if self._mumble.connected != PYMUMBLE_CONN_STATE_CONNECTED:
            LOGGER.error('Failed to connect to Mumble server')
            self._mumble.stop()
            raise ConnectionError(
                """Could not connect to Mumble server at {self._output_settings.mumble_settings.ip_address}:
                {self._output_settings.mumble_settings.port}. Please check your configuration and ensure 
                the server is reachable.
                """
            )

        LOGGER.debug('Mumble client connected and ready')
        self._move_to_channel()

    def stop_audio_stream(self):
        """Disconnects from the Mumble server"""
        self._mumble.stop()

    async def play(self, output_bytes: StreamingBody):
        """Streams audio data asynchronously directly from output_bytes to a Mumble server.

        Args:
            output_bytes (StreamingBody): The audio stream to play.
        """
        LOGGER.debug('Streaming to Mumble started...')

        loop = asyncio.get_running_loop()

        try:
            # Read data from output_bytes and send it to the Mumble stream
            while True:
                data = await loop.run_in_executor(
                    MumbleClient._executor, output_bytes.read, self._output_settings.chunk_len
                )

                if not data:
                    break  # End of data

                if self._mumble.sound_output is None:
                    LOGGER.warning('Mumble sound_output not initialized yet. Skipping chunk.')
                    continue

                self._mumble.sound_output.add_sound(data)
        except asyncio.CancelledError:
            LOGGER.debug('Mumble playback task was cancelled.')
        except Exception as e:
            LOGGER.error(f'Error during Mumble playback: {e}', exc_info=True)
        finally:
            LOGGER.debug('Streaming completed.')

    def _move_to_channel(self):
        """Moves to the specified channel."""

        LOGGER.debug(f'Move to channel {self._channel_name}')
        # Split the channel path
        channel_path = self._channel_name.split('/')

        if len(channel_path) > 2:
            raise ValueError('Invalid channel path. Only one subchannel is supported')

        channel = None

        if len(channel_path) == 1:
            main_channel_name = channel_path[0]
            channel = self._mumble.channels.find_by_name(main_channel_name)

        else:
            channel = self._mumble.channels.find_by_tree([channel_name for channel_name in channel_path])

        # Now move to the channel
        channel.move_in()
