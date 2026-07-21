"""Shared helper for the common "move a worker QObject to a QThread and run it" pattern.

Several parts of the app (Mumble server start, Mumble install, Windows
Firewall setup, …) spin up a background `QThread`, move a worker onto it,
wire up `started`/`finished` signals and clean everything up again once the
worker is done. This little helper centralizes that boilerplate.
"""

from PySide6.QtCore import QObject, QThread, SignalInstance


def run_in_thread(
    parent: QObject,
    worker: QObject,
    run_method,
    finished_signal: SignalInstance,
    on_finished=None,
) -> QThread:
    """Move *worker* to a new `QThread`, wire it up, and start it.

    Args:
        parent: Parent for the new `QThread` (keeps it alive as long as needed).
        worker: The worker `QObject` to run in the background thread.
        run_method: The worker's bound method to invoke once the thread starts
            (e.g. `worker.run`).
        finished_signal: The worker's "done" signal (e.g. `worker.finished`).
            Used to trigger cleanup (`thread.quit`, `worker.deleteLater`) and,
            if given, *on_finished*.
        on_finished: Optional slot connected to *finished_signal*, called with
            whatever arguments the signal carries.

    Returns:
        The started `QThread` (caller only needs this if it wants to keep a
        reference, e.g. to avoid premature garbage collection).
    """
    thread = QThread(parent)
    worker.moveToThread(thread)

    thread.started.connect(run_method)
    if on_finished is not None:
        finished_signal.connect(on_finished)
    finished_signal.connect(thread.quit)
    finished_signal.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()
    return thread
