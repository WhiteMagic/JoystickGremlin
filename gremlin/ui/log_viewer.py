# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import collections
import logging
import threading

from PySide6 import QtCore

import gremlin.ui.type_aliases as ta

QML_IMPORT_NAME = "Gremlin.Log"
QML_IMPORT_MAJOR_VERSION = 1


class LogNotifier(QtCore.QObject):
    """Bridge between the LogViewerHandler and the LogSource to work around Qt signal
    slot limitations."""

    recordAdded = QtCore.Signal(int, str, int)


class LogViewerHandler(logging.Handler):
    """Keeps the most recent formatted records of a logger in memory."""

    def __init__(self, max_records: int = 5000) -> None:
        """Creates a new handler instance.

        Args:
            max_records: number of records kept before the oldest is evicted
        """
        super().__init__()
        self._records: collections.deque[tuple[int, str]] = collections.deque(
            maxlen=max_records
        )
        self._records_lock = threading.Lock()
        self._sequence = 0
        # Must be created on the GUI thread so emits from others get queued.
        self.notifier = LogNotifier()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = self.format(record)
            with self._records_lock:
                self._sequence += 1
                sequence = self._sequence
                evicted_chars = 0
                if len(self._records) == self._records.maxlen:
                    evicted_chars = len(self._records[0][1]) + 1
                self._records.append((sequence, text))
            self.notifier.recordAdded.emit(sequence, text, evicted_chars)
        except Exception:  # noqa: BLE001
            self.handleError(record)

    def snapshot(self) -> tuple[str, int]:
        """Returns the buffered text and the sequence of its last record.

        Returns:
            Records joined by newlines and the last sequence number, 0 if empty
        """
        with self._records_lock:
            text = "\n".join(text for _, text in self._records)
            return text, self._sequence


@ta.QmlElement
class LogSource(QtCore.QObject):
    """Exposes the LogViewerHandler of a named logger to QML."""

    loggerNameChanged = QtCore.Signal()
    recordAppended = QtCore.Signal(str, int)

    def __init__(self, parent: ta.OQO = None) -> None:
        super().__init__(parent)
        self._logger_name = ""
        self._handler: LogViewerHandler | None = None
        self._snapshot_sequence = 0

    def _get_logger_name(self) -> str:
        return self._logger_name

    def _set_logger_name(self, name: str) -> None:
        if name == self._logger_name:
            return
        if self._handler is not None:
            self._handler.notifier.recordAdded.disconnect(self._on_record_added)
        self._logger_name = name
        self._handler = next(
            (
                handler
                for handler in logging.getLogger(name).handlers
                if isinstance(handler, LogViewerHandler)
            ),
            None,
        )
        if self._handler is not None:
            self._handler.notifier.recordAdded.connect(self._on_record_added)
        self.loggerNameChanged.emit()

    @QtCore.Slot(result=str)
    def snapshot(self) -> str:
        if self._handler is None:
            return ""
        text, self._snapshot_sequence = self._handler.snapshot()
        return text

    def _on_record_added(self, sequence: int, text: str, evicted_chars: int) -> None:
        # Queued signals can arrive for records already contained in the snapshot.
        if sequence > self._snapshot_sequence:
            self.recordAppended.emit(text, evicted_chars)

    loggerName = QtCore.Property(
        str,
        fget=_get_logger_name,
        fset=_set_logger_name,
        notify=loggerNameChanged,
    )
