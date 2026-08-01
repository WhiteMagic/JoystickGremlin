# Joystick   — New UI Style & Theming
## Implementation Guide & Claude Code Handoff

> **Status:** architecture locked. This document is the source of truth for implementing the
> new UI style/theming system. It is written to be handed to an LLM (Claude Code) one *phase*
> at a time, with §0–§5 always loaded as context.
>
> **Companion files:**
>
> -  `jg_style_design_specification.md` (the visual spec). This guide references
>   it by section as `SPEC §n`. **Keep both files in the repo.** Where they disagree, the spec
>   wins on *visual* rules; this guide wins on *architecture*.
> - `jg_style_mockup.html` a partially functional prototype visualizing some of the intents described in the above visual design specification.
>
> **Companion skills:**
> - `comment-code` — add code comments/docstrings or reword existing ones to match this
>   codebase's terse, human-written style.
> - `py-modernize` - containts the rules of the code base with regards to Python and QML idioms to use.
> - `ama` — ask-me-anything use this to resolve uncertainty and gain information from the user.

---

## 0. How to use this document

- **Always load §0–§5** (context, rules, token contract, architecture, domain model) before
  working on any phase. They are short by design.
- **To work a phase:** "Implement Phase N from the implementation guide." Each phase in §6 lists
  its goal, dependencies, deliverables, what it consumes/exposes, and a **Definition of Done (DoD)**.
- **Do not start a phase whose dependencies are unmet.**
- **When a Qt API is version-specific or you are unsure, verify it against the official Qt 6.11
  documentation before writing it. Do not invent API names, enum values, or signatures.** If you
  cannot verify, stop and flag it (see §8).
- **Never silently resolve an ambiguity in the spec.** Flag it (see §8).

---

## 1. Context & philosophy — READ FIRST

**What it is.** A Windows desktop utility for remapping HOTAS hardware. Power users bind 100–200
inputs across 4–6 devices, in long sessions, beside a game. **It is an instrument, not a product:
dense, literal, calm.** No onboarding, no delight, no marketing UI. Identity is carried by the
*organisation of data*, not by colour or typeface.

**Stack.** PySide6 + QML (Qt Quick), **targeting Qt/PySide6 6.11**. Windows-first.

**Approach.** A **fully custom Qt Quick Controls 2 style** (our own control templates), driven by
a small set of singletons for colour, dimensions, and type. Themes are colour-only data files.
Dimensions/type/icons are fixed design constants, not themeable.

**The five hard rules (SPEC §2) — these are inviolable:**

- **R1 — Layout is static.** Nothing appears/disappears/moves/resizes on hover. Hover may only add
  an overlay that is a *superset* of what's already on screen. *One* sanctioned exception: the
  action-name field's border (SPEC §8).
- **R2 — No shadows, ever.** Floating surfaces = 1px border + opaque fill. No elevation, blur,
  translucency.
- **R3 — No derived colours.** Every colour is a named token or it's a bug. No alpha, no tints,
  no `color-mix`.
- **R4 — Accent = state only, never a fill.** No primary button anywhere. Nothing ever sits *on*
  accent, so there is no `accentFg` token.
- **R5 — Everything visible at once.** No accordions, wizards, drawers, "advanced" sections, or
  overflow menus.

---

## 2. Non-negotiable conventions (the LLM must never violate)

These are mechanically checkable (§7). Treat a violation as a build defect.

1. **Colours come only from the `Theme` singleton.** No raw hex anywhere except inside the shipped
   scheme JSON files. No `Qt.rgba`, no alpha, no `Qt.lighter/darker`, no `Qt.tint`, no `color-mix`.
2. **Dimensions come only from the `Metrics` singleton.** No raw px literals in styling positions
   (size, spacing, margins, radius, border width, font size). The **2px grid**: every dimension is
   even and integer at 100% *and* 150% zoom. The **only** accepted non-integer-at-150% is a 1px
   border (SPEC §4).
3. **No `layer.effect` shadows, gradients, `Qt.rgba(`, `opacity` used for tinting, or `color-mix`.**
   (`opacity` for genuine show/hide of an already-present element is fine; opacity as a colour
   derivation is not.)
4. **Font sizes ∈ {12, 14} only. Pixels, never points.** Weights **400 and 600 only**. No italic,
   no bold — emphasis is SemiBold (600). Sizes come from `Metrics`; family/weight from `FontType`.
5. **Accent is state only** (selection, focus, the checkbox/radio *mark*, the engaged-toggle icon
   shade, tab underline, selected-row bar). Never a filled background. ~2–4 accent marks on screen
   at any time.
6. **All scheme file IO goes through `QFile`/`QDir`.** Never Python `open()`/`glob` for schemes —
   `QFile` resolves both `:/…` (qrc) and real filesystem paths; `open()` does not.
