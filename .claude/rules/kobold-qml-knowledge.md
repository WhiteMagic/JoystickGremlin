---
paths:
  - "**/*.qml"
---

- Use `onSignal: (param) => { some.thing = param }` only when the signal actually has a parameter, otherwise you will shadow control values.
- A `ComboBox` delegate in a `reuseItems: true` `ListView` needs `currentIndex = Qt.binding(() => ...)` in `onCompleted`, not a one-shot assignment, or it goes stale on recycle.
- Delegates in a `reuseItems: true` list should use implicit `modelData`/`index`, not `required property` -- reuse rebinds the former, not reliably the latter.
- `Kobold.Controls`/`Kobold.Composites` and action plugins never use `Kobold.Views` — if there is a component that would be shareable, ask the user whether they want to move it.
- Read a replacement component's real source before wiring it -- never assume a legacy widget's property/signal names or arity carried over.
- "Never two-way bind" forbids actual binding loops (`Binding{}`, self-aliasing) -- `field: action.x` + `onFieldEdited: action.x = field` is the sanctioned pattern, not a violation.
- Drop-in replacements often keep the legacy component's exact name -- grep the import path, not the component name, to tell old from new.
- `Repeater { delegate: ActionNode { action: modelData; ... } }` needs `required property var modelData`/`required property int index` on the delegate, or `modelData` resolves to the enclosing action, and `ActionNode`'s `Loader` reloads that action forever -- a silent stack overflow.
