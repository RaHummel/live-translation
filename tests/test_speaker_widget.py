import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QComboBox

from config.model.config_models import SpeakerSettings
from gui_elements.speaker_widget import SpeakerWidget


class TestSpeakerWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch(
        'gui_elements.speaker_widget.Speaker.list_output_devices',
        return_value=[{'name': 'Interface', 'index': 7, 'max_output_channels': 4}],
    )
    def test_assigns_and_returns_distinct_default_channels(self, _mock_devices):
        widget = SpeakerWidget(SpeakerSettings('Interface', 7))
        self.addCleanup(widget.deleteLater)

        widget.set_target_languages({'de-DE', 'en-US'})
        mapping = widget.get_channel_mapping()

        self.assertEqual(set(mapping), {'de-DE', 'en-US'})
        self.assertEqual(set(mapping.values()), {1, 2})
        self.assertEqual(widget.channel_mapping_table.rowCount(), 2)

    @patch(
        'gui_elements.speaker_widget.Speaker.list_output_devices',
        return_value=[{'name': 'Interface', 'index': 7, 'max_output_channels': 4}],
    )
    def test_preserves_loaded_channel_mapping(self, _mock_devices):
        widget = SpeakerWidget(SpeakerSettings('Interface', 7, {'de-DE': 3}))
        self.addCleanup(widget.deleteLater)

        widget.set_target_languages({'de-DE'})

        channel_combo = widget.channel_mapping_table.cellWidget(0, 1)
        self.assertIsInstance(channel_combo, QComboBox)
        self.assertEqual(channel_combo.currentData(), 3)