7. **Plugins import `Kobold.Foundation`, `Kobold.Controls` and `Kobold.Composites` — never
   `Kobold.Views`.** `Kobold.Views` is app-only shell furniture; plugins never import it. Allowed
   framework imports beyond that: `QtQuick`, `QtQuick.Controls`, `QtQuick.Layouts`, `QtQuick.Shapes`,
   `QtQuick.Window`, `QtQuick.Dialogs`, `Qt.labs.qmlmodels` (plugins may open their own dialogs).
   Allowed `Gremlin.*` imports: `Gremlin.ActionPlugins`, `Gremlin.Profile`. Context properties
   (`backend`, `uiState`, `signal`, `themeManager`) are a sanctioned global API available at every
   tier, plugins included. Component names must **not** collide with `QtQuick.Controls` type names
   (no `Button`, `CheckBox`, `ComboBox` in `Kobold.Controls`) as these are provided by the base
   style being created.
8. **The core owns the action-tree grammar; a plugin supplies only its config *body*.**
9. **Verify version-specific Qt APIs against docs; flag unknowns; never invent.**

---

## 3. The token contract (reference data)

### 3.1 Colour — exactly 11 tokens (SPEC §3)

| token | role |
|---|---|
| `bg` | base/window surface; action-tree bg; input rows |
| `bgAlt` | recessed vs `bg` in **both** themes; control fills, popup fill, left-pane well |
| `bgHover` | hover fill |
| `bgSelected` | selected fill |
| `line` | every 1px: borders, separators, control borders, indent guides, slot rules, drag line |
| `fg` | primary text: identifiers, action labels, values |
| `fgMuted` | secondary: descriptions, slot labels, units |
| `fgDisabled` | disabled, empty states |
| `accent` | **selection + focus only** |
| `error` | invalid-action icon, error hints |
| `warning` | warning hints |

> `AxesStateSeries` needs a separate 8-colour data-series palette. **Out of scope** — do not fold
> it into these 11.

**Shipped defaults** (bundle both as qrc scheme files):

```
light: bg #ffffff  bgAlt #f2f2f4  bgHover #e8e8ec  bgSelected #dcdce2  line #c4c4cc
       fg #17171a  fgMuted #6a6a74  fgDisabled #a6a6b0
       accent #1060c0  error #c0281c  warning #9a5c00
dark:  bg #242429  bgAlt #1b1b1e  bgHover #2e2e34  bgSelected #3a3a42  line #4a4a54
       fg #e6e6ea  fgMuted #94949e  fgDisabled #5c5c66
       accent #58a6ff  error #ff7b6b  warning #e0a63c
```

### 3.2 Dimensions & scaling (SPEC §4)

