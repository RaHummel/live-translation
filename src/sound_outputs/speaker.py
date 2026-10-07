import asyncio
import logging
import queue
import threading
from array import array
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, List, Mapping, Optional

import sounddevice

from config.model.config_models import OutputSettings
from translation import AudioReadableStream, SoundOutput
from utils.audio_devices import get_audio_device, list_audio_devices

LOGGER = logging.getLogger(__name__)


class SpeakerRouter:
    """Routes mono PCM streams to distinct channels of one physical output device."""

    _sample_width = 2

    def __init__(self, output_settings: OutputSettings, language_channel_mapping: Mapping[str, int]):
        self._output_settings = output_settings
        self._output_device = self._get_output_device(self._output_settings.speaker_settings.output_device_index)
        self._device_index = int(self._output_device['index'])
        self._language_channel_mapping = dict(language_channel_mapping)
        self._validate_mapping()
        self._stream_channels = max(self._language_channel_mapping.values())
        self._queues: dict[str, queue.Queue[bytes]] = {
            language: queue.Queue(maxsize=64) for language in self._language_channel_mapping
        }
        self._pending: dict[str, bytearray] = {language: bytearray() for language in self._language_channel_mapping}
        self._audio_stream: Optional[sounddevice.RawOutputStream] = None
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, min(4, len(self._language_channel_mapping))), thread_name_prefix='SpeakerAudio'
        )
        self._state_lock = threading.Lock()
        self._stopped = False

        LOGGER.debug(
            'Speaker router for device "%s" (index: %d) initialized with mapping %s.',
            self._output_device['name'],
            self._device_index,
            self._language_channel_mapping,
        )

    async def play(self, language: str, output_stream: AudioReadableStream) -> None:
        """Read one TTS stream and enqueue its mono PCM chunks for *language*."""
        if language not in self._queues:
            raise ValueError(f'No speaker channel configured for language "{language}".')
        self._ensure_audio_stream_initialized()
        loop = asyncio.get_running_loop()
        try:
            while not self._stopped:
                data = await loop.run_in_executor(
                    self._executor,
                    output_stream.read,
                    self._output_settings.chunk_len * self._sample_width,
                )
                if not data:
                    break
                await self._put_chunk(language, data)
        except asyncio.CancelledError:
            LOGGER.debug('Speaker playback for %s was cancelled.', language)
            raise
        finally:
            try:
                output_stream.close()
            except Exception:
                LOGGER.debug('Could not close completed output stream.', exc_info=True)

    def stop(self) -> None:
        """Stop the shared hardware stream. Safe to call through every channel adapter."""
        with self._state_lock:
            if self._stopped:
                return
            self._stopped = True
            if self._audio_stream is not None:
                try:
                    self._audio_stream.stop()
                    self._audio_stream.close()
                finally:
                    self._audio_stream = None
            for audio_queue in self._queues.values():
                while True:
                    try:
                        audio_queue.get_nowait()
                    except queue.Empty:
                        break
            for pending in self._pending.values():
                pending.clear()
            self._executor.shutdown(wait=False, cancel_futures=True)
            LOGGER.debug('Speaker router stopped.')

    async def _put_chunk(self, language: str, data: bytes) -> None:
        audio_queue = self._queues[language]
        while not self._stopped:
            try:
                audio_queue.put_nowait(bytes(data))
                return
            except queue.Full:
                await asyncio.sleep(0.01)

    def _ensure_audio_stream_initialized(self) -> sounddevice.RawOutputStream:
        """Lazily create and start the shared multi-channel output stream."""
        with self._state_lock:
            if self._stopped:
                raise RuntimeError('Speaker router has already been stopped.')
            if self._audio_stream is None:
                self._audio_stream = sounddevice.RawOutputStream(
                    samplerate=self._output_settings.output_sample_rate,
                    blocksize=self._output_settings.chunk_len,
                    device=self._device_index,
                    channels=self._stream_channels,
                    dtype='int16',
                    callback=self._audio_callback,
                )
                self._audio_stream.start()
                LOGGER.debug('Speaker output stream initialized and started.')
        return self._audio_stream

    def _audio_callback(self, outdata, frames: int, _time_info=None, status=None) -> None:
        if status:
            LOGGER.warning('Speaker stream status: %s', status)

        outdata[:] = b'\x00' * len(outdata)
        output_samples = memoryview(outdata).cast('h')
        bytes_needed = frames * self._sample_width
        for language, one_based_channel in self._language_channel_mapping.items():
            raw_pcm = self._take_bytes(language, bytes_needed)
            samples = array('h')
            samples.frombytes(raw_pcm[: len(raw_pcm) - (len(raw_pcm) % self._sample_width)])
            channel_index = one_based_channel - 1
            for frame_index, sample in enumerate(samples):
                output_samples[frame_index * self._stream_channels + channel_index] = sample

    def _take_bytes(self, language: str, count: int) -> bytes:
        pending = self._pending[language]
        audio_queue = self._queues[language]
        while len(pending) < count:
            try:
                pending.extend(audio_queue.get_nowait())
            except queue.Empty:
                break

        result = bytes(pending[:count])
        del pending[:count]
        return result

    def _validate_mapping(self) -> None:
        if not self._language_channel_mapping:
            raise ValueError('Speaker output requires at least one language channel mapping.')
        channels = list(self._language_channel_mapping.values())
        if any(not isinstance(channel, int) or isinstance(channel, bool) or channel < 1 for channel in channels):
            raise ValueError('Speaker output channel numbers must be positive integers.')
        if len(set(channels)) != len(channels):
            raise ValueError('Each speaker target language must use a different output channel.')
        max_output_channels = int(self._output_device['max_output_channels'])
        if max(channels) > max_output_channels:
            raise ValueError(
                f'Output device "{self._output_device["name"]}" supports {max_output_channels} channels, '
                f'but channel {max(channels)} is configured.'
            )

    def _get_output_device(self, device_index: Optional[int]) -> Mapping:
        """Gets the output device information by index (preferred) or name."""
        return get_audio_device(device_index, 'output')


