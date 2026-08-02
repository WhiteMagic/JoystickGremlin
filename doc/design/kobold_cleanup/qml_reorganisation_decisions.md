# QML reorganisation — decisions & backlog

Working document for the QML restructuring discussion.
Baseline: commit `7ef5e8a` on `feature/kobold-style`.

Intended home once settled: `doc/design/kobold_style/`.
Where this conflicts with `jg_style_architecture_design.md` or `.claude/rules/kobold-overview.md`,
**this document supersedes them** and those files need updating to match.

---

## Part 1 — Decisions reached

### D1. Namespace: `Kobold.*` for QML, `Gremlin.*` for Python

All QML UI modules live under `Kobold.*`. `Gremlin.*` stays reserved for the Python-registered
bridge and model types (`Gremlin.Profile`, `Gremlin.Device`, `Gremlin.Config`, `Gremlin.Script`,
`Gremlin.Tools`, `Gremlin.UI`, `Gremlin.Util`, `Gremlin.ActionPlugins`).

**Rejected:** moving UI modules to `Gremlin.Widgets` / `Gremlin.Views`. `Gremlin.*` is already
the Python-bridge namespace; reusing it for QML presentation collapses a boundary that is
currently clean and legible — `import Gremlin.X` means "reaching into Python", `import Kobold.X`
means "reaching into QML".

Consistent with `CONTEXT.md` §6, which already recorded `Kobold` as authoritative.

### D2. The style is not intended for reuse

Kobold is bespoke to Joystick Gremlin and will not be designed or architected for extraction.

Consequences:
- No qmldir version numbers (current practice of omitting them is correct).
- No `typeinfo` / `.qmltypes` generation.
- `internal` qmldir markers are optional documentation, not a correctness requirement.
- **The plugin SDK boundary is the only encapsulation boundary that earns enforcement.**
  Every other module split exists for human navigation.
- No objection to domain-aware types (`ActionModel` consumers) living in the `Kobold` namespace.

### D3. Module structure

```
style/qml/Kobold/
  *.qml          QQC2 control templates      (selected via QQuickStyle.setStyle)
  Foundation/    Theme, Metrics, FontType, AppIcon
  Controls/      leaves
  Composites/    assemblies of Kobold types, no app state
  Views/         app-only; plugins must never import
```

**Rejected:** `Widgets` / `Components` (synonyms — unmemorable, would end up co-imported with no
rule for placement). **Rejected:** topical `ActionTree` / `Inputs` split (arbitrary choice of
subjects; mixed a topical axis with a level axis and collided with `Controls`).

### D4. Controls vs Composites — the split rule

> **Does the file instantiate another type from the Kobold namespace?**
> No → `Controls`. Yes → `Composites`.

Chosen because it is mechanically checkable rather than a taste judgment: a script greps for
capitalised child elements and intersects with the Kobold type list. Misfiling becomes a lint
failure. The rule self-maintains — adding a Kobold child to a leaf forces it to move.

Current classification:

| | Members |
|---|---|
| **Controls** (leaves) | `Spacer` `Divider` `Chip` `TreeIndent` `ActivationToggle` `RowDropBand` `ActionDragDropArea` `ScrollList` `ButtonStateSelector` `NumericRangeSlider` `HatDirectionToggle` `InputAssignButton` `AddActionMenuButton` `InputCaptureButton` `VJoySelector` `LogicalDeviceSelector` |
| **Composites** | `ActionNode` `ActionRow` `SlotHeader` `ActionStepTable` `ActivationBehavior` |
| **Views** | `BindingHeader` `DeviceInputList` `KeyboardInputList` `LogicalDevice` `InputButton` + `qml/` survivors |

Known wrinkle, accepted: `VJoySelector`, `InputAssignButton` and `HatDirectionToggle` classify as
leaves today only because they hand-roll label rows with bare `Text`. Once `LabeledRow` /
`InlineRow` exist and they adopt them, they become composites automatically — no reclassification
decision required. The rule and intuition converge as the kit fills out.

`Chip` is a `Controls` member (`Rectangle` + `Text`, leaf), not a View.

### D5. Views is defined by the plugin contract

