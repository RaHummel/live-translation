import logging
from pymumble_py3 import Mumble
from translation import SoundOutput
from constants import CHUNK_LEN


LOGGER = logging.getLogger()


class MumbleClient(SoundOutput):
    username_postfix = 'ai_translator'

    def __init__(self, server_config: dict, language: str):
        """Initializes the MumbleClient instance.

        Args:
            server_config (Dict): The server configuration dictionary.
            language (str): The language code.
        """

        self._chunk_len = CHUNK_LEN
        self._channel_name = server_config['output']['mumble']['languageChannelMapping'][language]

        self._mumble = Mumble(
            host=server_config['output']['mumble']['ipAddress'],
            port=server_config['output']['mumble'].get('port', 64738),
            user=language + '_' + MumbleClient.username_postfix,
            password=server_config.get('password', ''),
            reconnect=True)

    def connect(self):
        """Connects to the Mumble server and moves to the target channel"""
        LOGGER.info('Connect to Mumble server')
        self._mumble.start()
        # Wait for the connection to be established
        self._mumble.is_ready()
        self._move_to_channel()

    def disconnect(self):
        """Disconnects from the Mumble server"""
        self._mumble.stop()

    def play(self, output_bytes):
        """Streams audio data directly from output_bytes to a Mumble server.

        Args:
            output_bytes (bytes): The audio bytes to play.
        """
        LOGGER.debug("Streaming to Mumble started...")

        try:
            # Read data from output_bytes and send it to the Mumble stream
            while True:
                data = output_bytes.read(self._chunk_len)
                if not data:
                    break  # End of data

                self._mumble.sound_output.add_sound(data)
        finally:
            LOGGER.debug("Streaming completed.")

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