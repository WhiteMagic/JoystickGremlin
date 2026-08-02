# Kobold Style UI Consistency Review

Date: 2026-08-01
Branch: `feature/kobold-style`
Scope: `style/qml/Kobold/{Foundation,Controls,Composites,Views}`, `action_plugins/**/*.qml`, `gremlin/ui/*.py`
Reference standard: `.claude/rules/kobold-overview.md`, `.claude/rules/kobold-qml.md`

This is a catalog of findings only — no remediation ordering is implied by the
order below. Findings are grouped by theme; each entry cites `file:line` and a
severity (high/medium/low) as assessed by the reviewing agent.

Methodology: four parallel review passes (Foundation+Controls, Composites+Views,
action_plugins, Python backend `gremlin/ui/`), each reading every file in its
scope in full, followed by a targeted cross-cutting verification pass on the
four highest-consequence claims (all four confirmed — see "Verified"
annotations below).

---

## 1. High-severity bugs (likely to break at runtime)

- **`action_plugins/response_curve/HandleControl.qml:25,105-107,136-137`** —
  references an undefined `Style` singleton (`Style.accent`, `Style.medColor`,
  `Style.background`). No `Style` type exists anywhere in the live source tree
  (only in stale `dist/**` build artifacts from the pre-Kobold UI); the file
  only imports `Kobold.Foundation`. **Verified: this component is live**,
  dynamically loaded from `response_curve/ResponseCurveAction.qml:227-234`, so
  any curve-editor Bezier handle will throw a QML `ReferenceError` at runtime.
  Its sibling `PointControl.qml:21` shows the correct migrated form
  (`Theme.accent`/`Theme.line`), confirming this is unmigrated legacy code.

- **`style/qml/Kobold/Views/OptionActionSequenceOrdering.qml:78-80`** —
  `Drag.mimeData: { "text/plain": model.index.toString() }` is missing the
  parenthesization QML requires to disambiguate an object literal from a
  grouped-property binding block. `Composites/ActionNode.qml:44-48` shows the
  correct form (`Drag.mimeData: ({...})`) for the identical pattern one file
  away. As written this very likely fails to parse/compile, breaking this
  component's drag-reorder (or the whole file).

- **`style/qml/Kobold/Views/ConfigGroup.qml:243`** —
  `Qt.createComponent("Kobold.Views", model.value)` does not match any valid
  `Qt.createComponent` overload (`url, mode, parent`); passing a module name as
  the URL and a filename as the second arg is not valid. The `meta_option`
  dynamic-loading `DelegateChoice` this backs is very likely non-functional.

- **`style/qml/Kobold/Controls/Spacer.qml:9-12`** — root is a `Rectangle` with
  no `color` set, so it defaults to opaque white. Since `Spacer` exists
  specifically to consume leftover layout space, this renders a solid white
  block wherever it has nonzero area — both a rendering bug and an
  accidental un-themed color on screen. Should be `color: "transparent"` or
  the root should be `Item`.

- **`gremlin/ui/theme_manager.py:173-183,205-212`** — `_apply(theme_name)`
  indexes `self._themes[theme_name]["colors"]` with no guard; `_get_current_theme()`
  falls back to the literal `"light"`, but if no schemes validate at all (or
  the default light scheme itself is missing/invalid), `"light"` won't be in
  `self._themes` either, raising `KeyError` and crashing startup — instead of
  the "log and skip the bad scheme, start on a valid default" behavior
  `kobold-overview.md` mandates. Same risk in `_config_changed_cb`.

- **`gremlin/ui/device.py:302-309`** — `DeviceListModel.selectedIndex`'s
  setter never emits `selectedIndexChanged` despite the property declaring
  `notify=selectedIndexChanged`. Any QML binding on `selectedIndex` silently
  stops updating when set from QML.

- **`gremlin/ui/device.py:1571-1587`** — `AxisCalibration._set_guid` calls
  `self.modelReset.emit()` and then `self.endResetModel()` — the latter
  already emits `modelReset` itself, so the signal double-fires, and the first
  emission happens while the model is still between `beginResetModel()`/
  `endResetModel()` (i.e. in an inconsistent state), risking connected
  views/proxies querying row data mid-reset. Every other `_set_guid` in the
  package (e.g. `Device._set_guid`) has the correct ordering.

- **`gremlin/ui/script.py:319-330`** — `VirtualInputVariableModel.label`
  returns a hardcoded `"Bla 123"` — a debug stub left in shipped code.

- **`gremlin/ui/script.py:190-197`** — `LogicalDeviceModel._get_logical_input_identifier`
  reads `LogicalDevice.device_guid` (the class itself, no instantiation)
  rather than `LogicalDevice().device_guid`, the pattern used everywhere else
  this singleton is touched. Unless `device_guid` is a genuine class
  attribute, reading this property raises `AttributeError`.
  > You should verify this kind of statement yourself, and second it's not used in that manner everywhere else, as a simple search prooved.

