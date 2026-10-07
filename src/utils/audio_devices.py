import logging
from typing import Literal, Mapping

import sounddevice

LOGGER = logging.getLogger(__name__)

DeviceKind = Literal['input', 'output']


def _channel_key(kind: DeviceKind) -> str:
    return f'max_{kind}_channels'


def get_audio_device(device_index: int | None, kind: DeviceKind) -> Mapping:
    """Resolve a configured device index, falling back to the system default."""
    channel_key = _channel_key(kind)
    if device_index is not None:
        try:
            device = dict(sounddevice.query_devices(device_index, kind))
            if int(device[channel_key]) > 0:
                device['index'] = device_index
                return device
        except ValueError, PortAudioError:
            LOGGER.warning('%s device with index %s not found. Falling back to default.', kind.title(), device_index)

    default_devices = sounddevice.default.device
    default_index = default_devices[0 if kind == 'input' else 1]
    if default_index is None or int(default_index) < 0:
        raise ValueError(f'No default {kind} audio device is available.')

    device = dict(sounddevice.query_devices(int(default_index), kind))
    if int(device[channel_key]) < 1:
        raise ValueError(f'Default {kind} audio device has no {kind} channels.')
    device['index'] = int(default_index)
    return device


def list_audio_devices(kind: DeviceKind) -> list[Mapping]:
    """Return devices supporting *kind*, including channel and host API metadata."""
    channel_key = _channel_key(kind)
    host_apis = sounddevice.query_hostapis()
    devices: list[Mapping] = []

    for index, raw_device in enumerate(sounddevice.query_devices()):
        device = dict(raw_device)
        channels = int(device.get(channel_key, 0))
        if channels < 1:
            continue

        host_api_name = None
        host_api_index = device.get('hostapi')
        if isinstance(host_api_index, int) and 0 <= host_api_index < len(host_apis):
            host_api_name = host_apis[host_api_index].get('name')

        devices.append(
            {
                'name': device['name'],
                'index': index,
                channel_key: channels,
                'host_api_name': host_api_name,
            }
        )

    return devices


PortAudioError = sounddevice.PortAudioError
