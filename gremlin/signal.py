# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from PySide6 import QtCore

from gremlin import common


def display_error(message: str, details: str = "") -> None:
    """Display an error message in the UI.

    Args:
        message (str): The error message to display.
    """
    signal.showError.emit(message, details)


@common.SingletonDecorator
class Signal(QtCore.QObject):

    reloadUi = QtCore.Signal()

    reloadCurrentInputItem = QtCore.Signal()

    inputItemChanged = QtCore.Signal(int)

    setInputIndex = QtCore.Signal(int)

    modesChanged = QtCore.Signal()

    profileChanged = QtCore.Signal()

    logicalDeviceModified = QtCore.Signal()

    configChanged = QtCore.Signal()

    showError = QtCore.Signal(str, str)

    showNotification = QtCore.Signal(str, str)


signal = Signal()