`Views` is drawn on a different axis from the Controls/Composites split — contract, not structure.
Structurally its members are composites; they are separated because **plugins must never import
them**. Plugins may import `Foundation`, `Controls` and `Composites`.

Enforcement lives on the *importing* side, not in Views' contents: `action_plugins/**/*.qml` must
not import `Kobold.Views`. That check is mechanical and is the only one that matters.

Placement heuristic: **a View is shell furniture** — instantiated once by the application (or once
per device/input) and positioned by the shell, never a reusable element a plugin could sensibly
drop into its own body.

> Superseded: an earlier draft defined Views as "reads `backend`/`uiState`/`signal`". D9 allows
> those everywhere, so that is no longer a discriminator.

### D6. qmldir re-exports

`Composites/qmldir` carries `import Kobold.Controls`; `Controls/qmldir` carries
`import Kobold.Foundation`. The qmldir `import` directive makes the other module's types available
in the same namespace as the importing module, so common cases need one import line:

- simple plugin body → `import Kobold.Controls`
- container plugin → `import Kobold.Composites`
- app view → `import Kobold.Views`

This directly answers the "both get imported anyway" objection to any tier split.

Accepted tradeoff: import blocks become less informative about actual usage and qmllint's
unused-import checking gets fuzzier. Acceptable given D2.

### D7. `qml/` is eliminated entirely

The top-level `qml/` directory goes away completely. It is currently not a module at all — no
qmldir, reached via `QDir.addSearchPath("qml", …)` plus implicit directory imports, which is the
pattern Qt has been steering projects away from since the CMake port.

Disposition is *mostly deletion, not migration*: of the 69 `.qml` files, **36 are deleted**
(13 already dead, 23 superseded) and **33 survive as moves** — 7 to `Controls`, 26 to `Views`.
No file in `qml/` moves unchanged in name and place; the directory ceases to exist.

### D8. `ScrollList` replaces `JGListView` and `InputListView`

Written fresh from `JGListView` (the more complete of the two); both originals deleted; all
call sites converted.

- **Pixel-based wheel scrolling**, not index jumping. `wheelStep` in px; uniform-row callers pass
  `Metrics.inputRowPitch * 3`. This deletes the `stepScroll` boolean and the
  `indexAt`/`positionViewAtIndex` fragility, which only ever worked for uniform short rows.
- `scrollbarAlwaysVisible` **defaults true** — 12 of 13 call sites set it. Also the more
  R1-compliant default (an as-needed scrollbar appears and disappears).
- Vertical scrollbar exposed via `property alias`, not hardcoded, so callers can reach
  `interactive` etc.
- Named `ScrollList`, not `ListView` — two unqualified `ListView` types in scope is
  import-order-dependent and fragile.
- Vertical only.
- Control-template internals (`ComboBox`, `Menu`, `TabBar`, `DeviceTabBar` `contentItem`s) keep
  the bare `ListView` and must not adopt this.

**Live bug this fixes:** `InputListView` is a lossy fork of `JGListView` that dropped
`stepScroll`. `qml/InputConfiguration.qml:65` sets `stepScroll: false` — the action-tree pane,
the tall-variable-delegate case. Migrating that file as-is is a hard QML error.

**`reuseItems` is off by default — opt-in per call site.** Recycling changes delegate semantics:
a reused instance keeps its local state unless it handles the `ListView.pooled` / `ListView.reused`
attached signals. The failure mode is subtle and visual (stale content during fast scroll), not a
hard error, so neither lint nor tests would catch a silent default change. The four sites that need
it already ask for it (`DeviceInputList`, `KeyboardInputList`, `LogicalDevice`, `MacroAction`).
`InputButton` is the delegate most at risk — it holds a `Timer`, a `TextMetrics`, a `Loader` and a
chip `Repeater`, and its chip-overflow measurement is exactly the computed state that breaks under
reuse. Recorded as **D16**.

### D9. Plugin import contract

