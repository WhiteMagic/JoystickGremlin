# AGENTS.md - JoystickGremlin Developer Guide

This file provides guidance for AI agents working on the JoystickGremlin codebase.


## Project Overview

JoystickGremlin is a Python application (PySide6/QML) for configuring joystick devices on Windows. It uses vJoy for virtual joystick emulation and supports macros, modes, and Python scripting.


## Build, Lint, and Test Commands

### Running Tests

```powershell
# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest test/unit/test_profile.py

# Run a specific test
poetry run pytest test/unit/test_profile.py::test_simple_action

# Run tests with verbose output
poetry run pytest -v

# Run tests matching a pattern
poetry run pytest -k "test_simple"

# Run e2e tests only
poetry run pytest test/integration/

# Run action interaction tests only
poetry run pytest test/action_interaction/

# Run unit tests only
poetry run pytest test/unit/
```

### Linting

```powershell
# Run ruff linter (ANN = annotations required)
poetry run ruff check .
```

### Type Checking

```powershell
# Run pyright type checker
poetry run pyright
```

### Running the Application

```powershell
# Run in dev mode
poetry run python joystick_gremlin.py
```


## Architecture

### Code Structure

- Keep related functionality together
- Follow the existing module organization:
  - `gremlin/` - Core application logic
  - `gremlin/ui/` - UI-related code (PySide6/QML integration)
  - `action_plugins/` - Action plugins, one directory per action
  - `test/` - Test suites
  - `qml/` - QML UI files
  - `vjoy/` — vJoy virtual joystick ctypes wrapper
  - `dill/` — native device input library (DILL.dll) with Python wrapper
- `joystick_gremlin.py` — entry point; initializes devices, Qt engine, plugins

### Key Singletons

| Class | Module | Purpose |
|---|---|---|
| `Configuration` | `gremlin.config` | Persistent app config |
| `EventListener` | `gremlin.event_handler` | Raw input capture & routing |
| `ModeManager` | `gremlin.mode_manager` | Mode stack & switching when Gremlin is active |
| `Backend` | `gremlin.ui.backend` | Main QML↔Python bridge |

Use `metaclass=common.SingletonMetaclass` (not the legacy `@common.SingletonDecorator`).

### Profile Storage

Profiles are XML files. `gremlin.profile.Profile` owns load/save and dispatches this via various `to_xml` and `from_xml` call chains.

### Python/QML Bridge

- `Backend` (registered as `backend` context property) exposes signals and slots to QML
- QML-accessible classes use `@QtQml.QmlElement` or `engine.rootContext().setContextProperty()`
- Qt signals/slots use `@QtCore.Signal` / `@QtCore.Slot` decorators
- Never call Qt GUI APIs from non-main threads


## Code Style Guidelines

### File Headers

Every Python file must include:
```python
# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only
```

### Imports

- Use `from __future__ import annotations` for forward references
- Sort imports: stdlib, third-party, local (alphabetically within groups)
- Use absolute imports within the package (e.g., `from gremlin.types import InputType`)
- Use `TYPE_CHECKING` guard for imports only needed for type hints to avoid circular imports

Example:
```python
from __future__ import annotations

import logging
from typing import (
    cast,
    Any,
    TYPE_CHECKING
)

from PySide6 import (
    QtCore,
    QtQml
)

import gremlin.profile
from gremlin.types import InputType
from gremlin.error import GremlinError

if TYPE_CHECKING:
    from gremlin.base_classes import AbstractActionData
```

### Type Annotations

- **Required**: All function signatures must have type annotations (enforced by ruff ANN rule)
- Use Python 3.13+ syntax: `list[str]`, `dict[str, int]` (no need for `List`, `Dict` from typing)
- Acceptable exceptions:
  - `PySide6` import errors (project-wide Pylance issue)
  - `AbstractActionData` attribute unknowns (project-wide)
- Use `X | None` over `Optional[X]`

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `JoystickGremlinApp`, `Profile`)
- **Functions/methods**: `snake_case` (e.g., `get_vjoy_device`, `from_xml`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `MAX_CACHE_SIZE`)
- **Private members**: `_leading_underscore` (e.g., `_cache`)
- **Qt properties/slots**: Follow Qt conventions (e.g., `imageReady`, `requestImage`)
- **QML variables**: Follow Qt convention (e.g. `someVariable`)
- **QML element identifiers**: Always start with `_` (e.g. `_label`, `_actionModel`)

### Qt Patterns