class Speaker(SoundOutput):
    """Language-specific adapter backed by a shared :class:`SpeakerRouter`."""

    def __init__(
        self,
        output_settings: OutputSettings,
        language: str = '__default__',
        router: Optional[SpeakerRouter] = None,
    ):
        self._language = language
        channel = output_settings.speaker_settings.language_channel_mapping.get(language, 1)
        self._router = router or SpeakerRouter(output_settings, {language: channel})
        self._play_lock = asyncio.Lock()

    async def play(self, output_stream: AudioReadableStream) -> None:
        async with self._play_lock:
            await self._router.play(self._language, output_stream)

    def stop_audio_stream(self) -> None:
        self._router.stop()

    @staticmethod
    def list_output_devices() -> List[Mapping]:
        """Lists all available output devices."""
        return list_audio_devices('output')


def create_speaker_outputs(output_settings: OutputSettings, languages: Iterable[str]) -> dict[str, SoundOutput]:
    """Create one language adapter per target over a shared hardware stream."""
    target_languages = list(languages)
    if not target_languages:
        raise ValueError('Speaker output requires at least one target language.')

    configured_mapping = output_settings.speaker_settings.language_channel_mapping
    if len(target_languages) == 1 and target_languages[0] not in configured_mapping:
        active_mapping = {target_languages[0]: 1}
    else:
        missing = [language for language in target_languages if language not in configured_mapping]
        if missing:
            raise ValueError('Missing speaker output channel mapping for: ' + ', '.join(sorted(missing)))
        active_mapping = {language: configured_mapping[language] for language in target_languages}

    router = SpeakerRouter(output_settings, active_mapping)
    return {language: Speaker(output_settings, language=language, router=router) for language in target_languages}
