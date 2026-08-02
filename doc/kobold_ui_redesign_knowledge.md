# Kobold UI redesign — working knowledge

Background for anyone doing small work on this codebase: fixups, conversions of remaining
widgets, bug fixes, review. This is orientation, **not** the spec. For anything you are about
to *decide*, go read the source documents listed below — they are decided, not suggestive.

---

## 1. What the project is

Joystick Gremlin R14 is a **Windows desktop utility for remapping HOTAS hardware**. Power users
bind 100–200 inputs across 4–6 devices, in long sessions, beside a running game.

The design brief calls it **"an instrument, not a product": dense, literal, calm.** No
onboarding, no delight, no marketing UI. Identity is carried by the *organisation of data* —
top chrome, left input list, right action tree, nested actions — not by colour or typeface.
That layout is preserved exactly; the redesign changes how it is drawn, not where things are.

**Stack:** PySide6 + QML (Qt Quick), targeting **Qt/PySide6 6.11**, Windows-first.

**Approach:** a **fully custom Qt Quick Controls 2 style** ("Kobold") plus a handful of
singletons for colour, dimensions and type. Themes are colour-only JSON data files. Dimensions,
type and icons are fixed design constants and are **not** themeable.

## 2. The document set

| File | What it is | Authority |
|---|---|---|
| `jg_style_design_specification.md` (SPEC) | The visual spec, condensed. Every value decided. | **Wins on visual rules** |
| `jg_style_architecture_design.md` (guide) | Implementation guide: architecture, modules, wiring, phases. §0–§5 are the always-loaded context. | **Wins on architecture** |
| `jg_style_mockup.html` | Partially functional HTML prototype of the intent. | Illustrative only |
| `phases/phase_1..7_*.md` | One detailed doc per phase: concepts, deliverables, Definition of Done, watch-outs. | Most detailed, most recent |

Referenced elsewhere as `SPEC §n` and `guide §n`. Both live in the repo; keep them there.

## 3. The five hard rules (SPEC §2) — inviolable

- **R1 — Layout is static.** Nothing appears, disappears, moves or resizes on hover. Hover may
  only add an overlay that is a *superset* of what is already on screen. **One** sanctioned
  exception, ever: the action-name field's border (SPEC §8).
- **R2 — No shadows, ever.** Floating surfaces = 1px border + opaque fill. No elevation, blur,
  translucency. Combobox popups and menus are where a shadow always tries to sneak back in.
- **R3 — No derived colours.** Every colour is a named token or it is a bug. No alpha, no
  tints, no `Qt.lighter/darker`, no `Qt.rgba`, no `color-mix`.
- **R4 — Accent = state only, never a fill.** No primary button anywhere. Nothing ever sits
  *on* accent, so there is no `accentFg` token.
- **R5 — Everything visible at once.** No accordions, wizards, drawers, "advanced" sections,
  overflow menus.

## 4. Tokens — the only legal source of colour and dimension

**Colour: exactly 11 tokens**, read from the `Theme` singleton:
`bg`, `bgAlt`, `bgHover`, `bgSelected`, `line`, `fg`, `fgMuted`, `fgDisabled`, `accent`,
`error`, `warning`. `bgAlt` is *recessed relative to `bg` in both themes*. Two schemes ship
(light, dark) as two instances of one contract — do not "design dark mode" separately.

**Accent's complete on-screen inventory:** 2px tab underline · 2px selected-row bar · focus
outline (2px, offset −2px) · checkbox/radio **mark** (border + tick, never a filled box) ·
engaged-toggle icon shade. Expect ~2–4 accent marks on screen at any moment.

**Dimensions** come from the `Metrics` singleton. Scaling is **pure zoom at 100/150/200%**
implemented as multiplied integer tokens (never a scene-graph transform or `QT_SCALE_FACTOR`),
so **every dimension must be integer at 100% *and* 150% → 2px grid, even numbers.** 13px is
illegal (×1.5 = 19.5). The 1px border is the sole accepted exception.

Key constants: gaps **4 / 8 / 12 only** · control height **24px, one height app-wide** ·
icon 16 · indent per level 16 · radius 2 on interactive controls, 0 on containers ·
input row 48 (+4 gap = 52 pitch) · action row 28 · menu bar 26 · toolbar 34 · tab strip 36 ·
footer 24 · window 1400×900 · left pane min 400 · right pane min 900.

