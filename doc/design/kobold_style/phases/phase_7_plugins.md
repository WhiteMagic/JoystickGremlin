# Phase 7 — Actions / plugin config views (reflow)

**Goal:** finalise the public `Kobold.Controls` kit and migrate each action's config *body* onto it.
Because plugins are built from basic controls (already restyled in Phase 2), most of this is **layout
reflow** for the new heights/grid, not reconstruction.

**Prereqs:** main guide §0–§5; the reference plugin (`MapToVJoyConfig.qml` + `map_to_vjoy.py` +
`map-to-vjoy.svg`). **Depends on:** Phases 1–6. **Enables:** the full app; third-party plugin authoring.

---

## Concepts for this phase

**A plugin is a trio:** a **QML config view** (what the user edits), **Python logic** (the action's
behaviour/model), and an **SVG type icon**. The reference stub shows all three; copy it.

**MVVM.** The Python logic is the *model/view-model*: it holds the editable config as
`Property(..., notify=changed)` fields and exposes commands as `@Slot` methods. The QML view is the
*view*: it **reads** config from the model and **writes** changes back on user interaction. The core
injects the model into the view as a `required property var action`.

- **Don't two-way bind** (it causes binding loops). Instead: bind a control's displayed value to
  `action.<field>`, and in the control's signal handler push the new value back:
  `checked: action.invert` + `onToggled: action.invert = checked`.

**The plugin supplies ONLY the config body.** No chevron, header, name field, guides, or indent —
those are the core's (Phase 6). The plugin's root is just the body content (a `ColumnLayout` of rows).
It mounts into the body slot the core positions at the correct indent.

**Import boundary — the rule stated precisely:**
- **`import QtQuick.Controls`** → the styled primitives (`Button`, `CheckBox`, `RadioButton`,
  `ComboBox`). They're auto-styled by the Kobold style; the plugin never themes them.
- **`import Kobold.Controls`** → the tokens (`Theme`, `Metrics`, `FontType`, `AppIcon`) and the
  within-action helpers (`LabeledRow`, `InlineRow`, field wrappers).
- **Never `import Kobold.Internal.*`.** "Plugins import only `Kobold.Controls`" means *never reach
  into internals* — it does **not** forbid the standard `QtQuick.Controls` primitives.

**`Kobold.Controls` is a curated allowlist, not a wrapper layer.** Most entries are re-exports; the
point is a stable public namespace plugins depend on, decoupled from where internal files live. **Kit
type names must not collide with `QtQuick.Controls`** (no `Button`/`CheckBox`/`ComboBox` in the kit),
so a plugin importing both never hits an ambiguity.

**Align within an action, not across.** Helpers align a label column *for one action*. There is **no
global label column**; raggedness across different actions is accepted and expected. Labels are
sentence case, no colons. Inline-sentence configs stay sentences (`When [All ▾] of the following…`),
not forced into `Mode: [All ▾]`.

**Widget vocabulary (SPEC §7):** checkbox = on/off; radio = 2–3 exclusive, all visible; toggle button
= armed/engaged state; push button = command (e.g. `Invert Curve` is a command → push button, not a
state). The **action selector is a menu button, not a combo** — no value, label never changes
(`Add action ▾` before and after); it's the one exception to "every `▾` is a value selector."

**Multi-input actions (SPEC §11)** — Merge Axis, Dual Axis Deadzone — render as a **labelled group +
N source rows**. The group label *is* the message. An **unassigned source row is a first-class state
carrying its instruction** (e.g. "Not assigned — open the second axis and add this merge instance
there to assign it.") — that instruction-as-default-value is the whole feature; everything else is a
readout. **One assign widget** (don't mix `⦿Rec` and `↻`). These actions carry
`activation-mode: disallowed` → **no TriggerMode, ever; reserve no space for it.** Use the one
canonical input-identifier formatter (`withDevice` true in configs, false in the left pane).

---

## What you're building

### 1. `Kobold.Controls` kit (public)

- Re-export the Foundation singletons + `AppIcon`.
- The within-action helpers used by config views: **`LabeledRow`** (sentence-case label left, control
  column right, aligned within this action), **`InlineRow`** (inline-sentence layout), and any field
  wrappers you standardise. Names must not collide with `QtQuick.Controls`.
- `qmldir` declaring the kit; this is the plugin contract.

### 2. Migrate each action's config view

- For each existing action, rewrite its config view as a **body-only** `ColumnLayout` consuming the
  kit (see the reference `MapToVJoyConfig.qml`).
- Most controls reskin automatically (Phase 2). Expect the real work to be **reflow**: the 24px
  control height and 2px grid change spacing/wrapping, so rows may need reorganising.
- Bind to the Python logic via `required property var action`; read fields, write on signals.

### 3. Multi-input pattern (SPEC §11)

- A reusable **labelled group + N source rows** component; the unassigned-source-row state with its
  instruction string; one assign widget; no TriggerMode/space reserved. The wording is per-plugin
  (`Merged axes` is Merge Axis's; the deadzone needs its own) — the **pattern** is reusable, the
  string is not.

### 4. Mounting (`CONFIRM-5`)

- Confirm how the core discovers a plugin's trio and injects the model into the view (the `action`
  property). Wire the body slot from Phase 6 to load the plugin view.

---

## Definition of Done

- [ ] `Kobold.Controls` exists, re-exports the singletons + `AppIcon` + the within-action helpers,
      and no kit type name collides with `QtQuick.Controls`.
- [ ] A migrated config view imports only `QtQuick.Controls` + `Kobold.Controls` (never
      `Kobold.Internal`), is body-only, and binds to its Python model without two-way binding loops.
- [ ] Config views reskin from the style; residual changes are layout reflow, not rebuilds.
- [ ] Labels are sentence case, no colons; alignment is within-action; inline-sentence configs stay
      sentences.
- [ ] Multi-input actions render as a labelled group + source rows; an unassigned source row shows its
      instruction as its value; one assign widget; no TriggerMode space.
- [ ] `Invert Curve`-style commands are push buttons; the action selector is a menu button (label
      never changes), not a combo.

## Watch-outs

- Don't draw any tree scaffolding in a plugin — body only.
- Don't import internals; don't collide kit names with QtQuick.Controls.
- Don't build a global label column; ragged-across-actions is correct.
- **`OPEN-1` (SPEC §11):** merge-axis has two editable names (`label` shared vs `action-label` this
  node) and nothing says which is which. **Flag it; do not invent a fix.**

**Spec refs:** §7, §8 (config), §11. **Guide refs:** §4.6; reference plugin stub.
