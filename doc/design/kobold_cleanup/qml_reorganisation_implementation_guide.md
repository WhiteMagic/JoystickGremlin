# QML reorganisation — implementation guide

Companion to `qml_reorganisation_decisions.md`. That document holds the **rationale**; this one
holds the **order of work**. Decision IDs (`D1`…`D19`) refer to it — read the relevant decision
before starting a phase, not the whole document up front.

Baseline: `feature/kobold-style` at `7ef5e8a`.

---

## Ground rules

- **Phases are ordered by dependency, not importance.** Do not start a phase until the previous one builds and runs.
- **`qml/` files are converted *in place*, then moved.** Never move a file and convert it in the same phase. Converting first keeps `lint_style.py` (which scans `style/qml/`, not `qml/`) from failing on half-migrated code — see D17.
- **After every phase:** `poetry run python joystick_gremlin.py` must launch and the main window must render followed by `poetry run python scripts/lint_style.py`.
- **Never widen the `lint_style.py` px allowlist to make a check pass.** Fix the code, or stop and ask.
- **Verify before deleting.** Every file list below was derived at `7ef5e8a`, verify with the current state of the code do not take statements as granted.

---

## Phase 0 — Purge

No behaviour change. Shrinks every later phase.

1. Delete the 14 dead files (Appendix A1): `ActionList` `DebugBox` `DebugBoxLayout` `GroupHeader` `HatDirectionSelectorV2` `IconButton` `JGComboBox` `JGTabButton` `LabelValueComboBox` `del.InputListener` `del.LayoutHorizontalSpacer` `del.LayoutVerticalSpacer` `del.LogicalDeviceSelector` `ActionNode.qml.orphaned`.
2. Delete the 8 dead `Gremlin.Style` / Universal imports (D15 Tier 2) — these files import but use nothing:  `Kobold/Internal/DeviceInputList` `Kobold/Internal/KeyboardInputList`
   `Kobold/Internal/LogicalDevice` `Kobold/Controls/VJoySelector` `qml/OptionProfileAutoLoading`
   `qml/MainFailure` `qml/InputItemBinding` `qml/InputItemBindingConfigurationHeader`. Delete only the `import` line.
3. Resolve the two duplicate type names. `qml/ButtonStateSelector.qml` and `qml/InputButton.qml` shadow their `Kobold` counterparts, and which one wins is import-order dependent. Determine each consumer's intended target, repoint it, then delete the `qml/` copy.

   Deleting `qml/InputButton.qml` orphans an entire chain (D11) — remove it all: the `ActionSummaryImageProvider` registration in `joystick_gremlin.py`, `gremlin/ui/action_image_generator.py`,  `gremlin/ui/util.py:ColorInformation`,
   `qml/ColorInformation.qml`, the `findChild(QObject, "colorInformation")` lookup and its `GremlinError`, and `_theme_refresh_timer`. Leave `IconProvider` and `ActionIconProvider` alone.

**Done when:** app launches, nothing references the deleted names.

---

## Phase 1 — Module skeleton

Create the empty tiers so later phases have somewhere to move things (D3).

```
style/qml/Kobold/
  Controls/     (exists — will be re-sorted in Phase 2)
  Composites/   (new)
  Views/        (new)
```

Write the `qmldir` files with the re-export directives from D6:

```
# Kobold/Controls/qmldir
module Kobold.Controls
import Kobold.Foundation
…types…

# Kobold/Composites/qmldir
module Kobold.Composites
import Kobold.Controls
…types…

# Kobold/Views/qmldir
module Kobold.Views
import Kobold.Composites
…types…
```

No version numbers (D2). `Kobold/Internal/` stays in place for now; it is emptied in Phase 2.

**Done when:** app launches unchanged (empty modules are inert).

---

## Phase 2 — Re-tier the existing Kobold files

Move only; do not edit contents beyond import lines. Placement per D4 and Appendix A.

| From | To |
|---|---|
| `Controls/{ActionNode, SlotHeader, ActionStepTable}` | `Composites/` |
| `Internal/{ActionRow, ActivationBehavior}` | `Composites/` |
| `Internal/{Chip, TreeIndent, ActivationToggle}` | `Controls/` |
| `Internal/{BindingHeader, DeviceInputList, KeyboardInputList, LogicalDevice, InputButton}` | `Views/` |
| everything else in `Controls/` | stays |

Then delete `Kobold/Internal/` and its `qmldir`.