- Use `@QtCore.Signal` and `@QtCore.Slot` decorators for Qt signals/slots
- Signals are defined as class attributes: `imageReady = QtCore.Signal(str, str)`
- Subclass `QtCore.QObject` for QML-accessible classes if no more specialized class is applicable
- Use `@QtQml.QmlElement` decorator for classes to register with QML
- Register QML context properties with `engine.rootContext().setContextProperty()` to be used in exceptional circumstances only

```python
from PySide6 import QtCore

if TYPE_CHECKING:
    import gremlin.ui.type_aliases as ta

class DataProvider(QtCore.QObject):
    dataReady = QtCore.Signal(str)

    def __init__(self, parent: ta.OQO=None):
        self._value = ""

    def _get_value(self) -> str:
        return self._value

    def _set_value(self, val: str) -> None:
        self._value = val
        self.dataReady.emit(val)

    value = QtCore.Property(
        str,
        fget=_get_value,
        fset=_set_value,
        notify=dataReady
    )
```

### Error Handling

- Custom exceptions are defined in `gremlin.error` and inherit from `GremlinError`
- Use specific exception types (e.g., `ProfileError`, `VJoyError`, `MissingImplementationError`)
- Provide meaningful error messages
- Exceptions are caught on the highest level and logged there

Example:
```python
from gremlin.error import GremlinError

try:
    value = int(text)
except ValueError:
    raise GremlinError(f"Invalid device index: {index}")
```

### Logging

- Use `logging.getLogger("system")` for logging

### Qt Threading Rules

- **Never use Qt GUI classes from non-main threads** (Qt is not thread-safe)
- Background threads (e.g., `threading.Thread`) are acceptable for non-GUI work (device polling, file monitoring)

### Singleton Pattern

The project uses two singleton patterns:
- Only the newer `metaclass=common.SingletonMetaclass` should be used
- `@common.SingletonDecorator` is legacy and is not to be used anymore

### QML Integration

- Use `Connections` for QML-to-Python signal connections when data binding cannot be used
- Use `onSignalName` for Python-to-QML property changes
- QML model classes often inherit from `QtCore.QAbstractListModel` and implement `rowCount()`, `data()`, `roleNames()`

### Action Plugins

Each plugin under `action_plugins/<name>/` defines:
- `AbstractActionData` subclass — XML serialization, validity, metadata (`tag`, `name`, `icon`, `version`, `input_types`, `functor`)
- `AbstractFunctor` subclass — actual runtime behavior
- `ActionModel` — QML UI model, enabling modifying the data via the UI

Required overrides on `AbstractActionData`: `_from_xml()`, `_to_xml()`, `is_valid()`, `_valid_selectors()`, `_get_container()`, `_handle_behavior_change()`.


Example:
```python
from gremlin.base_classes import AbstractActionData, AbstractFunctor
from typing import override

class SpecialActionData(AbstractActionData):

    tag = "special-action"
    name = "Special Action"
    icon = "f123"
    version = 1
    functor = SpecialActionFunctor

    # Implement functions mandated by the base class.
```

### Testing Conventions

- Tests go in `test/unit/`, `test/integration`, or `test/action_interaction/` depending on use  case
  - Self-contained unit tests are placed in `test/unit`
  - Simulated action interaction tests are placed in `test/action_interaction`
  - Full end to end system tests are placed in `test/integration`
- Function tests for action plugins are placed in `test/action_interaction`
- Tests in `test/action_interaction` have access to a `jgbot` fixture (`test/action_interaction/conftest.py:JoystickGremlinBot) which is similar to the Qt pytest fixture
- Use pytest fixtures from `test/conftest.py` and `test/unit/conftest.py`
- Use `pytest.raises()` for exception testing

Example:
```python
from test.unit.conftest import get_fake_device_guid

def test_something(xml_dir: pathlib.Path):
    p = Profile()
    p.from_xml(str(xml_dir / "profile_simple.xml"))
    assert len(p.inputs) == 1
```

### Type Aliases

Use type aliases from `gremlin.ui.type_aliases` for Qt-specific types:
```python
import gremlin.ui.type_aliases as ta
```

### Documentation

- Use docstrings for classes and complex functions
- Keep docstrings concise; describe purpose and parameters
- Do not add unnecessary inline comments

### Common Patterns

- Use `dataclasses` for simple data containers
- Use `ElementTree` for XML parsing/creation
- Use `pathlib.Path` for file paths

### Known Issues (Ignore)

- Pylance may show `Import "PySide6" could not be resolved` - this is a project-wide issue, not caused by your changes
- Some `AbstractActionData` attribute unknowns may appear - also project-wide

### Pre-commit Checks

Before considering a task complete, run:

```powershell
poetry run ruff check .
poetry run pyright
poetry run pytest
```
