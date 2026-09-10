---
paths:
  - "**/*.qml"
---

# Writing QML in this project

## Color — 11 tokens, from `Theme`

`bg` `bgAlt` `bgHover` `bgSelected` `line` `fg` `fgMuted` `fgDisabled` `accent` `error` `warning`

`bg` base surface and rows, `bgAlt` recessed relative to `bg` in both themes — control fills, popup fill, the left-pane well, `line` every 1px: borders, separators, indent guides, slot rules · `fg` primary text · `fgMuted` descriptions, slot labels, units, `+n` · `fgDisabled` disabled and empty states · `accent` selection and focus only.

Read `Theme.*` for colour, never the `themeManager` context property directly — the sole exception is `Metrics`, which reads `themeManager.uiScale` (a dimension, not a colour). `ThemeManager` is a plain `QObject` exposed as the `themeManager` context property, not a QML singleton; `Theme.qml` is the facade over it. There is no `accentFg` — nothing ever sits on accent. No `Theme.color("accent")`-style accessor: a function indexing a dict is not reactive.

**Accent's complete inventory:** 2px tab underline · 2px selected-row bar · focus outline (2px, `anchors.margins: -2`) · checkbox/radio *mark* · engaged-toggle icon shade · 2px drag insertion line. Expect 2-4 on screen (5 while dragging). Any accent **fill** is an R4 violation.

**Exception:** `BetterProgressBar`'s elapsed-region fill (`Controls/BetterProgressBar.qml`) is accent, filled. It reads a live value (e.g. an axis position), not a decorative or selection state, so it doesn't fit the "never a fill" wording above — but it's still the only filled use of accent in the app. Do not use this as precedent for a new filled control; it exists once, deliberately.

## Dimensions — named `Metrics` tokens

Gaps are **4 / 8 / 12 only**. Control height is **24px, one height app-wide** (`controlHeight`). Icon 16 · checkbox/radio mark box 16 (shares `icon`) · indent step 16 · radius 2 on interactive controls, 0 on layout containers · input row 48 (+4 gap = 52 pitch) · action row 28 · slot header 24 · menu bar and footer 26 (`menuFooterHeight`, one token for both chrome strips) · toolbar 34 · tab strip 36 · window 1400x900 · left pane min 400 · right pane min 900.

**Never call `Metrics.dp(48)` in a delegate** — read a named token, or a `readonly property` computed once on the file's root and referenced from the delegate. Policy functions run once per scale change, not per frame. Exceptions are hand-controlled and named: `hairline`, `accentMark`. A 2px line is `2 * Metrics.hairline`, not its own token.

**Dialog/one-off sizing**: a dialog's own `width`/`height`/`minimumWidth`/`minimumHeight`, or any other value that belongs to exactly one file, is `Metrics.dp(N)` inline — never a new named `Metrics.qml` token. Named tokens are for concepts genuinely shared across files; growing the token list to dodge the raw-px lint on a one-off value is the mistake this rule exists to prevent. If a one-off value is reused several times *within* one file (especially inside a delegate, where it must be pre-computed), give it a `readonly property` on that file's root instead — still local, still not in `Metrics.qml`.

## Type and icons

`FontType.sans` / `.mono`, `Metrics.textBody` (14) / `.textDetail` (12), `FontType.regular` (400) / `.semiBold` (600). No bold, no italic; emphasis is SemiBold.

Mono is **mechanical, not semantic** — only fixed-width readouts where character cells align: spin values, axis values, thresholds, GUIDs, VID/PID. Row titles (`Button 8`) and key combos (`Left Shift + F7`) stay Sans.

`AppIcon` only, with `name` + `role`. Its URL is **bound** to the resolved token so recolour rides the binding graph — never add an imperative refresh.

## Never appears in a `.qml` file

Raw hex (legal only in `style/themes/*.json`) · raw px in a styling position · `Qt.rgba(` ·`Qt.lighter`/`darker`/`tint` · `color-mix` · gradients · `layer.effect` for shadow · `opacity` as a tint (genuine show/hide is fine) · `pointSize` or `pt` · any `pixelSize` outside {12, 14}.

---

## Control templates — `style/qml/Kobold/*.qml`

Root the matching `QtQuick.Templates` type imported `as T` and assign **only** `background`, `contentItem`, `indicator`. The template already tracks state, handles keyboard and mouse, sizes the control and provides accessibility. **Never reimplement template behaviour** — if you are writing a `MouseArea` or a key handler, stop. Read `control.hovered`, `control.down`,
`control.checked`, `control.visualFocus`, `control.enabled`.

States change fills, borders and marks **only** — never layout or size. Checked checkbox and radio = accent border + accent **mark, never a filled box**. There is no primary button.

Popups (`ComboBox` popup, `Menu`, `ToolTip`): opaque `bgAlt` + 1px `line`. **No shadow, ever** — this is where one always sneaks back in. `SpinBox` shows its value in mono.

*"current style does not support customization of this control"* means the style directory is not registered or not on the import path — not a QML bug.

## Action tree — `Composites/{ActionRow,SlotHeader}.qml`

