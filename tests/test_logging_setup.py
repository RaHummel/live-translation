import logging
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

import main


class TestLoggingSetup(unittest.TestCase):
    def setUp(self):
        self._root_logger = logging.getLogger()
        self._original_handlers = list(self._root_logger.handlers)
        self._original_level = self._root_logger.level
        self.addCleanup(self._restore_logger)

    def _restore_logger(self):
        for handler in list(self._root_logger.handlers):
            handler.close()
            self._root_logger.removeHandler(handler)
        for handler in self._original_handlers:
            self._root_logger.addHandler(handler)
        self._root_logger.setLevel(self._original_level)

    @patch('main.ConfigManager.get_app_config_dir', return_value=Path('/tmp/live-translation-tests'))
    def test_get_log_file_path_uses_fixed_path(self, _mock_get_config_dir):
        log_file_path = main.get_log_file_path()

        self.assertEqual(log_file_path, Path('/tmp/live-translation-tests/logs/live-translation.log'))

    @patch('main.ConfigManager.get_app_config_dir', return_value=Path('/tmp/live-translation-tests'))
    def test_configure_logging_adds_stream_and_rotating_file_handler(self, _mock_get_config_dir):
        main.configure_logging(verbose=False)

        handlers = logging.getLogger().handlers
        self.assertTrue(any(type(handler) is logging.StreamHandler for handler in handlers))
        self.assertTrue(any(isinstance(handler, RotatingFileHandler) for handler in handlers))
