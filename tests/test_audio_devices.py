import unittest
from unittest.mock import patch

from utils.audio_devices import get_audio_device, list_audio_devices


class TestAudioDevices(unittest.TestCase):
    @patch('utils.audio_devices.sounddevice')
    def test_get_configured_device(self, mock_sounddevice):
        mock_sounddevice.query_devices.return_value = {'name': 'Output', 'max_output_channels': 4}

        device = get_audio_device(3, 'output')

        mock_sounddevice.query_devices.assert_called_once_with(3, 'output')
        self.assertEqual(device['index'], 3)

    @patch('utils.audio_devices.sounddevice')
    def test_invalid_configured_device_falls_back_to_default(self, mock_sounddevice):
        mock_sounddevice.PortAudioError = RuntimeError
        mock_sounddevice.default.device = (1, 2)
        mock_sounddevice.query_devices.side_effect = [
            ValueError('missing'),
            {'name': 'Default', 'max_output_channels': 2},
        ]

        device = get_audio_device(99, 'output')

        self.assertEqual(device['index'], 2)
        self.assertEqual(device['name'], 'Default')

    @patch('utils.audio_devices.sounddevice')
    def test_list_devices_filters_direction_and_includes_host_api(self, mock_sounddevice):
        mock_sounddevice.query_devices.return_value = [
            {'name': 'Input only', 'max_output_channels': 0, 'hostapi': 0},
            {'name': 'Speaker', 'max_output_channels': 2, 'hostapi': 0},
        ]
        mock_sounddevice.query_hostapis.return_value = [{'name': 'Core Audio'}]

        devices = list_audio_devices('output')

        self.assertEqual(
            devices,
            [
                {
                    'name': 'Speaker',
                    'index': 1,
                    'max_output_channels': 2,
                    'host_api_name': 'Core Audio',
                }
            ],
        )