Update imports across the repo. `Kobold.Internal` disappears entirely; the 28 plugin files keep importing `Kobold.Controls`, and the container plugins that use `ActionNode`/`SlotHeader` switch to `Kobold.Composites`.

**This phase kills the `Controls` ↔ `Internal` cycle** — `ActionRow` and `TreeIndent` now sit at or below `ActionNode` instead of above it.

The two `import "../../../../qml"` lines in `BindingHeader` and `LogicalDevice` cannot be fixed yet; they need  `TextInputDialog` and `InputBehavior`, which arrive in Phase 5. Leave them.

**Done when:** app launches, no file imports `Kobold.Internal`.

---

## Phase 3 — New shared controls

1. **`Controls/ScrollList.qml`** (D8). Write it fresh from `qml/JGListView.qml`, not from `Controls/InputListView.qml` — the latter is a lossy fork.
   - Pixel-based wheel scrolling via `wheelStep` (px). **Do not** reimplement the `indexAt`/`positionViewAtIndex` index-jumping; that is the bug being removed.
   - `scrollbarAlwaysVisible` defaults **true**.
   - Expose the vertical scrollbar via `property alias`; do not hardcode `ScrollBar.vertical` unreachable.
   - `reuseItems` stays **off** by default (D16).
   - Vertical only. Name it `ScrollList`, never `ListView`.
2. **`Controls/LabeledRow.qml` and `Controls/InlineRow.qml`** — the label/field row helpers the architecture doc specified and were never written. Several existing controls hand-roll a label with a bare `Text`; they adopt these later.
3. Convert all 13 `JGListView` / `InputListView` call sites to `ScrollList`, then delete both originals.

**Trap:** `qml/InputConfiguration.qml:65` sets `stepScroll: false`. That property does not exist on `ScrollList` and assigning it is a hard QML error. Delete the line — pixel scrolling handles the tall-delegate case that `stepScroll` was an escape hatch for. Verify the action-tree pane still scrolls smoothly with a tall action sequence.

**Done when:** every list in the app scrolls; `JGListView` and `InputListView` are gone.

---

## Phase 4 — Convert `qml/` in place

Files stay in `qml/` for this whole phase. This is the bulk of the work.

1. **Delete the superseded wrappers** (Appendix A2), converting each call site first: `JGText`→`Label` (16) · `JGTextField`→`TextField` (8) · `JGSpinBox`→`SpinBox` (3) · `IconCheckBox`→`CheckBox` + `AppIcon` (2) · `HorizontalDivider`→`Divider` · `NumericalRangeSlider`→`NumericRangeSlider` ·  `HatDirectionSelector`→`HatDirectionToggle` · `DragDropArea`→`ActionDragDropArea` · `DropMarker`→`RowDropBand` · `TriggerMode`→ `ActivationToggle` · `AutoSizingMenu`→`Menu` · `BootstrapIcons`/`BootstrapIconsNames`→`AppIcon`.
2. **Delete outright, no replacement:** `CompactSwitch`, `CompactSwitchIndicator` (SPEC deletes switches app-wide), `Triangle`, `HintsTooltip`.
3. **Fold `DynamicItemLoader` into `ConfigGroup`** as a plain `Loader` (D13). Its single call site passes only `qmlPath: model.value`; the `action` / `injectedProperties` machinery is unused. Delete the file.
4. **Convert the remaining `Gremlin.Style` / Universal references** (D15). Two mechanical patterns cover the 8 dialogs:

   - `color: Style.background` → `color: Theme.bg`
   - `Universal.theme: Style.theme` → **delete the line** (Kobold has no theme enum)

   Everything else takes whatever `Theme` token is appropriate, judged per site. `Style.lowColor`, `Style.medColor` and `Style.backgroundShade` are derived colours with no fixed mapping — read what each site meant. `accent` is state-only under R4; an accent *fill* is never the right answer, so pick another token.
5. **Skip `action_plugins/response_curve/` entirely** (D15) — owned separately.
6. Delete `qml/Style.qml` and its `qmlRegisterSingletonType` registration in `joystick_gremlin.py`.
7. Reduce `qml/helpers.js` to `capitalize`, `selectText`, `safeText` (D19). `hintColor` returns raw hex (R3 violation); `hintIcon` returns Bootstrap codepoints (superseded by `AppIcon`); `createComponent` depends on an undeclared `_root`. Convert their call sites to `Theme` tokens and `AppIcon`.

