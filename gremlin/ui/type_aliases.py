# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys
from typing import (
    TypeVar,
    cast,
)

from PySide6 import (
    QtCore,
    QtQml,
)

T = TypeVar("T")


def QmlElement(cls: type[T]) -> type[T]:
    """Type-preserving QML element registration decorator.

    Replacement for the @QtQml.QmlElement decorator which breaks type
    annotations.
    """
    frame = sys._getframe(1)
    uri = frame.f_globals["QML_IMPORT_NAME"]
    major = frame.f_globals.get("QML_IMPORT_MAJOR_VERSION", 1)
    minor = frame.f_globals.get("QML_IMPORT_MINOR_VERSION", 0)
    QtQml.qmlRegisterType(cls, uri, major, minor, cls.__name__)
    return cast(type[T], cls)


MI = QtCore.QModelIndex
PMI = QtCore.QPersistentModelIndex
OQO = QtCore.QObject | None
ModelIndex = MI | PMI