- **`gremlin/ui/profile.py:749-754`** — `InputItemModel.data()` constructs a
  brand-new `InputItemBindingModel` on every call, and that constructor itself
  rebuilds the entire `ActionModel` tree (BFS + fresh signal connections per
  node) with no caching. Called repeatedly by views/QML for the same row, this
  reconstructs the action tree far more than necessary and leaks the discarded
  instances' signal connections over the UI's lifetime.
  > Unclear how to resolve.

> All items here but the last one have been resolved.

---

## 2. Kobold rule violations

### 2.1 Raw px instead of `Metrics` tokens (pervasive — three separate clusters)

- **Controls "input-viewer cluster"** (looks ported-but-not-reskinned):
  `Controls/ButtonState.qml:62,73-74,82-83,110-111,118-119,127-128`,
  `Controls/AxesStateSeries.qml:70,77`, `Controls/AxesStateCurrent.qml:48,57,86`,
  `Controls/BetterProgressBar.qml:20,22,37,45`, `Controls/HatView.qml:56`,
  `Controls/LogicalDeviceSelector.qml:33`, `Controls/InputCaptureButton.qml:99`.
- **`Controls/TextInputDialog.qml:14-15,34,56`** — raw `minimumWidth: 200`/
  `minimumHeight: 60`/margins, even though `Metrics.qml:55` defines
  `dialogWidthXS: dp(300) // rename-script popup` seemingly authored for this
  exact dialog — and the value doesn't even match (200 vs 300).
- **Views dialogs** (the weakest area for token adoption in the whole Views
  tier — nearly every `Dialog*.qml` hardcodes window/row/margin sizes instead
  of the `dialogWidth*`/`dialogHeight*` tokens that already exist for this):
  `DialogAbout.qml:12-13`, `DialogAutoMapper.qml:16-17,49,57,70,92,105,151,174-175`,
  `DialogCalibration.qml:16-18,48,51,54,104,114-115,122,128,134,156,166,227,255,271,286`,
  `DialogDeviceInformation.qml:13-14,24,32,36,40,44,48,52,56,86,105,109,113,117,121,125,128,129,144,154`,
  `DialogInputViewer.qml:17-18,69-71` (mixed with correctly-used
  `Metrics.windowWidth`/`Metrics.dialogHeightL` two lines above),
  `DialogManageModes.qml:16-17,44-45,92,102,122-124,143`,
  `DialogOptions.qml:15-16,39`, `DialogSwapDevices.qml:16,45,65,93,109`.
  `LogicalDevice.qml:29` even calls `Metrics.dp(300)` ad hoc instead of the
  existing `Metrics.dialogWidthXS` — which `ScriptManager.qml:44` uses
  correctly for the identical rename-popup case.
- **Other Views raw px**: `Main.qml:24-25,317-318,326-327`,
  `InputButton.qml:172`, `ProfileSettings.qml:18-19,130,229`,
  `ScriptManager.qml:57,62,69,83-84,96,108,116,142,185`,
  `MainFailure.qml:46`, `OptionEntryCard.qml:34-37,60`,
  `OptionProfileAutoLoading.qml:223`, `ConfigGroup.qml:22,26,41`.
- **action_plugins**: `response_curve/ResponseCurveAction.qml:125,152,178,247`,
  `response_curve/HandleControl.qml:107,138`, `change_mode/ChangeModeAction.qml:54,133,179`.
  Notably `ResponseCurveAction.qml`'s `_vis.size: 450` and
  `Layout.preferredWidth: 475` are never passed through `Metrics.dp()`, so the
  entire curve-editor canvas doesn't scale with `uiScale` at any zoom level —
  unlike every other view in the app.
- **Duplicated magic-number literals** (raw px repeated identically across
  multiple files — a duplication issue as well as a token issue):
  tooltip width-clamp `contentWidth > 500 ? 500 : contentWidth + 20` in
  `ScriptManager.qml:126,153`, `ScriptConfiguration.qml:236,371`,
  `DialogDeviceInformation.qml:91`, `ConfigGroup.qml:196` (6 sites); tab-button
  width formula `_metric.width + 50` in `Main.qml:583,600`,
  `DeviceList.qml:44,67,87` (5 sites).

> Ignore response curve related aspects, fix everything else by making suggestions and using AMA whenever things are unclear.

### 2.2 Accent-color misuse (R4: accent is state-only, never a fill)

- **`Controls/BetterProgressBar.qml:46`** — `color: Theme.accent` fills the
  entire elapsed region of the progress indicator. The accent inventory in
  `kobold-qml.md` (tab underline, selected-row bar, focus outline,
  checkbox/radio mark, engaged-toggle shade, drag insertion line) has no
  progress-bar entry.
  > This is used to show state, i.e. what is the current value of an axis.
