---
paths:
  - "**/*.qml"
---

- An overview of the Kobold style can be found here: `doc/kobold_style.md` read it to understand the design and constraints.

- Use the following way to write signal handlers:

  ```qml
  onSignalWithoutArguments: () => { ... }
  onSignalWithArgument: (arg1, arg2) => { some.thing = arg1 }
  ```

  - Never put arguments in the `(...)` if the signal has no arguments, as that causes control value shadowing

- A `ComboBox` delegate in a `reuseItems: true` `ListView` needs `currentIndex = Qt.binding(() => ...)` in `onCompleted`, not a one-shot assignment, or it goes stale on recycle.

- Delegates in a `reuseItems: true` list should use implicit `modelData`/`index`, not `required property` -- reuse rebinds the former, not reliably the latter.

- `Kobold.Controls`/`Kobold.Composites` and action plugins never use `Kobold.Views` — if there is a component that would be shareable, ask the user whether they want to move it.

- "Never two-way bind" forbids actual binding loops (`Binding{}`, self-aliasing), the following is a sanctioned pattern, not a violation:
  ````qml
  field: action.x
  onFieldEdited: () => { action.x = field }
  ````

- `Repeater { delegate: ActionNode { action: modelData; ... } }` needs `required property var modelData`/`required property int index` on the delegate, or `modelData` resolves to the enclosing action, and `ActionNode`'s `Loader` reloads that action forever -- a silent stack overflow.
