# Kobold UI redesign — orientation

Human onboarding and the map of everything else. **Not loaded into every session by design.** The rules Claude Code must actually hold live in `CLAUDE.md` (always) and `.claude/rules/` (when you open a matching file). Read this when you need the *why*, the history, or the state of play.

Where a rule appears both here and in a rule file, **the rule file wins** — this document is narrative, not enforcement.

---

## 1. What the project is

Joystick Gremlin R14 is a Windows desktop utility for remapping HOTAS hardware. Power users bind 100-200 inputs across a possibly large number of devices.

The brief calls it **"an instrument, not a product": dense, literal, calm.** Identity is carried by the *organisation of data* — top chrome, left input list, right action tree, nested actions — not by colour or typeface. That layout is preserved exactly; the redesign changes how it is drawn, not where things are.

Stack: PySide6 + QML (Qt Quick), targeting **Qt/PySide6 6.11**, Windows-first. The approach is a fully custom Qt Quick Controls 2 style plus singletons for colour, dimension and type. Themes are colour-only JSON data. Dimensions, type and icons are fixed design constants, not themeable.

## 2. The document set

| File | What it is | Authority |
|---|---|---|
| `jg_style_design_specification.md` (SPEC) | The visual spec, condensed. Every value decided. | **Wins on visual rules** |
| `jg_style_architecture_design.md` (guide) | Architecture, modules, wiring, phases. | **Wins on architecture** |
| `jg_style_mockup.html` | Partially functional HTML prototype. | Illustrative only |
| `phases/phase_1..7_*.md` | Per-phase concepts, deliverables, Definition of Done, watch-outs. | Most detailed |

Referenced elsewhere as `SPEC §n` and `guide §n`.

## 3. Module tiers

| Import | Disk | Holds | Consumed by |
|---|---|---|---|
| *(the style)* `Kobold` | `style/qml/Kobold/*.qml` | QQC2 control templates | implicitly, via `QQuickStyle.setStyle` |
| `Kobold.Foundation` | `style/qml/Kobold/Foundation/` | tokens, singletons, `AppIcon` | everything |
| `Kobold.Controls` | `style/qml/Kobold/Controls/` | public kit helpers + re-exports | **plugins** |
| `Kobold.Internal` | `style/qml/Kobold/Internal/` | app components + shell | app only, never plugins |

`Kobold` (the style) and `Kobold.Foundation` (a module) are distinct things that share a directory root — exactly as `QtQuick` and `QtQuick.Controls` do. The control templates sit directly in `style/qml/Kobold/`; the submodules are directories beneath it.

## 4. The phases

1. **Foundation** — tokens, singletons, fonts, icon provider, shipped schemes + JSON schema.
2. **Custom QQC2 style** — every basic control redrawn app-wide, with no call-site changes.
3. **Playground + lint** — a permanent gallery (control x state x theme x zoom) plus CI lint and unit tests. First-class and permanent; it is where verification happens.
4. **Left pane** — the input list.
5. **Shell** — menu bar, toolbar, tab strip, footer, split layout.
6. **Action-tree scaffolding** — recursive rows, slot headers, guides, drag-drop, no plugin bodies.
7. **Plugins** — finalise `Kobold.Controls`, reflow each action's config body onto it.

The phase docs contain retrospective notes (Phase 2's reminder to flip the app-wide `setFont(...)` off `"Segoe UI"`; Phase 4 pointing at `InputButton.qml` and `DeviceInputList.qml` as "the current implementation") implying the early phases have landed. **Verify actual progress against the repository, not against these documents.**

## 6. Source-document reconciliation (2026-07-23 pass)

The guide, spec and phase docs were reconciled against the code; the earlier known-error list is
resolved:

- **Naming is settled: `Kobold` is authoritative.** The stale `Gremlin.Foundation` / `Gremlin.Controls`
  names and the old style name `Instrument` are purged from the guide. The *application* remains
  Joystick Gremlin: the `gremlin/` package and `joystick_gremlin.py` are correct and stay.
- **`ThemeManager` is a context property, not a QML singleton.** It is a plain `QObject` exposed as
  `themeManager` via `setContextProperty`; `Theme.qml` and `Metrics.qml` bind to it. `uiScale` lives
  on it — there is no separate `Config` singleton.
- **`Metrics.pick()` tables are integer-keyed** (`{100, 150, 200}`), matching the code; the `15%`
  typo (→ 150%) and the double-drawn `style/qml/Kobold/` tree are fixed. `Metrics` has a fourth
  hand-controlled exception, `accentMark`.
- **Component naming:** the left-pane delegate is `InputButton` (there is no `InputRow`); chips fill
  with `bgAlt`. Generic QQC2-adjacent controls (`MenuBar`, `SplitView`, `ToolButton`) are style
  templates in `style/qml/Kobold/`; custom single-purpose components live in `Kobold.Internal`;
  top-level `qml/` holds legacy app-composition pending migration.

## 7. Working principles

- **Never silently resolve an ambiguity in the spec.** Flag it and ask.
- **Verify version-specific Qt APIs against the official Qt 6.11 documentation.** Never invent API names, enum values or signatures. If you cannot verify, stop and say so.
- Treat a rule violation as a build defect, not a style opinion.
- Prefer the smallest change that satisfies the spec. The design is deliberately austere; additions are almost always what the spec explicitly rejected.
- New components get a gallery section in the playground.