| Allowed | Forbidden |
|---|---|
| `QtQuick`, `QtQuick.Controls`, `QtQuick.Layouts`, `QtQuick.Shapes`, `QtQuick.Window`, `QtQuick.Dialogs`, `Qt.labs.qmlmodels` | `Kobold.Views` |
| `Kobold.Foundation`, `Kobold.Controls`, `Kobold.Composites` | `Kobold` (the style — nobody imports it) |
| `Gremlin.ActionPlugins`, `Gremlin.Profile` | `Gremlin.Device`, `Gremlin.UI`, `Gremlin.Config`, `Gremlin.Script`, `Gremlin.Tools`, `Gremlin.Util` |
| plugin-local `.js` | any relative directory import (`import "../.."`) |

**Plugins may open their own dialogs.** `QtQuick.Dialogs` and `QtQuick.Window` are sanctioned.

**Context properties are a sanctioned global API, available everywhere including plugin bodies.**
`backend`, `uiState`, `signal`, `themeManager` may be read from any tier. The five existing plugin
call sites (`uiState.currentInput` ×4 in `merge_axis` / `dual_axis_deadzone`,
`signal.reloadCurrentInputItem()` ×1 in `macro`) are therefore legal as written and need no
refactor.

> Considered and dropped: routing `uiState.currentInput` through `InputAssignButton` or through
> `ActionModel`. Unnecessary once context properties are sanctioned globals.

Device access still goes through `VJoySelector` / `LogicalDeviceSelector` rather than a direct
`Gremlin.Device` import — that is current practice across all 28 plugins and is now written down
rather than accidental.

### D10. `Gremlin.Style` and Universal are entirely forbidden

Not merely deprecated, and not merely off-limits to plugins: **banned repo-wide**. No file in any
tier may import `Gremlin.Style`, `QtQuick.Controls.Universal`, or any other Universal module.
`qml/Style.qml` is deleted and its `qmlRegisterSingletonType` registration removed from
`joystick_gremlin.py`.

Current state to clear before the gate can be switched on: 32 files import `Gremlin.Style` and 31
import Universal, including three inside what is today `Kobold.Internal`, plus `response_curve/`.
The rule is adopted now as the target; the lint gate turns on at the end of B6.

### D11. The action-summary image pipeline is deleted

`ColorInformation` is a remnant — `ThemeManager` already provides everything it exposed. It is
not "rewired to read `ThemeManager`", it is **deleted**, along with the whole rendering path it
served.

The only consumer of `image://action_summary` is `qml/InputButton.qml:156`, the *legacy* left-pane
delegate. The Kobold `InputButton` replaced summary images with the `Chip` row. Deleting the legacy
delegate (already slated under D7 — it is also one of the two duplicate type names) orphans the
entire chain:

- `qml/InputButton.qml` (legacy delegate)
- `ActionSummaryImageProvider` registration in `joystick_gremlin.py`
- `gremlin/ui/action_image_generator.py` — the whole module, ~250 lines
- `gremlin/ui/util.py:ColorInformation`
- `qml/ColorInformation.qml`
- the `findChild(QObject, "colorInformation")` lookup and its startup `GremlinError`
- `_theme_refresh_timer` in `joystick_gremlin.py`

`IconProvider` (`image://icon`) and `ActionIconProvider` (`image://action-icon`) are unrelated and
stay.

Aside, now moot: the deleted path read the **Universal** palette rather than `Theme`, so Python's
colours and the UI's colours came from two different sources.

### D12. `ThemeManager` stays a context property

**Rejected:** registering `ThemeManager` as a QML singleton in `Kobold.Foundation`.

Reason is empirical, not theoretical: QML-singleton registration was attempted and behaved badly on
the PySide6 side. Registering the instance into the root context is the working alternative and is
consistent with how `backend` and `uiState` are already exposed. D9 having sanctioned context
properties as a global API, this is coherent rather than a compromise.

Consequence accepted: context properties are invisible to the Qt Quick Compiler, qmllint and the
QML Language Server, which treat every access as unqualified — hence `UnqualifiedAccess=disable`
in `.qmllint.ini`.