**Type:** IBM Plex Sans + IBM Plex Mono, bundled in qrc (not system fonts). **Weights 400 and
600 only** — no bold, no italic; emphasis is SemiBold. **Font sizes ∈ {12, 14}, in px, never
pt.** Mono is *mechanical, not semantic*: only where character-cell alignment matters (spin
values, axis values, thresholds, GUIDs, VID/PID). Row titles and key combos stay Sans.

**Icons:** Bootstrap Icons 1.13.1, shipped as **individual 16×16 SVG files, not the webfont**,
filled paths, `currentColor`. Recoloured by a Python `QQuickImageProvider` registered as
`image://icon/<name>?c=<hex>&px=<size>` (Qt's SVG renderer cannot resolve `currentColor`
itself). Consumers only use `AppIcon`, which binds its URL to a live `Theme` token so recolour
rides the binding graph. Chips carry no icons.

## 5. Architecture in one page

- **`ThemeManager` (Python, plain `QObject`)** — source of truth. Scheme discovery, parse,
  validation, active scheme. 11 `Property(QColor, …, notify=changed)`, a `uiScale` property
  (100 | 150 | 200), and **one** `changed` signal. Exposed to QML as the **context property
  `themeManager`** (`setContextProperty`), not a QML singleton.
- **`Theme.qml` (QML `pragma Singleton`)** — thin facade, 11 `readonly property color x:
  themeManager.x`. **Every consumer and every plugin reads `Theme`, never `themeManager`** (the
  one exception is `Metrics`, which reads `themeManager.uiScale`). Reason: only the 11 facade
  bindings cross the Python↔QML boundary, and only on a theme change; thousands of delegate reads
  stay QML-side.
- **`Metrics.qml`, `FontType.qml`** — QML singletons. `Metrics` holds named dimension tokens
  computed once per scale change; **consumers read named tokens, never call `Metrics.dp(...)`
  in a delegate.**
- **All scheme file IO goes through `QFile`/`QDir`**, never Python `open()`/`glob` — `QFile`
  resolves both `:/…` (qrc) and real filesystem paths.
- **Module tiers.** `Kobold` is the authoritative name for the style and its namespace (see
  §11 on the stale `Gremlin.*` text in the guide):
  - `Kobold.Foundation` — tokens, singletons, `AppIcon`, config surface. Used by everything.
  - *the Kobold style* — QQC2 control templates, consumed implicitly via
    `import QtQuick.Controls` after `QQuickStyle.setStyle("Kobold")`.
  - `Kobold.Controls` — leaves (no `Kobold`-type children: `Chip`, `TreeIndent`,
    `ActivationToggle`, `ScrollList`, …) plus re-exports of the Foundation singletons and
    within-action helpers (`LabeledRow`, `InlineRow`, field wrappers). One of two **public plugin
    surfaces**, alongside `Composites`. **Kit type names must not collide with `QtQuick.Controls`**
    (no `Button`/`CheckBox`/`ComboBox` in the kit).
  - `Kobold.Composites` — assemblies of `Kobold` types with no app state (`ActionNode`,
    `ActionRow`, `SlotHeader`, `ActionStepTable`, `ActivationBehavior`). Also plugin-importable, for
    container plugins (Chain, Condition, Tempo, …) instantiating `ActionNode` for their own children.
  - `Kobold.Views` — app components and shell (`InputButton`, `BindingHeader`,
    tabs/toolbar/footer, dialogs). Churns freely. **Plugins never import these.**
- **Style templates only supply visuals.** Each style file roots a `QtQuick.Templates` type and
  assigns `background` / `contentItem` / `indicator`, reading `control.hovered`, `control.down`,
  `control.checked`, `control.visualFocus`, `control.enabled`. Never reimplement template
  behaviour, key handling or state machines.
- **Startup order matters:** `QQuickStyle.setStyle` / `setFallbackStyle("Basic")` **before** the
  engine loads any Controls-importing QML; then fonts, image provider, import paths, then the
  Python modules whose `@QmlElement` types must register.

## 6. Domain model the UI renders

- **One node type: the action.** Editable name + type config + N named slots holding nested
  actions. Slot counts are dynamic (Condition 2, Tempo 2, Hat 4/8, Chain N, Map to vJoy 0).
- **The library owns config; inputs hold references** by UUID. One action can be referenced by
  two roots — that is how multi-input actions (Merge Axis, Dual Axis Deadzone) appear on two
  inputs; it is literally one object. **The file format is fixed — do not change it.**
- **`RootAction` is invisible** — no config, no indent. Top-level actions sit at **depth 0**.
- **Macro steps are NOT child actions** — render them as a table. If they look like nesting,
  the UI is lying.