Scaling is **pure zoom** at **100 / 150 / 200 %** — every dimension multiplies. Implemented as
**multiplied integer tokens**, never a scene-graph transform or `QT_SCALE_FACTOR`. Logical zoom is
orthogonal to OS DPI (Qt's high-DPI pipeline handles physical pixels).

Base constants (at 100%):

| | value | | | value |
|---|---|---|---|---|
| grid | 2px | | menu bar | 26 |
| gaps | 4 / 8 / 12 only | | toolbar | 34 |
| body text | 14px | | tab strip | 36 |
| detail text | 12px | | footer | 24 |
| control height | **24px (one height, app-wide)** | | body | 780 |
| icon | 16px | | window | 1400×900 |
| indent/level | 16px | | left pane min | 400 |
| border | 1px (accepted non-integer at 150%) | | right pane min | 900 |
| radius | 2px interactive only; containers 0 | | input row | 48 (+4 gap = 52 pitch) |
| | | | action row | 28 |

### 3.3 Type (SPEC §5)

**IBM Plex Sans + IBM Plex Mono** (SIL OFL 1.1), bundled OTF/TTF in qrc. Weights **400 and 600**.
Mono only for character-cell/fixed-width readouts (spin values, axis values, thresholds, GUIDs,
VID/PID). Row titles and key combos stay Sans.

### 3.4 Scheme file shape

```jsonc
{
  "meta": { "name": "Kobold Dark", "appearance": "dark" },   // appearance ∈ {light,dark}, optional
  "colors": {
    "bg": "#242429", "bgAlt": "#1b1b1e", "bgHover": "#2e2e34", "bgSelected": "#3a3a42",
    "line": "#4a4a54", "fg": "#e6e6ea", "fgMuted": "#94949e", "fgDisabled": "#5c5c66",
    "accent": "#58a6ff", "error": "#ff7b6b", "warning": "#e0a63c"
  }
}
```

**JSON Schema** (`themes/scheme.schema.json`): all 11 keys `required`, `additionalProperties:false`,
each colour `"pattern": "^#[0-9a-fA-F]{6}$"` (**6-digit; alpha rejected**), `meta.appearance` an enum
of `light`/`dark`. The schema is both editor-autocomplete and a lint input. A **load-time validator**
enforces the same rules at runtime and fails loud (never half-load, never silently fall back to a
partial scheme).

---

## 4. Target architecture

### 4.1 Colour theming

- **`ThemeManager` (Python, `QObject`)** — single source of truth. Owns scheme
  discovery, load, validation, and the *active* scheme. Exposes **11 named `Property(QColor, …,
  notify=changed)`** + one `changed` signal, plus a `uiScale` property (100 | 150 | 200) that
  `Metrics` reads. Reads/writes the selected scheme id **through the existing
  configuration-management class**, not by touching JSON directly.
- **Exposed to QML as a context property**, not a QML singleton: the Python entry point calls
  `engine.rootContext().setContextProperty("themeManager", theme_manager)`. It is **not** an
  `@QmlElement`/`@QmlSingleton` type. This is the one sanctioned context property in the style;
  every colour consumer reaches it only through the `Theme` facade below.
- **`Theme` (QML, `pragma Singleton`, in the Foundation module `qmldir`)** — thin facade:
  `readonly property color bg: themeManager.bg` ×11. **Every consumer and every plugin reads
  `Theme` only.** This keeps thousands of consumer reads QML-side; only 11 facade bindings read the
  context property, and only on `changed`. (`Metrics` is the lone exception that reads
  `themeManager.uiScale` directly — a dimension driver, not a colour.)
- **Live switch** = `ThemeManager` swaps the active scheme dict → `emit changed()` → all facade
  bindings recompute → all consumer bindings recompute. No per-property signals; one `changed`.
- **Appearance: manual only.** A single scheme id, persisted via the config class. On startup,
  resolve it; if missing/invalid, fall back to a shipped default and log. No OS-follow, no
  `colorSchemeChanged` listener.
- **Title bar:** when a scheme is selected, call `QGuiApplication.styleHints().setColorScheme(...)`
  from `meta.appearance` so the native Windows frame matches (best-effort; content is unaffected).

Sketch:

```python
# theme_manager.py  (plain QObject; exposed via setContextProperty, not @QmlSingleton)
_TOKENS = ("bg","bgAlt","bgHover","bgSelected","line",
           "fg","fgMuted","fgDisabled","accent","error","warning")

class ThemeManager(QObject):
    changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._c = {}                      # token -> QColor
        # discovery + load happen here, via QFile/QDir over a roots list (see 4.4)
    def _get(self, name): return self._c[name]
    # 11 identical Property declarations, all notify=changed:
    bg     = Property(QColor, lambda s: s._c["bg"],     notify=changed)
    accent = Property(QColor, lambda s: s._c["accent"], notify=changed)
    # ... etc for the remaining 9 ...
    uiScale = Property(int, lambda s: s._ui_scale, notify=changed)  # 100 | 150 | 200
```

```qml
// Theme.qml   (pragma Singleton; registered in qmldir: `singleton Theme Theme.qml`)
// Reads the `themeManager` context property directly — no import needed for it.
pragma Singleton
import QtQuick
QtObject {
    readonly property color bg:         themeManager.bg
    readonly property color accent:     themeManager.accent
    // ... 9 more ...
}
```

### 4.2 Dimensions & scaling — `Metrics` (QML singleton)

QML-owned (no file logic). `scale ∈ {100%, 150%, 200%}` driven by `themeManager.uiScale`.
**Policy functions + per-token override tables.** Consumers read **named tokens**, never call the
policy functions. `scalePercentage` is integer (100 | 150 | 200) so the `pick()` override tables key
by integer — no floating-point map lookups.

```qml
// Metrics.qml  (pragma Singleton) — reads the `themeManager` context property directly
pragma Singleton
import QtQuick
QtObject {
    readonly property int scalePercentage: themeManager.uiScale // 100 | 150 | 200
    readonly property real scale: scalePercentage / 100.0

    // policies — pick one per token
    function dp(x)   { return Math.round(x * scale) }      // default, grid-following
    function even(x) { let v = Math.round(x*scale); return v % 2 ? v + 1 : v }
    function pick(m) { return m[scalePercentage] }           // explicit per-zoom, no math

    // dimension tokens
    readonly property int  rowInput:      dp(48)
    readonly property int  rowAction:     dp(28)
    readonly property int  ctrlH:         dp(24)
    readonly property int  indent:        dp(16)
    readonly property int  icon:          dp(16)
    readonly property int  gapS:          dp(4)
    readonly property int  gapM:          dp(8)
    readonly property int  gapL:          dp(12)
    readonly property int  radius:        dp(2)
    readonly property int  markSize:      dp(16)  // checkbox box / radio ring diameter
    // font pixel sizes (family/weight live in FontType)
    readonly property int  textBody:      dp(14)
    readonly property int  textDetail:    dp(12)
    // hand-controlled exceptions (integer-keyed pick tables)
    readonly property real hairline:      pick({ 100: 1, 150: 1, 200: 2 })
    readonly property real insertionLine: pick({ 100: 2, 150: 2, 200: 4 })
    readonly property real accentMark:    pick({ 100: 2, 150: 2, 200: 4 })  // tab underline, selected-row bar
    readonly property int  indentGuide:   pick({ 100: 1, 150: 2, 200: 2 })
    // shell heights, pane minimums, etc. — add per SPEC §4/§10
}
```

**Performance note (already reasoned through):** token bindings are cached properties; `dp()`/`pick()`
run only on scale change, not per frame or per delegate. Consumers reading `Metrics.rowInput` do a
cheap leaf-property read — safe under delegate recycling. Do **not** call `Metrics.dp(48)` in a
delegate; read the named token.

### 4.3 Type — `FontType` (QML singleton) + Python loading

- **Python:** `QFontDatabase.addApplicationFont(":/fonts/…")` at startup for every bundled face
  (both families, weights 400 & 600). Assert each load succeeds; set IBM Plex Sans as the app
  default font. **Bundle real 600 faces** (no synthetic bold).
- **`FontType` (QML singleton):** `sans`, `mono` (family strings), `regular` (400), `semiBold` (600).
  Sizes stay in `Metrics`. Consumers compose:
  `font.family: FontType.sans; font.pixelSize: Metrics.textBody; font.weight: FontType.semiBold`.

### 4.4 Icons — image provider + `AppIcon`

- **`IconProvider` (Python `QQuickImageProvider`)** answering `image://icon/<name>?c=<hex>&px=<size>`:
  load the SVG bytes **via `QFile`** (qrc/user/plugin — same roots idea), **string-substitute
  `currentColor` → the resolved token hex**, render with `QSvgRenderer` to a `QImage` at
  `px × devicePixelRatio`, cache by `(name, hex, px, dpr)`.
  Rationale: Qt's SVG renderer does **not** resolve `currentColor`, and `IconImage`/`ColorImage`
  were removed in 6.9 — so we recolour the data ourselves. This depends on none of those features.
- **`AppIcon` (QML component)** — the only icon consumers use. Resolves `role` → the live `Theme`
  token and **binds the URL to it**, so recolour rides the binding graph (no imperative refresh):

```qml
// AppIcon.qml
import QtQuick
import Kobold.Foundation
Image {
    id: root
    property string name
    property string role: "fg"            // fg | fgMuted | fgDisabled | accent | error | warning
    readonly property color _c:
          role === "fgMuted"   ? Theme.fgMuted
        : role === "fgDisabled"? Theme.fgDisabled
        : role === "accent"    ? Theme.accent
        : role === "error"     ? Theme.error
        : role === "warning"   ? Theme.warning
        :                        Theme.fg
    sourceSize: Qt.size(Metrics.icon, Metrics.icon)
    width: Metrics.icon; height: Metrics.icon
    cache: true
    source: "image://icon/" + name + "?c=" + _c.toString().slice(-6) + "&px=" + Metrics.icon
}
```

Bootstrap Icons 1.13.1 (MIT), 16×16 viewBox, filled, single colour. **~50 curated glyphs**. Plugin authors ship SVGs to the same convention. Chips carry no icons.

### 4.5 The custom QQC2 style

- A directory of control templates, each rooting the matching `QtQuick.Templates` type, styling only
  `background`/`contentItem`/`indicator` from `Theme`/`Metrics`/`FontType`/`AppIcon`.
- **Registration:** `QQuickStyle.setStyle("Kobold")` (or a resource path) **before** the engine
  loads any Controls-importing QML — the style cannot change after QML types register. `Basic` is the
  fallback for controls we don't implement (`QQuickStyle.setFallbackStyle("Basic")`).
- **Packaging caveat:** the style dir must be discoverable on the QML import path /
  resource system. A common PySide6 failure ("current style does not support customization of this
  control") means the qrc/module wasn't registered. Confirm the exact 6.11 packaging (name-matched
  dir on import path vs. QML module) against *Qt Quick Controls → Creating a Custom Style* before
  finalising. Can use the `self.engine.addImportPath(...)` directive to make the style discoverable.
- Controls to implement (initial set): `Button`, `ToolButton`, `CheckBox`, `RadioButton`,
  `Menu` + `MenuItem`, `MenuBar` + `MenuBarItem`, `ComboBox` (the real value-selector `▾`),
  `TextField`, `SpinBox`, `DoubleSpinBox`, `ScrollBar`, `TabBar`, `TabButton`, `Slider`, `SplitView`,
  `ToolTip`, `Label`/Text conventions. (The action-selector menu-button and toggle buttons per
  SPEC §7 may be app components, not restyled primitives — decide during Phase 2.)
- **Placement rule:** generic, QQC2-adjacent controls (including `MenuBar`, `SplitView`, `ToolButton`)
  live here as style templates in `style/qml/Kobold/`; custom single-purpose components split further
  by the `Controls`/`Composites`/`Views` rule in §4.6 — a leaf like `Chip` sits in `Controls`, an
  assembly like `ActionRow`/`SlotHeader` sits in `Composites`, and app-only shell furniture like
  `InputButton`/`BindingHeader` sits in `Views` (§4.6).

### 4.6 Modules & boundary

Four tiers, in dependency order (each `qmldir` re-exports the tier below it, so a plugin body only
ever writes `import Kobold.Controls` and gets `Foundation` along for free; a container plugin writes
`import Kobold.Composites` and gets `Controls` + `Foundation`):

- **`Kobold.Foundation`** — the QML singletons `Theme`, `Metrics`, `FontType`, `AppIcon`. Shared by
  everything. (`ThemeManager` is the Python source of truth behind `Theme`, exposed as the
  `themeManager` context property — see §4.1; `uiScale` lives on it, not on a separate `Config`.)
- **The Kobold style** — control templates (consumed implicitly via `import QtQuick.Controls`).
  Generic, QQC2-adjacent controls that are not stock QQC2 types (`MenuBar`, `SplitView`, `ToolButton`)
  also live here.
- **`Kobold.Controls`** — leaves: components that instantiate nothing else from the `Kobold`
  namespace (`Chip`, `TreeIndent`, `ActivationToggle`, `ScrollList`, `Divider`, `Spacer`, …), plus
  the re-exported `Foundation` singletons and `AppIcon`. The *public plugin surface*, alongside
  `Composites`.
- **`Kobold.Composites`** — assemblies of `Kobold` types with no app state (`ActionNode`,
  `ActionRow`, `SlotHeader`, `ActionStepTable`, `ActivationBehavior`). Also plugin-importable: a
  plugin with its own nested action containers (Chain, Condition, Tempo, …) instantiates `ActionNode`
  directly for its children.
- **`Kobold.Views`** — app-only shell furniture (`Main`, `InputButton`, `BindingHeader`,
  `DeviceInputList`, the option/config dialogs, …): instantiated once by the application or once per
  device/input and positioned by the shell, never a reusable element a plugin could drop into its own
  body. Churns freely. **Plugins never import this tier.**

**`Controls` vs `Composites` — the split rule:** does the file instantiate another type from the
`Kobold` namespace? No → `Controls`. Yes → `Composites`. Mechanically checkable, so misfiling is a
lint-detectable drift rather than a taste judgment (D4 in the reorganisation decisions).

**`Views` is on a different axis** — contract, not structure. Structurally its members are
composites; they're separated because plugins must never import them. Enforcement lives on the
*importing* side: `action_plugins/**/*.qml` must not import `Kobold.Views`.

Type names in every tier must not collide with `QtQuick.Controls`.

### 4.7 Repo layout

One `Kobold/` directory holds both the style and the submodules: the control templates sit in it
directly, the submodules are subdirectories beneath it (exactly as `QtQuick` / `QtQuick.Controls`).
`qml/` no longer exists — everything that used to live there was either deleted or moved into a
`Kobold` tier below (see the reorganisation decisions doc for the full disposition).

```
gremlin/ui/
├── theme_manager.py     (plain QObject; exposed via setContextProperty("themeManager", …))
├── icon_provider.py     (QQuickImageProvider; registered on the engine at startup)

style/
├── qml/                            ← QML import ROOT (engine.addImportPath points here)
│   └── Kobold/                     ← THE STYLE: control templates sit here directly …
│       ├── qmldir                  (style manifest; Basic is the fallback for anything absent)
│       ├── Button.qml  CheckBox.qml  RadioButton.qml  ComboBox.qml  Menu.qml  MenuItem.qml
│       ├── MenuBar.qml  MenuBarItem.qml  TextField.qml  SpinBox.qml  ScrollBar.qml
│       ├── TabBar.qml  TabButton.qml  ToolTip.qml  ToolButton.qml  SplitView.qml  Label.qml
│       │                             (selected via QQuickStyle.setStyle, not imported)
│       ├── Foundation/             ← import Kobold.Foundation
│       │   ├── qmldir
│       │   ├── Theme.qml           (pragma Singleton facade over `themeManager`)
│       │   ├── Metrics.qml         (pragma Singleton)
│       │   ├── FontType.qml        (pragma Singleton)
│       │   └── AppIcon.qml
│       ├── Controls/               ← import Kobold.Controls  (leaves; PUBLIC plugin kit)
│       │   ├── qmldir              (imports Kobold.Foundation)
│       │   ├── Chip.qml  TreeIndent.qml  ActivationToggle.qml  ScrollList.qml
│       │   ├── Divider.qml  Spacer.qml  NumericRangeSlider.qml  HatDirectionToggle.qml
│       │   └── …leaves…            (re-exports Foundation singletons + AppIcon)
│       ├── Composites/             ← import Kobold.Composites  (assemblies; PUBLIC plugin kit)
│       │   ├── qmldir              (imports Kobold.Controls)
│       │   ├── ActionNode.qml
│       │   ├── ActionRow.qml
│       │   ├── SlotHeader.qml
│       │   ├── ActionStepTable.qml
│       │   └── ActivationBehavior.qml
│       └── Views/                  ← import Kobold.Views  (app-only; plugins MUST NOT import)
│           ├── qmldir              (imports Kobold.Composites; flat, no subdirectories)
│           ├── Main.qml
│           ├── InputButton.qml
│           ├── BindingHeader.qml
│           ├── DeviceInputList.qml
│           ├── DeviceTabBar.qml  DeviceList.qml
│           ├── Dialog*.qml  Option*.qml  Config*.qml
│           └── helpers.js          (declared as a JS resource in this qmldir)
├── playground/                     ← gallery app (Phase 7 of this guide); its own main.qml
├── assets/
│   ├── icons/*.svg                 ← Bootstrap glyphs (bundled in qrc)
│   └── fonts/*.otf                 ← IBM Plex 400/600 (bundled in qrc)
├── themes/                         ← light.json, dark.json, scheme.schema.json (shipped → qrc)

test/unit/                          ← test_style_lint.py, test_metrics.py, test_theme_manager.py
```

**Module → import → contents (the map at a glance):**

| Import name                | Disk (under import root) | Holds                                      | Consumed by                                               |
| -------------------------- | ------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| `Kobold.Foundation`        | `Kobold/Foundation/`      | `Theme`/`Metrics`/`FontType`/`AppIcon`      | everything                                                  |
| `Kobold.Controls`          | `Kobold/Controls/`        | leaves — no `Kobold`-type children          | everything above, **plugins**                               |
| `Kobold.Composites`        | `Kobold/Composites/`      | assemblies of `Kobold` types, no app state  | app views, **plugins** (container plugins)                  |
| `Kobold.Views`             | `Kobold/Views/`           | app-only shell furniture                    | app only (never plugins)                                    |
| *(the style)* `Kobold`     | `Kobold/` (files direct)  | QQC2 control templates + generic controls   | implicit via `QtQuick.Controls` + `QQuickStyle.setStyle`    |

**Example `qmldir`** (`Kobold/Foundation/qmldir`) — the QML singletons need explicit entries. `ThemeManager` is *not* here: it is a Python `QObject` reached through the `themeManager` context property (§4.1), and `Theme.qml` is the QML-side facade over it:

```
module Kobold.Foundation
singleton Theme     Theme.qml
singleton Metrics   Metrics.qml
singleton FontType  FontType.qml
AppIcon             AppIcon.qml
```

**Startup wiring** (Python entry point — order matters):

python

```python
app = QGuiApplication(sys.argv)

# 1) style BEFORE any Controls-importing QML loads (§4.5)
QQuickStyle.setStyle("Kobold")
QQuickStyle.setFallbackStyle("Basic")

# 2) load fonts, register the image provider
load_fonts()                                  # QFontDatabase.addApplicationFont(...)
engine = QQmlApplicationEngine()
engine.addImageProvider("icon", IconProvider())

# 3) make the import root discoverable, and expose the Python source-of-truth as a
#    context property so Theme.qml / Metrics.qml can bind to it.
engine.addImportPath("qrc:/style/qml")              # or the on-disk import root
theme_manager = ThemeManager()
engine.rootContext().setContextProperty("themeManager", theme_manager)

engine.load("qrc:/qml/main.qml")
```

> **`CONFIRM-2` reminder:** the exact PySide6 6.11 registration wiring — mixing `@QmlElement` Python types and `qmldir`-declared QML singletons under one import name, and getting the qrc/import paths right — is the fiddly part and has version-sensitive gotchas (a mis-set import path yields the "current style does not support customization" warning, or "module not installed"). Verify the precise incantation against *Qt Quick Controls → Creating a Custom Style* and *Qt Qml → Registering Types* for 6.11 before finalising, rather than treating the snippet above as exact.



---

## 5. Domain model the UI renders (SPEC §1, §8)

- **Action** — the one node type: editable name + type configuration + N named slots holding nested actions. Slot counts are dynamic (Condition 2, Tempo 2, Hat 4/8, Chain N, Map-to-vJoy 0).
- **RootAction is invisible** — no config, no indent. Top-level actions sit at **depth 0**.
- **Library owns config; inputs hold references.** One action can be referenced by two roots
  (native sharing / multi-input actions). Format is fixed — do not change it.
- **Macro steps are NOT child actions** — render as a table, never as nesting.
- **Tree grammar (core-owned):** an action's config, slot headers, and child actions sit one 16px
  step in from its header, sharing one 1px guide. **Config comes first and is unlabelled** ("what's
  under the header"). A **slot header** is the only thing that says "actions live below me."
  **A guide exists only to group child actions — no children, no guide** (but reserve the 1px as a
  transparent border so alignment/evenness holds). Guides are a map of where branching is.
- **Align within an action, not across** — no global label column; raggedness across actions is
  accepted.
- **Plugin supplies only the config body.** The core draws chevron, type icon (= drag handle),
  header, name field, trigger/error/remove, slot headers, guides, indentation, drag-drop.

---

- ## 6. Phases

  > Each phase: **Goal · Depends on · Deliverables · Consumes/Exposes · DoD · Spec refs · Watch-outs.** Phases 1–2 land together in practice but are separable work chunks. Do them in order.
  >
  > **Every phase has a dedicated detailed document in `phases/`** — the entries below are summaries. When working a phase, hand the LLM its detailed doc *plus* this guide's §0–§5. The detailed docs explain the concepts (e.g. what "facade", "template", "guide" mean) that these summaries assume.

  ### Phase 1 — Foundation

  > **Detailed doc:** `phases/phase_1_foundation.md`

  - **Goal:** tokens + assets available to QML.
  - **Depends on:** nothing.
  - **Deliverables:** `ThemeManager.py` (11 tokens + `changed`, scheme discovery/load/validate over a `QFile`/`QDir` roots list = `[":/themes"]`), `Theme.qml` facade, `Metrics.qml`, `FontType.qml`, font loading in the Python entry point, `IconProvider` + `AppIcon.qml`, `themes/light.json`, `themes/dark.json`, `scheme.schema.json`, `Kobold.Foundation` `qmldir`.
  - **Exposes:** `Theme`, `Metrics`, `FontType`, `AppIcon`.
  - **DoD:** a throwaway QML page shows a rectangle in each of the 11 tokens, text in Sans+Mono at 12/14 in 400/600, and one `AppIcon` that recolours when the active scheme is swapped from Python. Load-time validator rejects a deliberately malformed scheme with a clear error. All scheme IO via `QFile`.
  - **Spec refs:** §3, §4, §5, §6.
  - **Watch-outs:** conventions §2.1/§2.4/§2.6; never `open()` a scheme; assert font loads.

  ### Phase 2 — Custom QQC2 style (basic controls)

  > **Detailed doc:** `phases/phase_2_style.md`

  - **Goal:** every basic control renders in the new look app-wide.
  - **Depends on:** Phase 1.
  - **Deliverables:** the Kobold style dir (control templates in §4.5), `QQuickStyle.setStyle` wired **before** engine load, `setFallbackStyle("Basic")`, qrc/import-path registration.
  - **Consumes:** Foundation. **Exposes:** the active style (implicit).
  - **DoD:** each implemented control renders from tokens across both themes and all three zooms, with correct states (rest/hover/pressed/checked/focused/disabled/error). Checkboxes/radios show **accent mark, never a filled box** (R4). No shadows/gradients (R2/§2.3). Focus outline is `2px, offset -2px` accent.
  - **Spec refs:** §7, §2 (R1/R2/R4).
  - **Watch-outs:** `CONFIRM-2` packaging; the action-selector menu-button (SPEC §7) is *not* a combo.

  ### Phase 3 — Playground + lint

  > **Detailed doc:** `phases/phase_3_playground.md`

  - **Goal:** permanent verification harness + CI lint.
  - **Depends on:** Phases 1–2.
  - **Deliverables:** a gallery app rendering every control × states × **both themes** × **three zooms**, with theme/zoom toggles; the §7 lint scripts wired into CI; the Metrics-resolution test; the scheme-schema test.
  - **DoD:** gallery runs; a human can sign off visually; lint fails on a planted raw hex / odd px / shadow; Metrics test fails on a planted 13px token.
  - **Spec refs:** §12.
  - **Watch-outs:** no screenshot tests yet (deferred, §7). Gallery is first-class, not throwaway.

  ### Phase 4 — Left pane (input list)

  > **Detailed doc:** `phases/phase_4_left_pane.md`

  - **Goal:** SPEC §9 left pane.
  - **Depends on:** Phases 1–3.
  - **Deliverables:** `InputButton` (48px, identifier always-in-full + right-aligned 12px `fgMuted` description, chips row with render-all-then-`+n`-on-true-overflow), `bgAlt` recessed well, rows = `bg` + 1px `line` + 2px radius + 8px side margin + 4px gap, selection = `bgSelected` + 2px accent left bar.
  - **DoD:** an unbound row is a complete 48px row (not truncated); chips never abbreviate; `+n` only on measured overflow; description = accumulated *modified* action names only.
  - **Spec refs:** §9.
  - **Watch-outs:** description and chips never duplicate; hover popup is future work — reserve, don't build.

  ### Phase 5 — Surrounding structure (shell)

  > **Detailed doc:** `phases/phase_5_shell.md`

  - **Goal:** SPEC §10 menu/toolbar/tabs/footer + split layout.
  - **Depends on:** Phases 1–3.
  - **Deliverables:** menu bar (26), toolbar (34) with `Configuring mode` control kept in place, tab strip (36) as one exclusive selection set (device tabs + Scripts/Settings, 1px vertical rule between groups), footer (24) `State · Editing · Running`.
  - **DoD:** active tab = 2px accent underline + SemiBold + `bgSelected`; no greying of inactive tabs; no icons on tabs; never accent-filled. Footer shows adjacency with no divergence warning/icon/tone.
  - **Spec refs:** §10.

  ### Phase 6 — Action-tree scaffolding

  > **Detailed doc:** `phases/phase_6_action_tree.md`

  - **Goal:** the core-owned tree grammar (SPEC §8), *without* plugin bodies yet.
  - **Depends on:** Phases 1–3 (2 for controls used within).
  - **Deliverables:** `ActionRow` (28px: chevron, type-icon-as-drag-handle, name-as-plain-text with transparent border taking `line`+`bgAlt` on hover, trigger/error/remove), `SlotHeader` (24px: 12px `fgMuted` label · 1px `line` rule · `Add action ▾` chrome-on-hover-only), guides (present only with children; transparent 1px reserved otherwise), binding header, sequence separation (8px space + padding, **no rule between sequences**), drag-drop (grab type icon, row-edge band hit-test, 2px `line` insertion line, no parting animation).
  - **DoD:** "cover the labels" test passes — you can still point at where each slot starts; guides map exactly the branching; the action row has **no** full-width hover band (only the name field's border reacts — the one R1 exception).
  - **Spec refs:** §8.
  - **Watch-outs:** depth 0 has no indent; RootAction invisible; Macro steps render as a table.

  ### Phase 7 — Actions / plugin config views (reflow over time)

  > **Detailed doc:** `phases/phase_7_plugins.md`

  - **Goal:** migrate the plugin config bodies.
  - **Depends on:** Phases 1–6, and `Kobold.Controls` finalised.
  - **Deliverables:** `Kobold.Controls` public kit (within-action helpers); migrate each plugin's QML config view to consume it; the multi-input source-row pattern (SPEC §11: labelled group + N source rows; unassigned source row is a first-class state carrying its instruction; one assign widget; `activation-mode: disallowed` → no TriggerMode, reserve no space).
  - **DoD:** plugins reskin automatically from the style; residual work is **layout reflow** from the new 24px height / 2px grid, not reconstruction. Kit type names don't collide with QtQuick.Controls.
  - **Spec refs:** §7, §8 (config), §11.
  - **Watch-outs:** align within an action only; inline-sentence configs stay sentences; **flag** the §11 two-names issue (`OPEN-1`), don't fix it.

---

## 7. Verification & the §12 checks (lint spec)

**Gating in CI (now):**

- **`scripts/lint_style.py` — static grep/regex over QML** (fail on any hit):
  - hex colour literals outside `themes/*.json` → must be `Theme.*`
  - raw px in styling positions (width/height/spacing/margins/radius/border/font size) → must be
    `Metrics.*` (bare `0`, `2`, `-2` are the sanctioned literals — zero, and the fixed focus-ring
    stroke/outset)
  - `box-shadow`, `gradient`, `Qt.rgba(`, `color-mix`, `layer.effect` used for shadow, `opacity`
    used as tint
  - `pointSize` / `pt` font sizes → must be `pixelSize` from `Metrics`
  - `font.pixelSize` literals not sourced from `Metrics` → must be `{12,14}` only, via `Metrics`
  - **Scope:** the gate scans `style/qml/`, which now includes the `Views` tier (the former
    top-level `qml/`, which no longer exists — everything in it was deleted or moved). `action_plugins/*/*.qml`
    are in scope and come under the gate as Phase 7 migrates them (expect a wall of violations before
    then — treat it as the migration to-do list, not an instant hard gate).
- **Metrics-resolution unit test** (`test/unit/test_metrics.py`, separate from the lint script):
  resolve every `Metrics` token at scale ∈ {1.0, 1.5, 2.0}; assert each is an integer **or** a
  declared exception (`hairline`, `insertionLine`, `accentMark`, `indentGuide`, 1px border). Catches
  grid violations invisible to the eye.
- **Scheme-schema test** (`test/unit/test_theme_manager.py`): every shipped scheme validates against
  `scheme.schema.json`; exactly 11 colour keys; no alpha.

**Human (now):** visual inspection of the playground across both themes × three zooms × states.
Manual spec checks worth running periodically: cover-the-labels (§12.4), count accent marks ~2–4
(§12.5), hover-any-row static (§12.6).

**Not doing:** hot-reload of scheme files (`QFileSystemWatcher`) — schemes load at startup only.

---

## 8. Open / deferred items — flag, don't invent

- **`OPEN-1` (from SPEC §11):** `merge-axis` has two editable names — `label` (shared instance, in
  the combo) and `action-label` (this node, in the header). Nothing says which is which. **Ignore the user will fix at some point**
- **`CONFIRM-1` (resolved):** `ThemeManager` reads the selected scheme id from the existing config
  class, and **`uiScale` lives on `ThemeManager`** (100 | 150 | 200), reached from QML through the
  `themeManager` context property — there is no separate `Config` singleton. `Metrics` binds
  `scalePercentage: themeManager.uiScale`. See `gremlin/config.py` and `gremlin/ui/theme_manager.py`.
- **`CONFIRM-2`:** exact 6.11 packaging/registration for the custom style from qrc — verify against
  *Creating a Custom Style* before finalising Phase 2.
- **`CONFIRM-3` (resolved):** real repo directory paths and module import names — see §4.7. The
  `Kobold` module split into five tiers (`Foundation`/`Controls`/`Composites`/`Views` + the style
  itself) rather than the three originally sketched; full rationale in the QML reorganisation
  decisions doc (`doc/design/kobold_cleanup/qml_reorganisation_decisions.md`).
- **`CONFIRM-4`:** the curated list of ~50 Bootstrap icon glyphs and their names. The user will fill in once the stub stands.
- **`CONFIRM-5`:** current plugin discovery/registration mechanism (how a plugin's QML view + Python
  logic are found and mounted), to finalise Phase 7. See `gremlin/plugin_manager.py` and existing code
  such as `style/qml/Kobold/Composites/ActionNode.qml`.

**Out of scope:** the `AxesStateSeries` 8-colour data-series palette; hot reload; screenshot tests
(for now); OS light/dark following.

---

## 9. Glossary

- **Scheme** — a colour theme: one JSON file, 11 tokens + meta. Bundled (qrc) or user (`%USERPROFILE%`).
- **Token** — a named colour (`Theme.*`) or dimension (`Metrics.*`). The only legal source of a
  colour or a dimension.
- **Foundation / the Kobold style / Controls / Composites / Views** — the five module tiers (§4.6).
- **Action / slot / RootAction / library / sequence** — domain model (§5).
- **Config body** — the plugin-supplied UI under an action header; the plugin's only responsibility.
- **Tree scaffolding** — the core-drawn chevron/icon/header/slot-headers/guides/indent.
- **Playground** — the permanent gallery harness (Phase 3).
