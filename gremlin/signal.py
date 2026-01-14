# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from PySide6 import QtCore

from gremlin import common


@common.SingletonDecorator
class Signal(QtCore.QObject):

    reloadUi = QtCore.Signal()

    reloadCurrentInputItem = QtCore.Signal()

    inputItemChanged = QtCore.Signal(int)

    modesChanged = QtCore.Signal()

    profileChanged = QtCore.Signal()

    logicalDeviceModified = QtCore.Signal()

    configChanged = QtCore.Signal()


signal = Signal()