- **Tree grammar is core-owned:** an action's config, slot headers and child actions all sit
  one 16px step in from its header, sharing one 1px guide. Config comes first and is
  unlabelled. A slot header is the only thing that says "actions live below me."
  **A guide exists only to group child actions — no children, no guide** — but the body still
  reserves the 1px as a *transparent* border so alignment and evenness hold.
- **A plugin supplies only its config *body*.** The core draws chevron, type icon (which is
  also the drag handle), name field, trigger/error/remove, slot headers, guides, indentation,
  drag-and-drop.

## 7. The phases (what has been built, and in what order)

1. **Foundation** — tokens, singletons, fonts, icon provider, shipped schemes + JSON schema.
2. **Custom QQC2 style** — every basic control redrawn, app-wide, with no call-site changes.
3. **Playground + lint** — a permanent gallery (control × state × theme × zoom) plus the CI
   lint and unit tests. The gallery is first-class and stays forever; it is where you verify.
4. **Left pane** — the input list: `bgAlt` recessed well, 48px `bg` cards, identifier +
   description + chips.
5. **Shell** — menu bar, toolbar, tab strip, footer, split layout.
6. **Action-tree scaffolding** — the recursive action row / slot header / guides / drag-drop,
   without plugin bodies.
7. **Plugins** — finalise `Kobold.Controls` and reflow each action's config body onto it.

The phase docs contain retrospective notes (e.g. Phase 2's reminder to flip the app-wide
`self.setFont(...)` off `"Segoe UI"`; Phase 4 pointing at `InputButton.qml` and
`DeviceInputList.qml` as "the current implementation"), which implies the early phases have
landed. **Verify actual progress against the repo, not against these docs.**

## 8. Rules that are most often got wrong

- Chips in the left pane: **render all, measure, then drop** — `+n` only on genuine overflow.
  Never truncate by count. No abbreviations, no icons.
- Left pane **description = accumulated names of actions the user *modified*** (intent);
  **chips = structure**. They never duplicate. No modified actions → no description, and a
  48px empty row is **complete, not truncated**. Don't add placeholder text or greying.
- The **action row has no hover state of its own** — a full-width hover band drowns the name
  field's 1px border, which is the one sanctioned R1 exception.
- The slot-header `Add action` is **scaffolding**: no chrome at rest, an **edge only** (1px
  `line` + `fg` text, no fill) on hover, never accent. The **binding header's** `Add action` is
  a bordered button — deliberately different.
- Action **sequences are separated by space + padding, with no rule between them.** A rule
  would imply they are rows of one list; they are independent trees.
- Drag: grab the **type icon**; drop targets are **row-edge bands** (upper/lower half, ~12px),
  not gap-dwellers; feedback is a 2px insertion line in **`line`, not accent**; no animation.
- Tabs: device tabs and Scripts/Settings are **one exclusive selection set of one control
  type**, separated by a 1px vertical rule. Active = underline + SemiBold + `bgSelected`.
  **No greying of inactive tabs** (not-current ≠ unavailable), no icons, never accent-filled.
- The footer is plain adjacency: `State · Editing · Running`. **Editing ≠ Running is routine**,
  so no warning, no icon, no tone shift. Don't invent a divergence affordance.
- The toolbar's `Configuring mode` control **keeps its label and its position** — users
  repeatedly misread it as switching the live mode, so the label is load-bearing.
- The **action selector is a menu button, not a combo**: no value, no selection state, the
  label never changes (`Add action ▾` before and after). Every other `▾` in the app *is* a
  value selector. `Invert Curve` is a command → push button, not a state.
