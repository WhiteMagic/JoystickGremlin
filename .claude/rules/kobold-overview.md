---
paths:
  - "style/**"
  - "gremlin/ui/**"
  - "qml/**"
  - "action_plugins/*/*.qml"
---

# The Kobold style — overview

Everything here applies whether you are writing Python or QML.

Full background: `doc/design/kobold_style/CONTEXT.md`. Visual spec wins on visual rules; the architecture
document wins on architecture.

## What it is

A fully custom Qt Quick Controls 2 style plus three token singletons, replacing the previous Universal-styled UI. Targets **Qt/PySide6 6.11**, Windows-first.

Themes are **colour-only JSON data**, user-authorable. Dimensions, type and icons are **fixed design constants and are not themeable** — do not add a metrics or font file to a scheme.

## The five hard rules — inviolable

- **R1 Layout is static.** Nothing appears, disappears, moves or resizes on hover. Hover may
  only add an overlay that is a superset of what is on screen. One sanctioned exception in the
  whole app: the action-name field's border.
- **R2 No shadows, ever.** Floating surfaces = 1px border + opaque fill. No elevation, blur,
  translucency.
- **R3 No derived colours.** Every colour is a named `Theme.*` token or it is a bug. No alpha,
  no `Qt.lighter`/`darker`, no `Qt.rgba`, no `color-mix`.
- **R4 Accent = state only, never a fill.** No primary button anywhere. There is no `accentFg`.
- **R5 Everything visible at once.** No accordions, wizards, drawers, "advanced" sections,
  overflow menus.

## Module tiers

| Import | Disk | Holds | Used by |
|---|---|---|---|
| *(the style)* | `style/qml/Kobold/*.qml` | QQC2 control templates + generic controls | implicitly, via `QQuickStyle.setStyle("Kobold")` |
| `Kobold.Foundation` | `style/qml/Kobold/Foundation/` | `Theme`, `Metrics`, `FontType`, `AppIcon` | everything |
| `Kobold.Controls` | `style/qml/Kobold/Controls/` | public kit: re-exports + `LabeledRow`, `InlineRow` | app and plugins |
| `Kobold.Internal` | `style/qml/Kobold/Internal/` | custom single-purpose app components | app only, never plugins |

The style and `Kobold.Foundation` are distinct things sharing a directory root — exactly as `QtQuick` and `QtQuick.Controls` do. Control templates sit *directly* in `style/qml/Kobold/`; the submodules are directories beneath it. **Placement rule:** generic, QQC2-adjacent controls (`MenuBar`, `SplitView`, `ToolButton`) go in the style dir; custom single-purpose components (`InputButton`, `Chip`, …) go in `Kobold.Internal`. Top-level `qml/` holds legacy app-composition (`Main`, `DeviceTabBar`, `DeviceList`) still being migrated into these tiers. Other paths: `style/themes/` (schemes), `style/assets/{icons,fonts}/`, `style/playground/` (gallery).

## Python side

**`ThemeManager`** (`gremlin/ui/theme_manager.py`, a plain `QObject`) is the source of truth: scheme discovery, parse, validation, active scheme. It exposes 11 `Property(QColor, ..., notify=changed)`, a `uiScale` property (100 | 150 | 200), and **one** `changed` signal — not 11. It is exposed to QML as the **context property `themeManager`** (`engine.rootContext().setContextProperty("themeManager", ...)`), **not** a QML singleton.

**`Theme.qml` is a facade**: 11 lines of `readonly property color bg: themeManager.bg`, no logic. Every consumer and every plugin reads `Theme`, never `themeManager` — the lone exception is `Metrics`, which reads `themeManager.uiScale` (a dimension, not a colour). So only 11 bindings cross the Python/QML boundary and only on a theme change. Do not "simplify" this away.

**All scheme IO uses `QFile`/`QDir`, never Python `open()`/`glob`** — `QFile` resolves both `:/...` (qrc) and real filesystem paths.

Validation fails loud and never half-applies: exactly 11 keys, `^#[0-9a-fA-F]{6}$` (**alpha rejected**), `meta.appearance` in {light, dark} if present. Log the offending key, skip the scheme, start on a valid default. Scheme selection persists through the existing config class (`gremlin/config.py`).

**`IconProvider`** (`gremlin/ui/icon_provider.py`) answers `image://icon/<name>?c=<hex>&px=<n>`: load SVG bytes via `QFile`, substitute `currentColor` -> `#<hex>`, render with `QSvgRenderer` at `px * devicePixelRatio`, cache by full id. Qt's SVG renderer cannot resolve `currentColor` itself, and `IconImage`/`ColorImage` were removed in 6.9.

**Startup order matters:** `QQuickStyle.setStyle("Kobold")` + `setFallbackStyle("Basic")` **before** the engine loads any Controls-importing QML — the style cannot change after QML types register. Then fonts (assert every `addApplicationFont` id is valid; a silent failure means a system-font fallback), engine, `addImageProvider("icon", ...)`, `addImportPath("style/qml")`, expose the `ThemeManager` instance as the `themeManager` context property (`setContextProperty`), then `main.qml`.

## Scaling

Pure zoom at **100/150/200%** via multiplied integer tokens — never a scene-graph transform, never `QT_SCALE_FACTOR`. So **every dimension must be integer at 100% and 150%**: even numbers, 2px grid. 13px is illegal (x1.5 = 19.5). The 1px border is the only accepted exception. `scalePercentage` is an integer (100 | 150 | 200); key any override table by that integer — the guide's `pick()` tables and `Metrics.qml` both use integer keys.

## Verification

- `scripts/lint_style.py` — **static checks only** (raw hex, raw px, shadows, gradients, `pointSize`), scanning `style/qml/`. `action_plugins/*/*.qml` come under the gate as Phase 7 migrates them; legacy top-level `qml/` is excluded until migrated. The **Metrics-resolution test** (every token integer-or-declared-exception at all three scales) and the **scheme-schema test** are separate pytest files (`test/unit/test_metrics.py`, `test/unit/test_theme_manager.py`), not part of the lint script. Run all of them before claiming UI work is done. **Do not widen the px allowlist to make a check pass** — fix the code, or say explicitly that a new entry is warranted and ask.
- `scripts/gallery.py` renders`style/playground/` — the permanent gallery. New components get a section there; visual
  sign-off is both themes x three zooms.
- Screenshot/pixel-diff tests are **deliberately deferred**; do not add baseline images.