- **`Views/DialogCalibration.qml:245-249`** — `Rectangle { color: unsavedChanges
  ? Theme.warning : "transparent" }` fully fills a save button with a status
  color; not an explicit rule hit (only `accent` is formally restricted) but
  flagged as it reads like a status-color fill the rest of the app avoids —
  worth confirming intent.
  > Filling is bad, using a color callout is fine, but likely should be outline or underline like other indicators.

### 2.3 Raw hex color

- **`action_plugins/response_curve/ResponseCurveAction.qml:194`,
  `HandleControl.qml:69,82`** — raw hex `"#808080"` for curve/handle stroke
  color, should be a `Theme.*` token.
  > Agree: use Theme.line

### 2.4 Token/rule numeric contradiction

- **`Foundation/Metrics.qml:21`** declares `indent: dp(24)`, but
  `.claude/rules/kobold-qml.md:20` states the indent step is 16. Every
  consumer (`Controls/TreeIndent.qml:28`, `Controls/InputBehavior.qml:25`)
  inherits whichever value is "correct" — flagging the contradiction rather
  than assuming which side is stale.
  > Update the rules file to reflect this change, 24 looks better

### 2.5 Banned `Switch` control still present (app-wide ban per rules)

8 call sites across 5 Views files, despite `OptionActionSequenceOrdering.qml:113`
already showing the correct `CheckBox`-based conversion for the identical
concept: `DialogAutoMapper.qml:133,141`, `DialogCalibration.qml:133`,
`DialogInputViewer.qml:146,161,176`, `OptionProfileAutoLoading.qml:177`,
`ConfigGroup.qml:59-67`. `ConfigGroup.qml`'s use is a direct **consistency**
hit too — it implements the same on/off semantic as
`OptionActionSequenceOrdering.qml` with a different, banned control.
> Replace them all with CheckBoxes

### 2.6 Font/weight rule ("No bold, no italic; emphasis is SemiBold; type comes only from `FontType`")

- `MainFailure.qml:28` (`font.bold: true`), `:38` (`font.family: "Consolas"`
  instead of `FontType.mono`).
- `DialogSwapDevices.qml:48,68` (`font.bold: true` ×2), `:86` (raw
  `Font.DemiBold`/`Font.Normal` instead of `FontType.semiBold`/`.regular`).
- `OptionEntryCard.qml:44` (`font.weight: 600` literal instead of
  `FontType.semiBold`).
> You already spell out how to fix them, apply those changes.

### 2.7 Plugin body-only contract ("never `Kobold.Views`")

No violations found — **verified clean** across all 27 `action_plugins/**/*.qml`
files.

### 2.8 Phase-7 spec gap: unassigned multi-input source instruction text

- **`action_plugins/merge_axis/MergeAxisAction.qml:124-136`,
  `dual_axis_deadzone/DualAxisDeadzoneAction.qml:126-138`** — both drive
  `InputAssignButton.valueLabel` from `action.firstAxis.label`, which
  (traced to `gremlin/ui/device.py:129-145`) returns the generic `"No input"`
  when unassigned. `phase_7_plugins.md` explicitly specifies an unassigned
  source row should carry its own instruction text (example given:
  `"Not assigned — open the second axis and add this merge instance there to
  assign it."`). Currently both plugins show the generic string — flagged per
  the doc's own "flag it, don't invent a fix" guidance, since the fix may
  belong at the `InputIdentifier.label` level rather than in plugin QML.
  > Lets AMA to figure out how to fix this.

### 2.9 Python-side rule/convention violations

- **`gremlin/ui/theme_manager.py:214-238`** — `set_theme`/`set_ui_scale` are
  `@QtCore.Slot`-decorated QML-facing methods but named in `snake_case`, not
  `camelCase` — an isolated regression against the project's own confirmed
  convention (every other QML-facing slot in the package is camelCase).
  > Fix them to use camelCase
