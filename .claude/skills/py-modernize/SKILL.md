---
name: py-modernize
description: >-
  Perform a tight set of modifications on Python code to modernize it.
---

# Python Modernization

Modernize Python code by applying a set of specific transformations.


# Overview

- Read [Agents.md](../../../AGENTS.md) for general guidance, specifically running tools.
- Code is Python 3.13 and above.
- Code is ruff/black-formatted.
- Code is type-annotated.
- Changes always require validation.
- Use LSP for code modifications, not regex or string manipulation.
- Let tools apply changes, do not manually edit code unless necessary.
- Do not perform complicate git commands to compare before/after tool outputs.
- Use modern typing types, e.g. `list | tuple | None` instead of `Optional[List, Typle]`.
- Use f-strings when formatting strings.

# Transformations

1. Convert multiple imports on a single line into a multi-line import.
   ```python
   from foo import bar, baz, bat
   ```

   becomes

   ```python
   from foo import (
       bar,
       baz,
       bat,
   )
   ```
   - This uses the magic trailing comma syntax.
2. QtCore imports `Property`, `Signal`, and `Slot` always are used as `QtCore.Property`, etc.
   ```python
   from PySide6.QtCore import Property, Signal, Slot


   @Slot(int)
   def doSomething(self, value: int) -> None:
       pass
   ```

   becomes


   ```python
   from PySide6 import QtCore

    @QtCore.Slot(int)
    def doSomething(self, value: int) -> None:
        pass
   ```
3. Qt model defintion are properly annotated and use correct types.
   1. Import shared type alias
      ```python
      if TYPE_CHECKING:
          import gremlin.ui.type_aliases as ta
      ```
   2. Examples of correct usage for derived Qt models.
      ```python
      class SomeModel(QtCore.QAbstractListModel):
          someSignal = QtCore.Signal()

          roles = {
              QtCore.Qt.ItemDataRole.UserRole + 1: QtCore.QByteArray(b"label"),
              QtCore.Qt.ItemDataRole.UserRole + 2: QtCore.QByteArray(b"variable"),
          }

          def __init__(self, variable: int, parent: ta.OQO = None) -> None:
              super().__init__(parent)
              pass

          def rowCount(self, parent: ta.ModelIndex = QtCore.QModelIndex()) -> int:
              return 0

          def data(
              self, index: ta.ModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole
          ) -> str | None:
              if not index.isValid() or index.row() >= self.rowCount():
                  return None

              match cast(str, self.roles.get(role, "")):
                  case "label":
                      return "some label"
                  case "variable":
                      return "some variable"
                  case _:
                      return None

          def roleNames(self) -> Dict:
              return self.roles
      ```
    3. Replace all usages of `@QtCore.QmlElement` with `@ta.QmlElement`.
4. All files use `from __future__ import annotations` at the top of the file.
5. Imports are organized into standard groups.
   1. Standard library imports.
   2. Third-party imports.
   3. Local imports.
6. F-strings over all other formatting approaches.
   ```python
   print("Hello {}".format(name))
   ```
   becomes
   ```python
   print(f"Hello {name}")
   ```


# Validation

- Run the linter and formatter.
- Run the type checker.
- Run the test suite, only unit and action_interaction, no integration tests.
