# Phase 1 — Foundation

**Goal:** make colour, dimension, type, and icon *tokens* available to QML, loaded from data, so
every later phase can consume them. Nothing visual ships yet except a throwaway test page.

**Prereqs:** load the main implementation guide §0–§5 (context, hard rules, token contract, domain
model). **Depends on:** nothing. **Enables:** every other phase.

---

## Concepts for this phase (read before coding)

**QML singleton.** A single shared object instance that any QML file can reach by name without
creating it. `Theme`, `Metrics` and `FontType` are QML singletons (`pragma Singleton` + a `qmldir`
entry). Consumers just write `Theme.bg`, `Metrics.rowInput`, etc. — no instance to pass around. We
use singletons because colours/metrics/fonts are global and read from thousands of places.

**Source of truth vs. facade.** We split the theme into two objects on purpose:

- **`ThemeManager` (Python)** is the *source of truth*. It does the real work: find scheme files,
  parse and validate them, hold the currently-active colours, and emit a signal when they change.
  It exposes 11 colour properties (`bg`, `accent`, …), a `uiScale` property (100 | 150 | 200, read
  by `Metrics`), and one `changed` signal. **It is exposed to QML as a *context property* named
  `themeManager`** (`engine.rootContext().setContextProperty("themeManager", …)`) — a plain
  `QObject`, **not** a `@QmlSingleton`.
- **`Theme.qml` (QML) is a *facade*.** "Facade" = a thin, simple front object that stands in for a
  more complex one behind it. `Theme.qml` does no work; each of its 11 properties is just
  `readonly property color bg: themeManager.bg`. Consumers only ever touch `Theme`, never
  `themeManager` (the one exception is `Metrics`, which reads `themeManager.uiScale` — a dimension,
  not a colour).

  **Why bother with the facade instead of reading `themeManager` directly?** Two reasons:
  1. *Encapsulation* — consumers depend on a stable QML name (`Theme`), not on the Python object.
  2. *Performance* — when a QML binding like `color: Theme.bg` is evaluated (including every time a
     list delegate is recycled during scrolling), reading a QML property is cheap and stays inside
     QML. If consumers read `themeManager.bg` directly, every read crosses the Python↔QML boundary.
     With the facade, only the **11 facade bindings** cross the boundary, and only when the theme
     actually changes. Thousands of consumer reads stay QML-side. For a UI with 100–200 rows, that
     matters.

  Flow on a theme switch: `ThemeManager` swaps its active colours → emits `changed` → the 11 facade
  bindings re-evaluate → every consumer bound to `Theme.*` updates. One signal drives everything.

**Image provider.** A Python object registered on the QML engine that answers special URLs of the
form `image://<providerId>/<path>?<query>`. When an `Image { source: "image://icon/trash?c=e6e6ea" }`
renders, Qt calls your provider with `"trash?c=e6e6ea"`, and you return a pixmap. We use one to
recolour SVGs (Qt's SVG engine can't resolve `currentColor` itself), by substituting the colour into
the SVG text and rasterising.

**Roots list (scheme discovery).** A list of directories to search for scheme files. We iterate it
and read every `*.json`. In Phase 1 the list is just `[":/themes"]` (the qrc-bundled defaults). Later
a user directory is appended — one line. All reads use `QFile`/`QDir`, which transparently handle
both `:/…` (qrc) and real filesystem paths; Python's `open()` cannot read `:/…`, so **never use it
for schemes.**

---

## What you're building

### 1. `ThemeManager` (Python — the source of truth)

- A plain `QObject` (no `@QmlElement`/`@QmlSingleton`). The entry point creates one instance and
  exposes it as the context property `themeManager`
  (`engine.rootContext().setContextProperty("themeManager", theme_manager)`).
- Holds a dict `token → QColor` for the active scheme.
- Exposes **11 `Property(QColor, …, notify=changed)`** named exactly per the token table (guide §3.1),
  all backed by one `changed = Signal()`; plus a `uiScale` `Property(int)` (100 | 150 | 200).
- **Scheme discovery/loading** over a roots list using `QFile`/`QDir`:
  - `QDir(root).entryList(["*.json"])` per root; read each file's bytes with `QFile`; `json.loads`.
  - Build a registry: `id (filename stem) → {name, appearance, colors}`. Bundled vs user tracked.
- **Validation** on load (fail loud, never half-apply): exactly the 11 keys, no extras, no missing;
  each value matches `^#[0-9a-fA-F]{6}$` (6-digit; **alpha rejected**); `meta.appearance ∈ {light,
  dark}` if present. Validate against `scheme.schema.json` and/or in code; on failure, raise/log with
  the offending key and skip that scheme.
- **Active scheme selection:** read the persisted scheme id from the **existing config-management
  class** (`CONFIRM-1`); if missing/invalid, fall back to a shipped default and log. Setting the
  active scheme updates the dict and emits `changed`.
- **Title bar:** when the active scheme changes, call
  `QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Dark/Light)` from `meta.appearance`
  (best-effort on Windows; leaves content untouched).