Qt 6.11 added a qmllint configuration file for declaring context properties, which would let that
check be re-enabled. **Deferred — not a priority.** Folded into B8 if and when it matters. (The
file's exact name and format have not been verified against the docs.)

---

## Part 2 — Backlog

Ordered so that decisions unblocking others come first.

| # | Topic | Why it's here |
|---|---|---|
| ~~B1~~ | ~~Plugin import contract~~ | **Settled → D9, D10** |
| ~~B2~~ | ~~`themeManager`: context property vs QML singleton~~ | **Settled → D12** |
| ~~B3~~ | ~~App-state access rule~~ | **Settled → D9.** Context properties are a sanctioned global API at every tier |
| ~~B4~~ | ~~`qml/` file-by-file disposition~~ | **Settled → D13 + Appendix A** (open items marked there) |
| ~~B5~~ | ~~Entry point & dynamic loading~~ | **Settled → D14**, except the option-editor mechanism (one open choice) |
| ~~B6~~ | ~~`Gremlin.Style` / Universal removal~~ | **Settled → D15** |
| ~~B7~~ | ~~`ScrollList` detail~~ | **Settled → D16** |
| ~~B8~~ | ~~Lint & test gates~~ | **Settled → D17** |
| ~~B9~~ | ~~Playground~~ | **Settled → D18** |
| ~~B10~~ | ~~Housekeeping~~ | **Settled → Appendix A + D19** |
| ~~B11~~ | ~~Migration sequencing~~ | **Not pre-planned.** Order is flexible and can be reordered as work proceeds; only hard constraint is the `Views`/lint interaction in D17 |

### Deferred / assumed, flag if wrong

- `action_plugins/*/*.qml` stay co-located with their Python. Not revisited.
- Screenshot / pixel-diff tests remain deliberately deferred (existing project decision).

### D13. `qml/` disposition rules

- **`Main.qml` stays a single file** for now. It is the main UI; decomposition is not part of this
  restructure.
- **No subdirectories under `Views`.** Flat, with a naming-prefix convention (`Dialog*`, `Option*`,
  `Config*`). Avoids hand-maintaining a `qmldir` per subdirectory — the engine's implicit import
  resolves to a file's own directory, not the module root, so nested files cannot see their
  siblings without explicit imports. Qt's CMake tooling generates those extra qmldirs
  automatically (policy `QTP0004`); under Poetry they would be maintained by hand.
- **Generic dialogs are judged case by case**, and only if still needed at all. Of the current set,
  only `ErrorDialog` clearly qualifies as a View.
- **The input-viewer cluster splits** — the dialog is a View, its visualisation widgets go to
  `Controls`/`Composites` by the D4 rule.
- **`Config*` are Views** — `ConfigGroup`, `ConfigSection`, `ConfigSectionButton` serve the options
  dialog.
- **`DynamicItemLoader` is deleted.** One consumer (`ConfigGroup.qml:235`); folded in as a plain
  `Loader` using `setSource(path, {props})`. Its post-load property injection cannot initialise a
  `required property` — the failure mode `ActionNode` documents — and its `reload()` calls
  `destroy()` on an item the `Loader` owns. Shape is contingent on B5.

### D14. Dynamic loading

**The governing constraint** (verified against Qt 6.11 docs). `Loader` has exactly two inputs:
`source` (a URL) and `sourceComponent` (a `Component`). There is no module-based `source`.
`setSource(url, properties)` accepts initial properties; `sourceComponent` has **no**
initial-properties channel. `Qt.createComponent(moduleUri, typeName, mode, parent)` exists since
Qt 6.5 and returns a `Component`; `Component.createObject(parent, {props})` takes initial
properties.

> **Anything with a `required property` must be loaded via `Loader.setSource(url, props)` or
> `Component.createObject(parent, props)`. Module-based loading through `Loader.sourceComponent`
> cannot initialise required properties.**

Applies to any future dynamic loading, not just the three cases below.

**Plugin bodies — no change.** They declare `required property ActionModel action`, so
`ActionNode`'s `setSource(root.action.qmlPath, {"action": root.action})` is the only mechanism that
works. Plugin QML stays on disk next to its Python and is loaded by path. Consistent with the
standing assumption that `action_plugins/*/*.qml` stay co-located.

**Entry point.** `engine.loadFromModule("Kobold.Views", "Main")` replaces the absolute-path
`engine.load(...)`. No properties involved. `QQmlApplicationEngine.loadFromModule(uri, typeName)`
is available in PySide6, introduced in Qt 6.5 — within the project's `PySide6 >= 6.8` floor.

**Option editors — module-based loading.** `gremlin/ui/option.py` returns a **type name**, not a
`file:///` URL; QML calls `Qt.createComponent("Kobold.Views", name)` and assigns the result to
`Loader.sourceComponent`. Viable because the three `Option*.qml` files declare no required
properties, and `ConfigGroup` passes only `qmlPath: model.value` (`DynamicItemLoader`'s
`action` / `injectedProperties` machinery is entirely unused at its single call site — see D13).

**This is what deletes `QDir.addSearchPath("qml", …)`.** Rejected alternative: keeping `file:///`
URLs repointed at the new directory — works, but relocates the search-path hack rather than
removing it.

### D15. `Gremlin.Style` / Universal removal

Real size is **126 call sites** (82 `Style.*` across 38 files, 44 raw `Universal.*` across 37), not
the 39 `Gremlin.Style` imports. Four tiers, only the last needing thought:

**Tier 1 — vanishes with the file (53 sites, 17 files).** All already in A1/A2:
`CompactSwitchIndicator` (12) `Style.qml` (7) `ColorInformation` (7) `JGTextField` (5)
`InputButton` (5) `JGTabButton` (4) `NumericalRangeSlider` (2) `IconButton` (2)
`HorizontalDivider` (2) `HintsTooltip` (2) `DropMarker` (2) `JGText` (1) `GroupHeader` (1)
`CompactSwitch` (1) `TriggerMode` `LabelValueComboBox` `ActionList`

**Tier 2 — dead imports, one deleted line each (8 files, 0 sites).** Import `Gremlin.Style` or
Universal and use nothing from it: `Kobold/Internal/DeviceInputList`
`Kobold/Internal/KeyboardInputList` `Kobold/Internal/LogicalDevice` `Kobold/Controls/VJoySelector`
`qml/OptionProfileAutoLoading` `qml/MainFailure` `qml/InputItemBinding`
`qml/InputItemBindingConfigurationHeader`

The first four are the "old styling system live inside the new Kobold tier" problem. Four deleted
lines, no conversion.

**Tier 3 — formulaic (8 dialogs, 30 sites).** Two repeated patterns: `color: Style.background`
→ `Theme.bg` (×8) and `Universal.theme: Style.theme` → **delete the line** (×8). Five leftovers.
`DialogDeviceInformation` is the only outlier at 7 sites.

**Tier 4 — routine (31 sites, 12 files).** `Main` (6), `TextInputDialog` (4),
`ConfigSectionButton` (4), `AxesStateSeries` (3), long tail of 1–2s.

**Out of scope — `response_curve` (12 sites, 3 files).** `ResponseCurveAction`, `HandleControl`
and `PointControl` are excluded from the mechanical pass; they need manual intervention and are
handled separately.

**Method: no up-front mapping table.** Tier 4 sites take whatever `Theme` token is appropriate,
decided per site as part of the conversion each of these files is undergoing anyway.

Two consequences worth stating:

- **The accent question dissolves.** 23 legacy accent references exceed R4's closed inventory
  many times over, but accent-as-fill is not an appropriate token choice, so those sites resolve
  to non-accent tokens during conversion. No spec amendment required.
- **Five `Style.qml` members are already unreferenced** and go with the file: `removeAlpha()`
  `decimalsPrecise` `decimalsStandard` `tooltipMaxWidth` `tooltipDelayMs` `warning`. Notably this
  means no home is needed in the token set for a duration or a numeric-precision preset.

**Handled separately.** `response_curve` — including its
`source: Style.isDarkMode ? "grid_dark.svg" : "grid.svg"` line, for which no `Theme` token exists —
is owned outside this restructure and is not resolved here.

### D17. No new lint or structural checks

**Rejected:** import-graph checks, the D4 leaf/composite placement check, the D9 plugin allowlist
check, and any new pytest for QML structure. The existing `lint_style.py` value checks (raw hex,
raw px in styling positions, gradients/tints, `pointSize`) are sufficient and stay as they are.
`.qmllint.ini` rework is likewise not a priority (D12).

Consequence, accepted: D4, D5, D9 and D10 are **conventions, not enforced rules**. Note this does
not undermine the reasoning behind D4 — the leaf/composite rule was chosen because it is
*decidable by reading the file*, which remains true whether or not a script checks it. That is
still the property `Widgets`/`Components` lacked. Given D2, the cost of drift is low.

**One mechanical consequence for B11.** `lint_style.py` scans `style/qml/**`, which will contain
`Views` after the restructure. `Views` arrives as freshly-migrated legacy code full of raw px and
hand-rolled colours, so the existing lint starts failing the moment those files land — without
anyone touching the lint. Either exclude `Views` from its scan, or land the moves only after B6
has converted those files. Decide at sequencing time.

### D18. The playground exercises standalone components only

**Scope principle:** the gallery exists to exercise the main *standalone-testable* components —
those that do not require the full Gremlin application. Not a catalogue of everything.

Sorting the current types by what they actually need:

| Grade | Types | In the gallery? |
|---|---|---|
| **Standalone** — nothing but QtQuick + Foundation | all 20 style templates, plus `Spacer` `Divider` `Chip` `TreeIndent` `ActivationToggle` `RowDropBand` `ActionDragDropArea` `ScrollList` `ButtonStateSelector` `NumericRangeSlider` `HatDirectionToggle` `InputAssignButton` `AddActionMenuButton` | **yes** — ~33 types, the real target |
| **Needs device/app init** | `VJoySelector` (`VJoyDevices`), `LogicalDeviceSelector` (`LogicalDeviceSelectorModel`), `InputCaptureButton` (`InputListenerModel`) | no |
| **Needs the running app** | `ActionNode` (reads `backend`, `signal`), every `View` | no |

**Both non-standalone grades are out of scope**, for the same reason: they effectively require
Gremlin. Device/app-init types need DILL, vJoy and device enumeration to mean anything;
`ActionNode` and the `Views` need a live `Backend` and a loaded profile. Neither is a gallery
gap to be closed later — they are outside what the gallery is for.

**No `Backend` or `uiState` in `gallery.py`.** Standing one up would contradict the scope
principle.

**The "new components get a gallery section" obligation narrows accordingly** — it applies to
standalone components only. Blanket application across four modules would be unenforceable for the
two grades the gallery cannot instantiate.

**Corollary: `gallery.py` should shed bootstrap, not grow it.** It currently constructs
`Configuration()` and calls `register_config_options()`, and its own docstring warns that it reads
and writes the real Joystick Gremlin user profile and should not be run from automation. That
coupling exists solely because `ThemeManager` reads scheme selection from config. Removing it —
e.g. letting `ThemeManager` start on a default scheme without config — is what would make the
gallery genuinely standalone and safe to run casually.

Gallery file naming (`PublicGallery` / `InternalGallery`) mirrors the superseded
`Controls`/`Internal` split and should be restructured to match what the gallery now covers.

### D19. `helpers.js` moves with its consumers

Destination: **`Views`**, declared as a JavaScript resource in the `Views` qmldir. Every surviving
non-plugin consumer lands there — `Main` `ConfigGroup` `ConfigSection` `ConfigSectionButton`
`DialogOptions` `OptionEntryCard` `ProfileSettings` `ScriptManager`
`InputItemBindingConfigurationHeader`. `HintsTooltip`, the tenth, is deleted.

**Most of the file is already obsolete** and should not survive the move intact:

- `hintColor()` returns raw hex (`#3E65FF` `#F0A30A` `#A20025` `#74008b`) — an R3 violation that
  `lint_style.py` rejects. Two of those are the old `Style.warning` / `Style.error` values;
  they become `Theme` tokens.
- `hintIcon()` returns Bootstrap font codepoints (`\uF433` …) — the approach `AppIcon` +
  `IconProvider` replaces, and for which A2 already deletes `BootstrapIcons`.
- `determineHintIcon()` / `determineHintColor()` are wrappers over those two.
- `createComponent()` references a free variable `_root` that is not a parameter — it depends
  silently on the calling scope.

Genuinely live remainder: `capitalize`, `selectText`, `safeText` — three one-liners.

**Plugin wrinkle.** `response_curve`'s three files also import it, and plugins cannot import
`Kobold.Views` (D5). It already carries a local `render_helpers.js`, so it absorbs whatever it
still needs there when it is converted — consistent with plugins being self-contained.

---

## Appendix A — `qml/` file disposition

No open items remain.

### A1. Delete — already dead (14)

`ActionList` `DebugBox` `DebugBoxLayout` `GroupHeader` `HatDirectionSelectorV2` `IconButton`
`JGComboBox` `JGTabButton` `LabelValueComboBox` `del.InputListener`
`del.LayoutHorizontalSpacer` `del.LayoutVerticalSpacer` `del.LogicalDeviceSelector`
`ActionNode.qml.orphaned`

### A2. Delete — superseded; convert call sites

| File | Refs | Replaced by |
|---|---|---|
| `Style` | 39 | `Theme` / `Metrics` / `FontType` (B6) |
| `JGText` | 16 | `Kobold` `Label` |
| `JGListView` | 11 | `Controls/ScrollList` (D8) |
| `JGTextField` | 8 | `Kobold` `TextField` |
| `InputButton` | 4 | `Views/InputButton`; takes the summary-image chain with it (D11) |
| `JGSpinBox` | 3 | `Kobold` `SpinBox` |
| `ButtonStateSelector` | 3 | `Controls/ButtonStateSelector` (duplicate type name) |
| `BootstrapIcons` / `BootstrapIconsNames` | 2 / 1 | `AppIcon` + `IconProvider` |
| `IconCheckBox` | 2 | `Kobold` `CheckBox` + `AppIcon` |
| `ColorInformation` | 4 | nothing — deleted (D11) |
| `HorizontalDivider` | 1 | `Controls/Divider` |
| `NumericalRangeSlider` | 1 | `Controls/NumericRangeSlider` |
| `HatDirectionSelector` | 1 | `Controls/HatDirectionToggle` |
| `DragDropArea` | 1 | `Controls/ActionDragDropArea` |
| `DropMarker` | 1 | `Controls/RowDropBand` |
| `DynamicItemLoader` | 1 | folded into `ConfigGroup` (D13) |
| `CompactSwitch` / `CompactSwitchIndicator` | 3 / 1 | nothing — SPEC deletes switches app-wide |
| `TriggerMode` | 2 | `Controls/ActivationToggle` |
| `Triangle` | 1 | nothing — no longer needed |
| `AutoSizingMenu` | 1 | `Kobold` `Menu` |
| `HintsTooltip` | 1 | nothing — to be reintegrated/redone as and when needed |

### A3. Move to `Controls` — subject to the D4 leaf check

| File | Note |
|---|---|
| `BetterProgressBar` | no Kobold `ProgressBar` template exists |
| `TextInputDialog` | 4 refs incl. `LogicalDevice`; kills one `import "../../../../qml"` |
| `InputBehavior` | consumed by `BindingHeader`; kills the other relative import |
| `AxesStateCurrent` `AxesStateSeries` `ButtonState` `HatView` | input-viewer widgets, per D13's split |

### A4. Move to `Views` (flat)

`Main` `MainFailure` `DeviceTabBar` `DeviceList` `InputConfiguration` `InputItemBinding`
`InputItemBindingConfigurationHeader` `ProfileSettings` `ScriptManager` `ScriptConfiguration`
`ErrorDialog` `DialogAbout` `DialogAutoMapper` `DialogCalibration` `DialogDeviceInformation`
`DialogInputViewer` `DialogManageModes` `DialogOptions` `DialogSwapDevices`
`OptionActionSequenceOrdering` `OptionEntryCard` `OptionProfileAutoLoading`
`OptionTTSVoiceSelection` `ConfigGroup` `ConfigSection` `ConfigSectionButton`

Plus, arriving from today's `Kobold.Internal`: `BindingHeader` `DeviceInputList`
`KeyboardInputList` `LogicalDevice` `InputButton`

### A5. Other

`helpers.js` (10 importers) → JavaScript resource declaration in the destination `qmldir` — B10.
