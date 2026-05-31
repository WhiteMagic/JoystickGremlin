# AGENT.md — `qml/compact/`

> Read this file fully before touching anything in this folder.

## What This Folder Is

This folder is the `Compact` QML module — a set of compact/condensed variants
of Qt Quick Controls 2 (Universal theme) widgets and project-level composite
widgets that use them. Every control here presents the same visual design as
its standard counterpart but with reduced padding, smaller implicit height, and
a 14 px font so it fits in dense row layouts (toolbars, list-item action rows).

**Owns:** All compact-sized variants of Universal-theme base controls, and any
composite/compound widget whose full-size analogue exists (or could exist)
elsewhere in the UI.

**Does not own:** Standard-sized controls (those live directly in `qml/`),
business logic, data models, or reusable layout helpers.

Rules:
- One component per file. File name must match the QML type name exactly (PascalCase).
- Every new file **must** be registered in `qmldir` before use.
- No subdirectories.

---

## Membership Rules

A component belongs here if **either** condition holds:

1. **Base override** — it directly inherits from a `QtQuick.Templates as T` type
   (`T.Button`, `T.CheckBox`, etc.) and applies the compact size constraints
   below. Every Universal-theme base control for which a compact variant is
   needed **must** live here, not inline at the call site.

2. **Compact composite** — it is a compound widget whose standard-size
   equivalent exists or could exist in `qml/`. Use compact sub-controls
   internally; do not mix standard-size controls inside a compact composite.

---

## Coding Conventions

### Adding new UI components

Defining a new `Compact` class always start by copyuing the original Universal style variant and then modifies it. This is done to simplify keeping the `Compact` widgets up-to-date with changes to the main Universal theme.

### Sizing Contract

The height and font size are fixed for `Compact` UI elements to the following values:

| Property | Value |
|---|---|
| `font.pixelSize` | `14` |
| Background `implicitHeight` | `24` |

Furthermre padding is reduced, usually by half to keep some padding but reduce the overall space required by widgets. Below are some example values used:

| Property | Value |
|---|---|
| Button padding | `padding: 4`, `verticalPadding: 2` |
| ItemDelegate padding | `padding: 6`, `topPadding: 4`, `bottomPadding: 4` |
| CheckBox padding | `padding: 2` |

Do not introduce a new base override that deviates from these without updating
this table.

### Naming

- File names and QML type names: PascalCase, matching the Qt control name
  where applicable (`Button`, not `CompactButton`).
- Internal IDs: `control` for the root in base overrides (matches Qt
  convention); `_camelCase` with underscore prefix for private items in
  composites.

### Patterns to Follow

- Keep base overrides structurally identical to the Qt Universal source —
  same `contentItem` / `background` / `indicator` structure, only sizing
  values changed. This makes future Qt upgrades straightforward to diff.
- Composite components expose their interface through named properties and
  signals only; no internal implementation details should leak to callers.

### Patterns to Avoid

- Do not import from `QtQuick.Controls` as the root type of a base override —
  this layers two themes on top of each other.
- Do not hardcode colours. Use `Universal.*` color tokens (e.g.
  `Universal.foreground`, `Universal.baseLowColor`) so the control respects
  the active theme.
- Do not add components here that have no standard-size analogue and are
  specific to a single feature — those belong in the feature's own QML file or
  `qml/`.

---

## How Callers Use This Module

```qml
import Compact as Compact

Compact.Button { text: "Add" }
Compact.ComboBox { model: [...] }
Compact.ButtonStateSelector {
    isPressed: modelData.isPressed
    onStateModified: (isPressed) => { modelData.isPressed = isPressed }
}
```

Callers are in `action_plugins/**/MacroAction.qml` and `qml/compact/ButtonStateSelector.qml`.