```python
# Plain QObject — registered via setContextProperty("themeManager", …), not @QmlSingleton.
class ThemeManager(QObject):
    changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._roots = [":/themes"]           # user root appended in a later iteration
        self._schemes = {}                   # id -> parsed+validated scheme
        self._active = {}                    # token -> QColor
        self._discover()                     # QFile/QDir, validate, populate _schemes
        self._apply(self._resolve_active_id())
    # 11 properties, all notify=changed, e.g.:
    accent = Property(QColor, lambda s: s._active["accent"], notify=changed)
    # bg, bgAlt, bgHover, bgSelected, line, fg, fgMuted, fgDisabled, error, warning …
    uiScale = Property(int, lambda s: s._ui_scale, notify=changed)  # 100 | 150 | 200
```

### 2. `Theme.qml` (QML singleton — the facade)

```qml
// Reads the `themeManager` context property directly — no import needed for it.
pragma Singleton
import QtQuick
QtObject {
    readonly property color bg:         themeManager.bg
    readonly property color bgAlt:      themeManager.bgAlt
    readonly property color bgHover:    themeManager.bgHover
    readonly property color bgSelected: themeManager.bgSelected
    readonly property color line:       themeManager.line
    readonly property color fg:         themeManager.fg
    readonly property color fgMuted:    themeManager.fgMuted
    readonly property color fgDisabled: themeManager.fgDisabled
    readonly property color accent:     themeManager.accent
    readonly property color error:      themeManager.error
    readonly property color warning:    themeManager.warning
}
```
Declare it in `qmldir`: `singleton Theme Theme.qml`.

### 3. `Metrics.qml` (QML singleton — dimensions + scaling)

Implement exactly as guide §4.2: `scalePercentage: themeManager.uiScale`; policy functions
`dp`/`even`/`pick` (with integer-keyed `pick` tables); named dimension tokens; hand-controlled
exceptions (`hairline`, `insertionLine`, `accentMark`, `indentGuide`). Consumers read named tokens,
never call the policy functions. Add the shell heights and pane minimums from guide §3.2/SPEC §10.

### 4. `FontType.qml` (QML singleton) + Python font loading

- Python at startup: `QFontDatabase.addApplicationFont(":/fonts/…")` for every bundled face (IBM Plex
  Sans + Mono, weights **400 and 600**). **Assert each returns a valid id** — a silent failure means
  a system-font fallback, which breaks §5. Set IBM Plex Sans as the app default font.
- `FontType.qml`: `readonly property string sans`, `mono`; `readonly property int regular: 400`,
  `semiBold: 600`. Sizes live in `Metrics`, not here.

### 5. `IconProvider` (Python) + `AppIcon.qml`

- `IconProvider(QQuickImageProvider)`: parse `id` = `"<name>?c=<hex>&px=<size>"`; load
  `:/assets/icons/<name>.svg` bytes via `QFile`; replace the literal string `currentColor` with
  `#<hex>`; render with `QSvgRenderer` to a `QImage` at `px * devicePixelRatio`; cache by the full id.
  Register with `engine.addImageProvider("icon", IconProvider())`.
- `AppIcon.qml` exactly as guide §4.4: an `Image` whose `source` URL is **bound** to the resolved
  `Theme` token (so recolour happens automatically on theme change — do not add an imperative
  refresh).

### 6. Shipped schemes + JSON Schema

`themes/light.json`, `themes/dark.json` (values in guide §3.1), `themes/scheme.schema.json` (all 11
required, `additionalProperties:false`, `^#[0-9a-fA-F]{6}$`, `meta.appearance` enum). Bundle all in
qrc.

### 7. `Kobold.Foundation` `qmldir`

```
module Kobold.Foundation
singleton Theme     Theme.qml
singleton Metrics   Metrics.qml
singleton FontType  FontType.qml
AppIcon             AppIcon.qml
```
(`ThemeManager` is **not** listed here — it is a plain `QObject` reached through the `themeManager`
context property set at startup; see guide §4.7 wiring.)

---

## Definition of Done

- [ ] A throwaway QML page shows 11 rectangles, one per token colour, and text in Sans + Mono at
      12 px and 14 px, weights 400 and 600.
- [ ] Calling a Python method that switches the active scheme repaints all 11 rectangles **and**
      recolours an `AppIcon` on screen, with no page reload.
- [ ] Feeding a malformed scheme (missing key / extra key / `#abc` / 8-digit hex with alpha) is
      **rejected at load with a clear per-key error**, and the app still starts on a valid default.
- [ ] Every scheme read goes through `QFile`/`QDir`; there is no `open()`/`glob` on scheme paths.
- [ ] Font loads are asserted; removing a bundled face makes startup fail loudly, not silently
      fall back.

## Watch-outs

- **Named colour properties, not a `Theme.color("accent")` function.** A function accessor that indexes
  a dict is *not* reactive — bindings won't update on theme change. Use the 11 named properties.
- **One `changed` signal**, not 11. All facade properties depend on it.
- Do not compute or derive colours anywhere (no `Qt.lighter`, alpha, tint) — R3.
- `Metrics` consumers read named tokens; calling `Metrics.dp(48)` in a delegate scatters computation.

**Spec refs:** §3, §4, §5, §6. **Guide refs:** §3, §4.1–§4.4, §4.7.
