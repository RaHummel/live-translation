import logging
from typing import Callable, List

from PySide6.QtCore import QObject, Signal


class QTextEditLogger(logging.Handler, QObject):
    """
    A logging handler that emits log messages as Qt signals.

    This handler allows log records to be sent to Qt widgets, such as QTextEdit,
    by emitting a signal (`new_log_message`) with each formatted log entry.
    It is useful for displaying application logs in a GUI in real time.

    """

    # Define a signal that will carry the log message (as a formatted string)
    # This signal will be connected to a slot in LiveOutputDashboardWidget.
    new_log_message = Signal(str)

    def __init__(self, parent_widget=None):
        QObject.__init__(self, parent_widget)
        logging.Handler.__init__(self)
        # Following logs are too noisy
        logging.getLogger('botocore').setLevel(logging.INFO)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
        # Set up the logging handler
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.setLevel(logging.DEBUG)
        # Cache for log messages when no slot is connected
        self._cache: List[str] = []
        self._connected = False

    def emit(self, record: logging.LogRecord):  # type: ignore[override]
        """
        This method is called by the logging system for each log record.
        """
        msg = self.format(record)

        if not self._connected:
            self._cache.append(msg)
        else:
            self.new_log_message.emit(msg)

    def connect_slot(self, slot: Callable[[str], None]):
        """
        Connects a slot to the `new_log_message` signal.

        The slot will be called whenever a new log message is available.
        If there are cached log messages when connecting, they will be immediately
        emitted to the slot and the cache will be cleared.

        Args:
            slot: A callable that accepts a string (the log message).
        """
        self.new_log_message.connect(slot)
        if not self._connected:
            self._connected = True
            for msg in self._cache:
                self.new_log_message.emit(msg)
            self._cache.clear()