- **Switch controls are deleted app-wide**, including in Options.
- In plugin views, **don't two-way bind**: `checked: action.invert` + `onToggled:
  action.invert = checked`. And align *within* an action — there is no global label column;
  raggedness across actions is correct.

## 9. How the rules are enforced

Mechanical checks (SPEC §12, guide §7), wired into CI in Phase 3 — run them before you claim
something is done:

- grep for **hex colours** outside `themes/*.json` → must be `Theme.*`
- grep for **raw px** in styling positions → must be `Metrics.*`; the allowlist is tiny and
  deliberately documented (this is where discipline erodes)
- grep for `box-shadow`, `gradient`, `Qt.rgba(`, `color-mix`, `layer.effect` shadow, `opacity`
  used as a tint → must be zero
- `pointSize`/`pt` → defect; font sizes must be {12, 14} via `Metrics`
- **Metrics-resolution test:** every token at scale ∈ {1.0, 1.5, 2.0} is an integer or a
  declared exception (`hairline`, `insertionLine`, `indentGuide`, 1px border)
- **Scheme-schema test:** exactly 11 keys, `^#[0-9a-fA-F]{6}$` (alpha rejected),
  `meta.appearance ∈ {light, dark}` if present

Human checks worth repeating: **cover the labels** in the tree (you must still be able to point
at where each slot starts), **count accent marks** (~2–4, any accent *fill* is an R4
violation), **hover any row** (anything that appears/moves/resizes is an R1 violation).

Screenshot/pixel-diff tests are deliberately deferred. Scheme hot-reload is deliberately not
implemented — schemes load at startup only.

## 10. Open items — flag, don't invent

- **`OPEN-1`** — `merge-axis` has two editable names, `label` (the shared instance) and
  `action-label` (this node), and nothing says which is which. **Report it; do not design a
  fix.** The user will resolve it.
- **`CONFIRM-1`** — how `ThemeManager` reads the selected scheme id and how `uiScale` reaches
  QML, via the existing config class (`gremlin/config.py`).
- **`CONFIRM-2`** — the exact 6.11 packaging/registration for a custom style from qrc. This is
  the fiddly, version-sensitive part; the symptom of getting it wrong is *"current style does
  not support customization of this control"* or *"module not installed"*.
- **`CONFIRM-3`** — real repo directory paths and module import names.
- **`CONFIRM-4`** — the curated list of ~50 Bootstrap glyph names.
- **`CONFIRM-5`** — current plugin discovery/mounting (`gremlin/plugin_manager.py`,
  `qml/ActionNode.qml`) — how a plugin's QML view + Python logic are found and how the model is
  injected as `required property var action`.

**Out of scope:** the `AxesStateSeries` 8-colour data-series palette; hot reload; screenshot
tests; OS light/dark following.

## 11. Source-document reconciliation — check the repo, not the prose

The design docs were reconciled against the code on 2026-07-23. The contradictions below are now
resolved in the guide/spec/phase docs, but the underlying facts are worth keeping in view — and if
you find prose that still disagrees, trust the code:

- **Naming — settled. `Kobold` is authoritative.** The stale `Gremlin.Foundation` /
  `Gremlin.Controls` names and the old style name `Instrument` are purged from the guide.
  **Do not over-purge:** the *application* is still Joystick Gremlin. The `gremlin/` Python package,
  `gremlin/config.py`, `gremlin/plugin_manager.py`, `gremlin/ui/`, `joystick_gremlin.py` and the
  product name are all correct and stay. Only the **style and QML module namespace** is Kobold.
- **`Kobold` means two things — one directory.** The control templates sit **directly** in
  `style/qml/Kobold/`; the submodules (`Foundation` / `Controls` / `Composites` / `Views`) are
  subdirectories beneath it — exactly as `QtQuick` / `QtQuick.Controls`. `QQuickStyle.setStyle("Kobold")`
  finds the templates; the submodule dirs do not shadow them.
- **`ThemeManager` is a context property.** Plain `QObject` exposed as `themeManager` via
  `setContextProperty`, not a `@QmlSingleton`; `Theme.qml`/`Metrics.qml` bind to it, and `uiScale`
  lives on it (no separate `Config`).
- **`Metrics.pick()` tables are integer-keyed** (`{100, 150, 200}`), the `15%` → 150% typo is fixed,
  and `Metrics` carries a fourth hand-controlled exception, `accentMark`.
- **Placement + naming:** generic QQC2-adjacent controls (`MenuBar`, `SplitView`, `ToolButton`) are
  style templates in `style/qml/Kobold/`; custom components split into `Kobold.Controls` (leaves,
  e.g. `Chip`) and `Kobold.Composites` (assemblies, e.g. `ActionRow`/`SlotHeader`), with app-only
  shell furniture (`InputButton` — there is no `InputRow` — and friends) in `Kobold.Views`.
  Top-level `qml/` no longer exists.

## 12. Working principles for an agent on this codebase

- **Never silently resolve an ambiguity in the spec.** Flag it and ask.
- **When a Qt API is version-specific or you are unsure, verify against the official Qt 6.11
  documentation before writing it.** Do not invent API names, enum values or signatures. If you
  cannot verify, stop and say so.
- Treat a rule violation as a **build defect**, not a style opinion.
- Prefer the smallest change that satisfies the spec. The design is deliberately austere;
  additions ("a subtle shadow", "grey out the inactive tab", "an icon would help here") are
  almost always the thing the spec explicitly rejected.
- New components get a **gallery section** in the playground. That is where verification lives.