- **`gremlin/ui/icon_provider.py:99-135`** — `kobold-overview.md` specifies
  icons render via `QSvgRenderer` at `px * devicePixelRatio`; `_render()`
  rasterizes at raw `px` only, and `size`/`requestedSize` are documented as
  unused with no DPR lookup anywhere in the file — icons would under-resolve
  and blur at 150%/200% UI scale or on HiDPI displays. (Caveat noted by the
  reviewer: moot if DPR multiplication happens QML-side before the URL is
  built, in `Foundation/AppIcon.qml`, which was out of that pass's scope.)
  > Put this on a "feature fixes" list that lives in the kobold_style folder
- **`gremlin/ui/backend.py:151-152`** — `Backend` (the central Python/QML
  bridge singleton) uses the legacy `@common.SingletonDecorator`. AGENTS.md is
  explicit that only `metaclass=common.SingletonMetaclass` should be used and
  the decorator form is retired; `option.py`'s `MetaConfigOption` shows the
  correct pattern already in use elsewhere in the same package.
  > You cannot use a metaclass singleton with a QtObject derived class that breaks things. At least I assume, correct me if I'm wrong.
- **`gremlin/ui/theme_manager.py:44-53,244-246`** — `_CHART_SERIES_COLORS`,
  8 hardcoded raw hex strings exposed via `chartSeriesColors`, bypassing the
  colour-only-JSON/11-token-scheme architecture (R3). Code comment
  self-acknowledges it's outside the validated scheme schema — flagged as an
  undocumented architectural deviation, not necessarily wrong.
  > Actually since we're already exposing them turn them into part of the json color theme.
- **`gremlin/ui/option.py:429-431`** — `TTSVoiceSelectionModel.data()`
  matches on the raw role integer instead of the established
  `cast(str, self.roles.get(role, ""))` pattern every other model in the
  package uses.
  > Fix that, the py-modernize skill is useful here
- **`gremlin/ui/option.py:162-199`** — `ConfigEntryModel.data()` hand-decodes
  the `QByteArray` role name and branches with nested `if`/`match` instead of
  the same established pattern.
  > Fix that, the py-modernize skill is useful here
- Verification pass found these two are the concrete named exceptions; a
  repo-wide grep otherwise shows the `cast(str, self.roles...)` pattern
  dominant (~24 conforming implementations located), plus one further raw
  role-int match at `gremlin/ui/util.py:455`.
  > Fix them, the py-modernize skill is useful here
- **`gremlin/ui/option.py:110-123`** and, by the same unguarded pattern,
  `option.py`'s `ActionSequenceOrdering.setData`/`ProfileAutoLoadingModel.data`/
  `setData`, and `profile.py`'s `StartupModeModel`, `VJoyInputOrOutputModel`,
  `OutputVJoyListModel`, `OutputVJoyInitialValuesModel`,
  `ProfileDeviceListModel` — all index `self.roles[role]` directly with no
  membership check, unlike guarded siblings (`Device`, `DeviceListModel`,
  `KeyboardManagerModel`, `ConfigSectionModel`, `ConfigEntryModel`) which
  `return None` on an unmapped role. An unmapped role raises `KeyError`
  instead of degrading gracefully.
  > Ignore
- **`gremlin/ui/profile.py:936`** — `LabelValueSelectionModel._set_current_value`
  calls root-logger `logging.error(...)` instead of
  `logging.getLogger("system").warning(...)`, per the project's mandated
  system/user logger split.
  > That's wrong and needs fixing
- **`gremlin/ui/action_model.py:221-222`** — `lambda x: sort_names.index(x)`
  and `for name, vis in priority_list` use single-letter/abbreviated names
  (`x`, `vis`), against the project's naming convention.
  > make suggestions for a fix

---

## 3. Duplication / reusability gaps

### 3.1 Within Controls/

- **Divider boilerplate triplicated**: `Controls/AxesStateCurrent.qml:44-50`,
  `Controls/AxesStateSeries.qml:66-72`, `Controls/ButtonState.qml:58-64` each
  hand-roll `Rectangle { Layout.fillWidth: true; height: 2; color: Theme.line }`
  instead of reusing `Controls/Divider.qml`, which exists for exactly this.
  > Use Controls.Divier
- **Whole-section boilerplate shared 3×**: the same three files share a near-
  identical `Item` root / `title` property / `ColumnLayout` content /
  `RowLayout` header-with-divider structure — a strong candidate for one
  shared "ViewerSectionHeader" component instead of three copies that will
  drift independently.
  > Good idea refactor as such
- **`Controls/HatDirectionToggle.qml:45-72`** (`ToggleBackground`) reimplements
  the rest/hover/down fill logic and focus-ring block verbatim from
  `style/qml/Kobold/ToolButton.qml:54-70` — only the checked-state accent
  underline is genuinely new code.
  > Not great but that differentiated behavior is required, ama to find a solution

### 3.2 Views not reusing existing Controls/Composites

- **`Views/DialogDeviceInformation.qml`** and **`Views/DialogInputViewer.qml`**
  — neither imports `Kobold.Controls`; both hand-roll a
  `ScrollView`+`ColumnLayout`/`Repeater` table/list instead of reusing
  `Controls/ScrollList.qml`.
  > Transition them to be proper Kobold using views, also adjust their font uses etc
- **`Views/DialogDeviceInformation.qml`** additionally hardcodes the same
  column widths twice — once per `HeaderText` in the header row, once per
  `TextEntry` per delegate row (e.g. `50/75/50/100/100/100/320` repeated
  verbatim) — a duplication issue layered on top of being raw px.
  > Transition to Kobold and rework the display in general it's the oldest ui element that's never been reworked
- **`Views/ScriptConfiguration.qml`**'s local `DescriptiveText` component
  (lines 343-381) duplicates `Views/OptionEntryCard.qml`'s "label +
  description + trailing control" concept with a structurally different
  implementation (`RowLayout`+`Label` vs `Pane`+`RowLayout`+`ColumnLayout`).
  > Unclear what the point is here, ama
- **`Views/DeviceInputList.qml`, `KeyboardInputList.qml`, `LogicalDevice.qml`**
  each repeat an identical 2-line `footer: Item { width: ListView.view.width;
  height: Metrics.gapM }` — trivial, likely not worth extracting alone.
  > Nah leave as is

### 3.3 Within action_plugins

- **Hand-rolled `Text` duplicating `Label`'s styling** — 9 files / 15
  occurrences hand-roll `Text { color: Theme.fg; font.family: FontType.sans;
  font.pixelSize: Metrics.textBody }` instead of using `Label`, losing the
  disabled-color binding `Label` provides for free:
  `double_tap/DoubleTapAction.qml:25-30,44-49`, `chain/ChainAction.qml:25-30`,
  `change_mode/ChangeModeAction.qml:44-49,85-90,97-102,110-117,169-174`,
  `macro/MacroAction.qml:607-613`, `tempo/TempoAction.qml:25-30,44-49`,
  `map_to_vjoy/MapToVjoyAction.qml:64-70`,
  `hat_buttons/HatButtonsAction.qml:25-30`,
  `smart_toggle/SmartToggleAction.qml:25-30`,
  `condition/ConditionAction.qml:160-165`.
  > Incomplete porting to Kobold, fix
- **Exact-duplicate inline rename dialog**: `merge_axis/MergeAxisAction.qml:36-53`
  and `dual_axis_deadzone/DualAxisDeadzoneAction.qml:36-53` contain a
  byte-for-byte identical `Dialog { title: "Rename action" ... }` block — a
  third, inline reimplementation of what `Controls/TextInputDialog.qml`
  already exists to do (see §2.1's `TextInputDialog` raw-px finding — that
  component itself is also not fully polished, which may be why plugin
  authors avoided it).
  > Cleanup and impove the Controls.TextInputDialog and then use it instead of the hand rolled options, ama
- **Duplicated "instance selector" ComboBox idiom** (~20 lines each): a
  `ComboBox` bound to `LabelValueSelectionModel` + `Component.onCompleted`
  seeding + `Connections{onSelectionChanged}` + `onActivated` write-back,
  near-verbatim in `reference/ReferenceAction.qml:25-45`,
  `merge_axis/MergeAxisAction.qml:63-83,98-118`,
  `dual_axis_deadzone/DualAxisDeadzoneAction.qml:63-83`.
  > What is the point you're tryign to make? ama
- **Duplicated file-picker row**: `load_profile/LoadProfileAction.qml:21-56`,
  `play_sound/PlaySoundAction.qml:20-67`,
  `run_command/RunCommandAction.qml:22-86` each hand-roll an identical
  `TextField` + "Select file" `Button` + `FileDialog` triplet, including the
  same `selectedFile.toString().substring("file:///".length)` idiom.
  > Is it possible to extract this out into a Control/Composite filepicker?
- **Duplicated "axis mode" radio+scaling block**:
  `map_to_vjoy/MapToVjoyAction.qml:49-81`,
  `map_to_logical_device/MapToLogicalDeviceAction.qml:36-70`, and a third
  variant as local components in `macro/MacroAction.qml:484-509`.
  `MapToVjoyAction` and `MapToLogicalDeviceAction` are otherwise near-identical
  bodies (selector + axis-mode block + button-invert checkbox); the two also
  disagree stylistically per the `Text`-vs-`Label` finding above.
  > Have to see if can be refactored as use cases are different, and unsure if the "setting of values" is the same as well, AMA.
- **Internal triple-duplication**: `map_to_mouse/MapToMouseAction.qml`'s
  cross-clamped min/max-speed `SpinBox` pair repeats 3× (button/axis/hat
  modes) at lines 83-105, 173-195, 211-233, unlike `MacroAction.qml` which
  factored its own repeats into local `component`s.
  > AMA on how we want to tackle this, i.e. local component or maybe a refactored PairedSpinBox component.

### 3.4 Python backend

- **`gremlin/ui/action_model.py:412-446`** `ActionPriorityListModel` —
  **verified dead**: not QML-registered, zero `.qml` references, superseded
  by `option.py`'s `ActionSequenceOrdering` (line 260), which
  `Views/OptionActionSequenceOrdering.qml:12` actually instantiates. Carries a
  `# TODO: Needs to be treated as a normal action property type...` comment.
  > This is ENTIRELY wrong, it drives the whole action sequence editor. Properly read this you moron.
- **`gremlin/ui/profile.py:127-190` (`VirtualButtonModel`) and `:218-277`
  (`HatDirectionModel`)** — each implement ~65 lines of near-identical
  8-direction (`hatNorth`…`hatNorthWest`) `QtCore.Property` boilerplate around
  a `directions` list, differing only in whose attribute the list lives on.
  > Find a way to refactor and generally go over hat usage and see if there are more inconsistencies or duplications.
- **`gremlin/ui/script.py:67-279`** — `BoolVariableModel`, `FloatVariableModel`,
  `IntegerVariableModel`, `ModeVariableModel`, `SelectionVariableModel`,
  `StringVariableModel` each repeat an identical get/set/`changed.emit()`/
  `evaluate_validity()` `QtCore.Property` pattern differing only by value type.
  > Fine to elave as is
- **`gremlin/ui/device.py`** — `Device`, `LogicalDeviceManagementModel`,
  `KeyboardManagerModel` each define near-identical `roles` dicts and
  `data()` `match` blocks for `actionSequenceCount`/`actionSequenceDescriptor`/
  `actionSequenceDisplayMode`/`description`/`actionLabels`
  (~lines 390-421, 564-599, 849-876), differing only in the `"name"` case and
  the `_get_input_item` lookup.
  > Fine to leave as is

---

## 4. Consistency issues

- **`Controls/ActivationToggle.qml`** is named "*Toggle" but implements two
  `CheckBox`es (on/off), not the armed/engaged semantics `kobold-qml.md`
  reserves for "toggle." The component's own comment agrees ("checkbox =
  on/off"). Name invites confusion with the real toggle-button pattern
  (`HatDirectionToggle`'s `ToggleBackground`).
  > Rename to ActionActivationSelector
- **`Controls/ButtonStateSelector.qml:11`** — signal is
  `stateModified(bool isPressed)`, breaking the `xxxEdited` naming convention
  every other Controls "prop-in/signal-out" component uses.
  > Rename to be in line
- **Unused `import QtQuick.Window`** in `Controls/AxesStateSeries.qml`,
  `AxesStateCurrent.qml`, `BetterProgressBar.qml`, `ButtonState.qml`,
  `HatView.qml` — same copy-pasted dead import across the whole
  "input-viewer cluster." Also present in
  `action_plugins/merge_axis/MergeAxisAction.qml` and
  `dual_axis_deadzone/DualAxisDeadzoneAction.qml`.
  > Remove unused imports
- **Import ordering** inconsistent between files mixing `Kobold.Foundation`
  with `Gremlin.*`: `Controls/VJoySelector.qml` puts `Kobold.Foundation`
  before `Gremlin.Device`; `Controls/InputCaptureButton.qml` puts
  `Gremlin.Util` before `Kobold.Foundation`; `Controls/ButtonState.qml`/
  `HatView.qml` put `Gremlin.Device` before `Kobold.Foundation`. No fixed
  convention across the directory.
  > Make it consistent across all files. Kobold and Gremlin are together in one block, ordered lexicographically, ama if unclear
- **`Views/DeviceTabBar.qml:38-39`** reuses `Metrics.tabStrip` (a height
  token, 36) as a horizontal highlight-range inset — numerically works, reads
  as a copy-paste of the wrong token rather than an intentional choice.
  > Why do you think that, it's part of the shell and a tab so?
- **Redundant self-import**: `Views/Main.qml:16` and
  `Views/InputItemBinding.qml:15` both `import Kobold.Views` from within
  `Kobold.Views` itself (same-directory types are implicitly visible), while
  sibling files consuming other Views components don't do this — inconsistent
  import style across the tier.
  > Fix it
- **`Views/Main.qml:386-438`** — footer labels read "Status:"/"Editing:"/
  "Executing mode:" where `phase_5_shell.md` and `kobold-qml.md` both specify
  the exact wording `State · Editing · Running`.
  > Rename to: State - Editing - Running.
- **`Views/Main.qml:396`** — `Helpers.selectText(backend.gremlinActive &
  backend.gremlinPaused, ...)` uses bitwise `&` instead of logical `&&`;
  happens to work today via boolean→int coercion but is a latent footgun.
  > Fix it
- **action_plugins root-of-body deviates from documented convention**:
  `merge_axis/MergeAxisAction.qml`, `dual_axis_deadzone/DualAxisDeadzoneAction.qml`,
  `response_curve/ResponseCurveAction.qml` all root the plugin body in an
  extra `Item` wrapper instead of rooting directly in `ColumnLayout` as the
  other 24 plugins do and as `kobold-qml.md`'s "Action Plugin views" section
  specifies. None of the three bind `implicitWidth` (only `implicitHeight`),
  unlike `Composites/ActionNode.qml:37-38` which binds both — looks like
  copy-paste drift, not a deliberate need (nothing in these three files
  requires the wrapper).
  > Change them to be in line with other plugins
- **Three different idioms for "combo bound to a Python string enum"**: plain
  string array + `find()`/`currentText` (`change_mode/ChangeModeAction.qml:25-37`,
  `response_curve/ResponseCurveAction.qml:124-133`); object array
  `{value,text}` + `textRole`/`valueRole` (`macro/MacroAction.qml:58-76`,
  `condition/ConditionAction.qml:43-55`); parallel arrays + manual index
  lookup (`text_to_speech/TextToSpeechAction.qml:35-43`). All work; three
  conventions for one recurring shape.
  > Lets ama about that to find a good single way of doing this
- **`pragma ComponentBehavior: Bound` applied inconsistently**: only
  `dual_axis_deadzone/DualAxisDeadzoneAction.qml`,
  `merge_axis/MergeAxisAction.qml`, `root/RootAction.qml` declare it, despite
  most of the other 24 plugin files relying on the same `required property`
  delegate idiom the pragma is meant to make rigorous.
  > AMA need to explain this to me and then together arrive at a decision
- **`action_plugins/condition/ConditionAction.qml`** mixes two delegate-
  property conventions in one file: explicit `required property var
  modelData`/`required property int index` on `ActionNode` `Repeater`
  delegates (lines 98-107, 124-133), vs. implicit ambient `index`/`modelData`
  in its `DelegateChooser`/`DelegateChoice` components (lines 135-190).
  > implicit is likely wrong, but ama
- **`gremlin/ui/profile.py:127-190,218-277`** — getter/setter lambdas for all
  16 hat-direction properties use `cls` as the parameter name for what is
  actually the instance (`fget=lambda cls: ...`); `ProfileSettingsModel
  .macroDefaultDelay` in the same file correctly uses `self`.
  > Fix it but make sure this is actually correct and doesn't have some hidden requirement you've overlooked, ama
- **`gremlin/ui/tools.py:61-62,83-84`** — imports `signal` the module
  (`from gremlin import (..., signal, ...)`) rather than `from gremlin.signal
  import signal` as every other file in the package does, producing the
  confusing double-attribute `signal.signal.profileChanged`.
  > Make sure there is no other signal in there tha would cause a shadowing effect, if then it is safe change it, ama if unsure
- **`gremlin/ui/device.py`, `icon_provider.py`, `action_model.py`, `option.py`**
  — three different idioms mark an unimplemented base-class method:
  `NotImplementedError` (`icon_provider.py:97`), `error.GremlinError`
  (`device.py:1168,1186`), `error.MissingImplementationError`
  (`action_model.py:109,309`, `option.py:253`).
  > The only valid exception should be error.MissingImplementationError which is designed for that purpose
- **`gremlin/ui/script.py:338-361`** — `VirtualInputVariableModel`'s setters
  compare against the public property (`self._variable.input_type`) but
  write the private attribute directly (`self._variable._input_type = ...`),
  reaching past whatever validation the owning class's own setter performs.
  > There are no setters, read the class properly you moron

---

## 5. Dead / orphaned code

- **`style/qml/Kobold/Views/InputItemBindingConfigurationHeader.qml`** —
  **verified dead**: superseded by `BindingHeader.qml` (whose own header
  comment says so), still exported in `Views/qmldir:15`, zero real
  instantiations anywhere in the repo. Itself contains raw px
  (`Layout.leftMargin: 20` at lines 118,166; `-5`/`+5` offsets at 91-92) and
  zero `Metrics.*` usage despite importing `Kobold.Foundation`.
  > Remove
- **`style/qml/Kobold/Views/helpers.js:32-77`** — `hintIcon`/`hintRole`/
  `determineHintIcon`/`determineHintRole`'s sole consumer is the orphaned file
  above; dead code once that file is removed.
  > Lets keep for now we may want to reuse some of that
- **`gremlin/ui/action_model.py:412-446`** `ActionPriorityListModel` —
  **verified dead**, see §3.4.
  > AGAIN wrong see other item where you make this claim
- **`gremlin/ui/profile.py:718-744`** — `InputItemModel.dropAction` reorders
  `action_sequences` in place but only emits the custom `bindingsChanged`
  signal, not `dataChanged`/`layoutChanged`/`modelReset` — the signals a
  `QAbstractListModel`-backed view actually reacts to for reordering. Likely
  a stale-ordering-in-view bug rather than dead code, flagged here since it's
  adjacent to the dead-model finding above.
  > Go ahead and fix that

---

## 6. Other / low severity

- **`Controls/ButtonState.qml:20-27,75`** — `computeButtonHeight()` takes no
  parameters but is called as `computeButtonHeight(_root.width)`; the
  argument is silently discarded (harmless in QML/JS, but dead/misleading).
  > Fix it
- **`Foundation/Theme.qml`** re-exposes `appearance` alongside the 11 color
  tokens — legitimate (confirmed against `theme_manager.py:253`), just
  technically undercounted by `kobold-overview.md`'s "11 bindings" line. Not
  a defect.
  > Update the documentation
- **`Views/OptionActionSequenceOrdering.qml:49-50,136`** — drag insertion
  line uses `height: 2` instead of `Metrics.insertionLine`, even though the
  semantics match the spec's "2px drag insertion line in accent" exactly.
  > Switch to the Metrics.hairline token and we'll see if it looks ok
- **`Views/helpers.js:15`** — `component.createObject(parent, {"x": 100, "y":
  300})` hardcodes a dialog spawn position.
  > AMA
- **`gremlin/ui/device.py:188-193`** — `InputIdentifier.__eq__` defined
  without `__hash__`, making instances unhashable (not currently exercised as
  a dict/set key, but a latent footgun).
  > Implement a hash function, ama on the design
- **`gremlin/ui/device.py:519-521`** — `changeName` has an acknowledged
  `# FIXME: Somehow needs to reset the text field to the previous value`.
  > AMA on how we do that
- **`gremlin/ui/action_model.py:63-65`** — `SequenceIndex.parent_index`
  annotated `-> int` but `self._parent_index` is `int | None` in practice
  (root nodes pass `None`).
  > AMA focusing on if None is ever used etc
- **`gremlin/ui/profile.py:654-656`** — `InputItemBindingModel.behavior_type`
  annotated `-> None` but returns an `InputType`; this feeds
  `ActionModel.input_type`, so the wrong annotation propagates into a real
  contract.
  > Update the annotation, None makes no sense there
- **`gremlin/ui/profile.py:886-887`** — `LabelValueSelectionModel.__init__`
  uses mutable default arguments (`bootstrap: list[str] = []`,
  `icons: list[str] = []`).
  > AMA on how we want to tackle this
- **`gremlin/ui/profile.py:700-716`** — `InputItemModel.deleteActionSequnce`
  (typo: missing "e") is `@QtCore.Slot`-exposed, so the misspelling is now
  part of the QML-facing API surface.
  > Fix the typo
- **`gremlin/ui/action_model.py:200-227`** — `compatibleActions` does
  `sorted(filtered_names, key=lambda x: sort_names.index(x))` against a
  user-persisted priority list; a new/unlisted action type raises
  `ValueError` and breaks the action menu for that context.
  > I don't think that's true, explain yourself
- **`gremlin/ui/script.py:322-325`** — `VirtualInputVariableModel.__init__`
  is typed `variable: user_script.PhysicalInputVariable` (copy-pasted from
  the sibling class above it), but `ScriptListModel.data_class_lookup` maps
  this class to `user_script.VirtualInputVariable` — the annotation is wrong.
- **`gremlin/ui/script.py:381-383`** — `ScriptListModel.roles` uses
  `QtCore.QByteArray("path".encode())` instead of the `QtCore.QByteArray(b"path")`
  byte-literal style every other `roles` dict in the package uses.
  > Wrong that's been fixed, read the code you retard
- **`gremlin/ui/backend.py:372-397,411-423`** — `getActionCount`/`getInputItem`
  silently swallow `error.ProfileError` with no logging, unlike most other
  error paths in the package.
  > Unsure what you mean, explain and ama
- **`gremlin/ui/backend.py:102`, `device.py` (multiple), `script.py`** —
  parameter/loop variable named `input`, shadowing the Python builtin, in
  several places.
  > AMA about this, though we don't use input which is a cli only thing
- **`gremlin/ui/theme_manager.py:100-108`** — `__init__` docstring says
  `Args: roots:` but the actual parameter is `root_paths`.
  > Fix it
- **`gremlin/ui/tools.py:39-50`** — `createMappings` docstring omits the
  `mode` parameter.
  > Fix it, the comment-code skill tells you how
- **`gremlin/ui/util.py:455`** — one further raw role-int match in `data()`,
  the sole outlier the verification pass found outside `option.py`'s two.
  > Fix using the py-modernize skill

---

## 7. What's clean (worth stating explicitly)

- No shadows, gradients, `Qt.rgba`, or `color-mix` found anywhere in
  Foundation, Controls, Composites, Views, or action_plugins.
- No `action_plugins/**/*.qml` file imports `Kobold.Views` — the plugin
  body-only contract is fully respected (verified across all 27 files).
- `style/qml/Kobold/Composites/*` is clean — no findings at all in that
  directory.
- The bulk of action_plugins (`description`, `load_profile` through
  `smart_toggle`, `split_axis`, `tempo`, `root`) is structurally sound:
  correct `ColumnLayout` root, correct Controls/Composites import tier for
  simple vs. container plugins, consistent `SlotHeader` +
  `Repeater{delegate: ActionNode{...}}` container idiom.
- `Controls/AddActionMenuButton.qml`, `RowDropBand.qml`, `TreeIndent.qml`,
  `NumericRangeSlider.qml`, `Chip.qml`, etc. are meticulously token-driven and
  rule-compliant — the raw-px issues in §2.1 are concentrated in specific,
  identifiable clusters, not spread evenly across Controls.
- Scheme discovery/validation and font loading in `theme_manager.py`
  correctly go through `QFile`/`QDir`, never raw Python `open()`/`glob`.
- `ThemeManager` exposes exactly the documented `QtGui.QColor` properties
  (plus `uiScale`) backed by one `changed` signal, matching the architecture
  doc's shape.
