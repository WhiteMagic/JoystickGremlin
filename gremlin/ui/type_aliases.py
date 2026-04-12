# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from typing import (
    cast,
    Optional,
    TypeVar,
)

from PySide6 import (
    QtCore,
    QtQml,
)


T = TypeVar("T")

def QmlElement(cls: T) -> T:
    """Type-preserving wrapper around QtQml.QmlElement as that decorator
    stripes type information of the decorated class away, making type
    annotation problematic."""
    return cast(T, QtQml.QmlElement(cls))


MI = QtCore.QModelIndex
PMI = QtCore.QPersistentModelIndex
OQO = Optional[QtCore.QObject]
ModelIndex = MI | PMI