**Done when:** no file anywhere imports `Gremlin.Style` or any Universal module, except `action_plugins/response_curve/`.

---

## Phase 5 — Move the survivors

Everything in `qml/` is now clean. Move it (Appendix A3/A4).

- To `Controls/`: `BetterProgressBar` `TextInputDialog` `InputBehavior` `AxesStateCurrent` `AxesStateSeries` `ButtonState` `HatView`
- To `Views/`: the remaining 26 files, **flat** — no subdirectories (D13). `Main.qml` moves as a single file; do not decompose it.
- `helpers.js` → `Views/`, declared in its `qmldir` as a JS resource.

Then fix the two `import "../../../../qml"` lines left from Phase 2 — `TextInputDialog` and `InputBehavior` are now normal `Kobold.Controls` types.

**Trap:** `lint_style.py` scans `style/qml/**` and will now see `Views`. If Phase 4 was done properly it should pass. If it does not, fix the code — do not exclude `Views` from the scan and do not widen the allowlist.

**Done when:** `qml/` contains no `.qml` files.

---

## Phase 6 — Entry point and dynamic loading

Read D14 first; the constraint there governs anything dynamic.

1. Replace `engine.load(QUrl.fromLocalFile(…"qml/Main.qml"))` with `engine.loadFromModule("Kobold.Views", "Main")`. Same for `MainFailure`.
2. Change the three functions in `gremlin/ui/option.py` to return a **type name** instead of a `file:///` URL. In QML, call `Qt.createComponent("Kobold.Views", name)` and assign the result to `Loader.sourceComponent`.
3. Delete `QDir.addSearchPath("qml", …)` from `joystick_gremlin.py`.
4. Delete the `qml/` directory.
5. Remove the dead `engine.addImportPath(…"theme")` — that directory does not exist.

**Do not touch `ActionNode`'s `setSource(root.action.qmlPath, {"action": root.action})`.** Plugin bodies declare `required property ActionModel action`, and `setSource(url, props)` is the only mechanism that can initialise a required property. `Loader.sourceComponent` cannot. Plugin QML stays on disk, loaded by path.

**Done when:** the app launches with no `qml/` directory present.

---

## Phase 7 — Playground

Rescope per D18: the gallery exercises **standalone** components only — the 20 style templates plus the `Controls` leaves that instantiate nothing but QtQuick.

1. Restructure `PublicGallery` / `InternalGallery`; those names mirror the deleted `Controls`/`Internal` split.
2. Do **not** add `backend` or `uiState` to `scripts/gallery.py`. Types needing device init (`VJoySelector`, `LogicalDeviceSelector`, `InputCaptureButton`) or the running app (`ActionNode`, all `Views`) are out of scope, not gaps to close.
3. Remove the `Configuration()` / `register_config_options()` coupling if `ThemeManager` can be given a default scheme. Its docstring currently warns that the gallery reads and writes the real user profile.

---

## Phase 8 — Documentation reconciliation

`doc/design/kobold_style/jg_style_architecture_design.md` and `.claude/rules/kobold-overview.md` now contradict the implementation: the module tier table, `Kobold.Controls` described as "re-exports + `LabeledRow`/`InlineRow`", `SlotHeader` placed in `Internal`, and the `Internal` name itself. **The rule files are what a Claude Code session actually loads**, so until they are updated the rules in force are the old ones. Update both to match `qml_reorganisation_decisions.md`.

---

## Standing traps

- **Required properties.** Only `Loader.setSource(url, props)` and `Component.createObject(parent, props)` initialise them. `Loader.sourceComponent` does not.
- **Type shadowing.** Never name a type after a `QtQuick` one (`ListView`, `Menu`). Resolution between two unqualified imports is order-dependent.
- **Delegate reuse.** Do not turn `reuseItems` on globally. A recycled delegate keeps its state unless it handles `ListView.pooled` / `ListView.reused`; the failure is stale content on fast scroll, which no test will catch. `InputButton` is the one most at risk.
- **Accent.** R4 — state only, never a fill. Closed inventory: tab underline, selected-row bar, focus outline, checkbox/radio mark, engaged-toggle shade. Expect 2–4 on screen.
- **Derived colours.** No `Qt.rgba`, `Qt.lighter`, `Qt.darker`, `Qt.tint`, alpha, gradients. Every colour is a named `Theme` token.
- **Do not silently resolve an ambiguity.** Flag it and ask.