**Action row (28)**: `[chevron 16][type icon 16][name][TriggerMode?][error?][remove]`. The type icon **is** the drag handle. The name is **plain text, not a bordered field**: 14px with a 1px *transparent* border that takes `line` + `bgAlt` on hover — the border always exists so nothing moves. **This is the single sanctioned R1 exception in the app.** The row has **no hover state of its own**; a full-width band drowns that border. `TriggerMode` only when `actionBehavior === "button" && canChangeActivation`.

**Slot header (24)** is scaffolding, not content: `[12px fgMuted label][1px line rule → flex] [Add action ▾]`. `Add action` at rest has **no chrome**; on hover **an edge only** — 1px `line` `fg`, no fill. **Accent is never used here.**

**Indent and guides — the crux.** An action's config, slot headers and child actions all sit one 16px step in from its header, sharing one 1px guide. Config comes first and is **unlabelled**. Depth 0 has no indent; `RootAction` is invisible. **A guide exists only to group child actions: no children -> no visible line — but still reserve the 1px as a transparent border**, or a config-only body stops aligning with a guided sibling and the even grid breaks. Test: cover the labels and you must still see where each slot starts.

**Sequences** are independent trees: 8px space + 8px padding, **no rule between them**. `New action sequence` is an unfilled push button. The binding header's `Add action` **is** bordered — deliberately unlike the slot-header one. `Treat as` is radios (axes and hats only).

**Drag:** grab the type icon; drop targets are **row-edge bands** (upper/lower half, ~12px), not gap-dwellers; feedback is a **2px insertion line in `accent`, always exactly 2px, never a filled band**; no parting animation.

**Macro steps are NOT child actions** — render them as a table, or the UI is lying.

## Left panel — `Views/InputButton.qml`

Pane is `bgAlt`; rows are `bg` cards, 1px `line`, 2px radius, 8px side margin, **48px with a 4px gap**, no shadow. `ListView` with `reuseItems: true` and shallow delegates — ~100 rows.

Three things that never duplicate: **identifier** (left, `fg` 14px) · **description** (right, `fgMuted` 12px) = accumulated names of actions the user **modified**, so it carries **intent**; absent entirely when nothing was modified · **chips** (row 2) = **structure**, full action names, no icons, no abbreviations.

**An empty row is complete**, not truncated — no placeholder text, no greying.

**Chip overflow: measure, don't guess.** Render all chips, measure, drop only what genuinely does not fit, replace with `+n` in `fgMuted`. Never pre-truncate by count — this is the most common way to get this pane wrong. Chips are driven by the **existing** `Action sequence information` option; do not add a setting.

**Selection is two channels:** `bgSelected` fill **and** a 2px `accent` left-edge bar.

## Shell

Root is `ApplicationWindow`. Device tabs **and** `Scripts`/`Settings` are **one exclusive selection set of one control type**, separated by a 1px `line` vertical rule. Active tab = 2px `accent` underline + `bgSelected`, **never a fill**. Inactive tabs are **not greyed** (not-current is not unavailable) and have **no icons**. A 1px `line` rule runs the full width beneath the tab row, separating it from the split view below. The device-tab strip has no horizontal scrollbar; it scrolls via wheel/drag, plus full-height prev/next `ToolButton`s bookending just the device list, enabled only while scrolling that direction is possible.

`Configuring mode` **keeps its label and toolbar position** — users misread it as switching the live mode, so the label is load-bearing.

Footer is plain adjacency: `State · Editing · Running`. Editing differing from Running is **routine**: no warning, no icon, no tone shift. Do not invent a divergence affordance.

## Action Plugin views — `action_plugin/*/*.qml`

**Body only** — a `ColumnLayout` of rows. No chevron, header, name field, guide or indent; those are the core's. Import `QtQuick.Controls` (styled primitives), `Kobold.Controls` (tokens + `LabeledRow`/`InlineRow`) and, for a container plugin with its own nested action list (Chain, Condition, Tempo, …), `Kobold.Composites` to instantiate `ActionNode` directly for its children. **Never `Kobold.Views.*`** — that is what "plugins never import `Kobold.Views`" means; it does not forbid the stock primitives or `Composites`. Kit names must not collide
with `QtQuick.Controls`.

**Never two-way bind** — `checked: action.invert` + `onToggled: action.invert = checked`.

Align **within** an action; there is no global label column and raggedness across actions is correct. Labels sentence case, no colons. Inline-sentence configs stay sentences (`When [All ▾] of the following...`), not `Mode: [All ▾]`.

Vocabulary: checkbox = on/off · radio = 2-3 exclusive, all visible · toggle = armed/engaged · push button = command (`Invert Curve` is a command). **Switches are deleted app-wide.** The action selector is a **menu button, not a combo** — no value, label never changes.

Multi-input actions (Merge Axis, Dual Axis Deadzone): labelled group + N source rows; an **unassigned source row is a first-class state carrying its instruction as its value** — that is the whole feature; one assign widget; `activation-mode: disallowed` so **no TriggerMode and no reserved space for it**.
