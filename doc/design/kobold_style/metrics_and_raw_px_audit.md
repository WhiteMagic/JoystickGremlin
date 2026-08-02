# Metrics token sprawl & raw-px audit

Date: 2026-08-01
Branch: `feature/kobold-style`
Source: follow-up audit on `ui_consistency_review.md` §2.1 (raw px) and §2.2 (accent
misuse), after an AMA session surfaced that the `dialogWidth*`/`dialogHeight*`
token family had grown ad hoc, without sign-off, specifically to dodge the
"no raw px" lint rather than because those sizes were reused. This document
is a factual audit for manual remediation — no code changes have been made
for the raw-px cluster itself. The decisions already locked in during the AMA
(margin snapping, dialog sizing policy, the two accent/fill items, and the
§2.8 fix) are implemented separately, or noted below where relevant.

---

## Resolution status (2026-08-01)

All items in Parts 1, 2 and 4 below have been implemented per the inline
`>` comments, with these exceptions:

- **`windowWidth`/`windowHeight`** — kept as-is. The requested change (drive
  these from `uiState`/persisted config) is a real feature — new
  `Configuration` keys, save-on-resize/move, restore-on-startup — not a
  token rename. Deferred as its own follow-up task.
- **`viewerChartYOffset`** — kept as-is. Fixing the underlying `ChartView`
  margin behavior properly needs the app running to iterate on visually;
  not something to guess at blind. Deferred as its own follow-up task.
- **`DialogDeviceInformation.qml`'s raw-px** — done now (7 column widths
  became named local `readonly property`s on the file's `Window` root,
  shared between the static header row and the `Repeater` delegate) rather
  than deferred to the `ui_consistency_review.md` §3.2
  `ScrollList`/`Kobold.Controls` rework, since that rework hasn't started
  and there's no reason to leave raw px in place until it does.
- **"Coincidental" existing-token matches** (Part 2's `DialogInputViewer`,
  `DialogOptions`, `DialogSwapDevices`, `ScriptManager` cases) were **not**
  wired onto the numerically-matching existing token (e.g. `hatViewSize`,
  `labelColumn`) — a follow-up investigation found those matches were pure
  coincidence with no shared design intent. Each got its own per-file local
  `readonly property` instead (named for what it actually is), consistent
  with the "local constant over borrowed token" policy below.
- `bodyMin` was removed outright (0 consumers, nothing to migrate).
- The `dialogWidth*`/`dialogHeight*` family, `markSize`, `indentGuide`,
  `insertionLine`, `dropTargetHeight`, `viewerButtonSize`, `hatViewSize`,
  `hatViewDotSize`, `rowCompact`, `menuBar`/`footer` were all removed from
  `Metrics.qml` per their `>` comments below; `ctrlH` was renamed to
  `controlHeight`. See `.claude/rules/kobold-qml.md`'s Dimensions section
  for the current token set.
- Part 4's two duplicated formulas became `Metrics.tooltipWidth(contentWidth)`
  and `Metrics.tabButtonWidth(metricWidth)` functions (built on precomputed
  `_tooltipMaxWidth`/`_tooltipPadding`/`_tabButtonPadding` properties so the
  actual `dp()` calls still only run once), answering the question raised
  in Part 4 below.

The rest of this document is kept as the historical record of the audit and
decisions — read it for *why*, not for current `Metrics.qml` contents.

---

## Part 1 — `Metrics.qml` token usage inventory

47 names are declared in `Foundation/Metrics.qml` (45 dimension/scale tokens +
`scalePercentage`/`scale`, the two scale-engine properties that back `dp()`/
`even()`/`pick()` and are never meant to be read directly elsewhere).

**32 of the 47 tokens sit at 0-2 total call sites across the whole repo**
(`style/qml/` + `action_plugins/`). Sorted ascending by total occurrences:

| Token | Defined as | Files using it | Total occurrences | Ccomment |
|---|---|---:|---:|---|
| `scalePercentage` | `themeManager.uiScale` | 0 | 0 | keep |
| `scale` | `scalePercentage / 100.0` | 0 | 0 | keep |
| `bodyMin` | `dp(780)` | 0 | 0 | remove |
| `labelColumn` | `dp(250)` | 1 | 1 | tbd |
| `insertionLine` | `pick({100:2,150:2,200:4})` | 1 | 1 | remove, and express as 2 * hairline at use site |
| `toolbar` | `dp(34)` | 1 | 1 | keep |
| `footer` | `dp(24)` | 1 | 1 | keep |
| `windowHeight` | `dp(900)` | 1 | 1 | obtain via uiState which obtains this from the configuration which should persist user UI resizing and positioning |
| `rightPaneMin` | `dp(900)` | 1 | 1 | keep |
| `inputRowPitch` | `dp(52)` | 1 | 1 | keep |
| `dialogWidthXS` | `dp(300)` | 1 | 1 | drop |
| `dialogWidthS` | `dp(500)` | 1 | 1 | drop |
| `dialogWidthM` | `dp(600)` | 1 | 1 | drop |
| `dialogHeightS` | `dp(300)` | 1 | 1 | drop |
| `dialogHeightM` | `dp(500)` | 1 | 1 | drop |
| `dialogHeightL` | `dp(800)` | 1 | 1 | drop |
| `dropTargetHeight` | `dp(20)` | 1 | 1 | handle the same as insertionLine |
| `viewerAxisColumnWidth` | `dp(60)` | 1 | 1 | turn into a in-file constant |
| `viewerAxisBarHeight` | `dp(100)` | 1 | 1 | turn into a in-file constant |
| `viewerChartYOffset` | `dp(-20)` | 1 | 1 | shoudn't be required |
| `viewerButtonRadius` | `even(10)` | 1 | 1 | turn into a in-file constant |
| `labelTrailingReserve` | `even(50)` | 1 | 1 | no, use one of the gaps, maybe gapL |
| `indent` | `dp(24)` | 2 | 2 | keep |
| `sliderTrack` | `dp(4)` | 2 | 2 | keep |
| `indentGuide` | `pick({100:1,150:2,200:2})` | 1 | 2 | replace by hairline |
| `menuBar` | `dp(26)` | 2 | 2 | use the same as footer and rename to something more generic |
| `windowWidth` | `dp(1400)` | 2 | 2 | see comment about windowHeight |
| `rowCompact` | `dp(40)` | 2 | 2 | replace by rowInput or rowAction |
| `dialogWidthL` | `dp(800)` | 2 | 2 | drop |
| `viewerButtonSize` | `dp(40)` | 1 | 2 | drop |
| `hatViewSize` | `dp(200)` | 1 | 2 | drop |
| `hatViewDotSize` | `even(15)` | 1 | 2 | drop |

**Tokens with healthier reuse (3+ occurrences), for contrast:**

| Token | Defined as | Files using it | Total occurrences | Comment |
|---|---|---:|---:|---|
| `leftPaneMin` | `dp(400)` | 1 | 3 | keep |
| `rowInput` | `dp(48)` | 5 | 5 | keep |
| `tabStrip` | `dp(36)` | 3 | 5 | keep |
| `rowAction` | `dp(28)` | 6 | 6 | keep |
| `accentMark` | `pick({100:2,150:2,200:4})` | 4 | 6 | keep |
| `markSize` | `dp(16)` | 4 | 10 | remove, use icon instead |
| `icon` | `dp(16)` | 3 | 12 | keep |
| `radius` | `dp(2)` | 16 | 18 | keep |
| `gapL` | `dp(12)` | 14 | 19 | keep |
| `textDetail` | `dp(12)` | 11 | 21 | keep |
| `hairline` | `pick({100:1,150:1,200:2})` | 23 | 38 | keep |
| `ctrlH` | `dp(24)` | 21 | 39 | rename to controlHeight |
| `textBody` | `dp(14)` | 31 | 42 | keep |
| `gapS` | `dp(4)` | 28 | 55 | keep |
| `gapM` | `dp(8)` | 56 | 164 | keep |

**Takeaways for manual remediation:**
- `bodyMin` (`dp(780)`) has **zero** consumers — either wire it up somewhere or delete it.
  > Remove it
- The entire `dialogWidth*`/`dialogHeight*` family (6 tokens, 6 total occurrences — one call site each) was grown specifically to avoid raw-px lint hits on one-off dialog sizes, not because the sizes recur. See Part 3's recommended policy: stop growing this family: new dialog sizes should be `Metrics.dp(N)` inline, not a new named token.
  > Should be define in-file using dp(N), only allowed for actual dialogs not main UI parts
- The "input-viewer cluster" tokens (`viewerAxisColumnWidth`, `viewerAxisBarHeight`, `viewerChartYOffset`, `viewerButtonRadius`, `viewerButtonSize`, `hatViewSize`, `hatViewDotSize`, `labelTrailingReserve`) are all 1-2 occurrences — each was seemingly named for a single component rather than a reused concept. Worth a judgment call per-token: keep as documentation-via-naming (arguably fine, since these values are still real design constants even at one call site) vs. inline `dp()` and delete the token.
  > See description above
- `insertionLine`, `indentGuide`, `sliderTrack`, `toolbar`, `footer`, `menuBar`, `rowCompact`, `inputRowPitch`, `labelColumn`, `dropTargetHeight` are shell/structural constants at 1-2 sites — likely legitimate one-offs (there is only one toolbar, one footer, one menu bar), lower priority to touch than the dialog-size and viewer-cluster groups above.
  > See description above

---

## Part 2 — remaining §2.1 raw-px cluster, classified

53 static/top-level wrap-candidate sites (safe to inline `Metrics.dp(N)`,
evaluated once, not in a delegate) plus a smaller set of delegate-context
sites (need a pre-existing or new named token — see Part 3).

### Static / top-level (inline `Metrics.dp(N)`, no token)

| File | Sites | Notes | Comment |
|---|---:|---|---|
| `Controls/ButtonState.qml` | 9 | GridView container `Layout.minimumWidth/preferredWidth/cellWidth/cellHeight` for both `_button_grid` and `_hat_grid` — these are properties of the GridView itself, not its delegate | See comments from Part 1 |
| `Controls/AxesStateSeries.qml` | 2 | header divider height, chart-hosting rectangle height | See comments from Part 1 |
| `Controls/AxesStateCurrent.qml` | 2 | header divider height, `ListView` `Layout.preferredHeight` (its `86` line is delegate — see Part 3) | See comments from Part 1 |
| `Controls/LogicalDeviceSelector.qml` | 1 | `implicitWidth` floor of 200 | Get rid of that, was another invention |
| `Controls/InputCaptureButton.qml` | 3 | includes the duplicated tooltip-clamp formula — see Part 4 instead | see sec 4 |
| `Views/DialogCalibration.qml` | 1 | only line 54 (top row Label, before the `ScrollList`); every other flagged line in this file is inside the `CalibrationItem` delegate — see Part 3 | see below |
| `Views/DialogDeviceInformation.qml` | 8 | header row only (lines 32-56, 154); the delegate rows (86-129, 144) need tokens or are deferred — see Part 3 and the §3.2 rework note below | Replace by standard metric tokens |
| `Views/DialogInputViewer.qml` | 5 | `ScrollView` container properties (rightMargin/minimumWidth/maximumWidth), not its `Repeater`'s delegate | use existing metric tokens |
| `Views/DialogOptions.qml` | 3 | `ScrollList` container `Layout.preferredWidth`, not its delegate | use existing metric tokens |
| `Views/DialogSwapDevices.qml` | 5 | window height formula, label widths, margins — none fall inside the file's one delegate (`ComboBox.delegate`) | use existing metric tokens |
| `Views/ScriptManager.qml` | 4 | only lines 69, 83-84, 96 (`ScrollList` container margin, "Add Script" button, `ScriptConfiguration` instance) — lines 108-185 are inside the `ScriptUI` delegate, see Part 3/4 | use existing metric tokens |
| `Views/Main.qml` | 5 | header `ToolBar`/`ComboBox` (317-318, 326-327) plus the two static `TabButton`s at 583/600 — these `TabButton`s are static siblings, not inside `Main.qml`'s own `Repeater` | what are you trying to say |
| `Views/DeviceList.qml` | 2 | only lines 67, 87 (static `TabButton`s after the `Repeater`); line 44 is inside `_physicalInputs`'s delegate — part of the tab-width duplication, see Part 4 | ? |
| `Views/ConfigGroup.qml` | 3 | only lines 22, 26, 41 (root margin, header Label, Spacer); line 196 is inside a `DelegateChooser` — part of tooltip duplication, see Part 4 | ? |

**Total: 53 sites, 14 files.**

### Delegate context (needs a token — existing or new)

| Site | Existing token available? | Notes |
|---|---|---|
| `Controls/HatView.qml:56` (`radius: 2`, inside a `Repeater` delegate) | **Yes — `Metrics.radius`** | Exact value match; just wire it up, no new token |
| `Controls/ButtonState.qml:127-128` (`cellHeight/cellWidth - 20`, inside `_hat_grid`'s delegate) | **Yes, via the margin-snap policy** | `20` rounds to `gapL` (12) under the already-agreed margin policy; that's an existing pre-computed token, so it's delegate-safe |
| `Controls/AxesStateCurrent.qml:86` (`barSize: 20`, inside `_list`'s delegate) | No | Not a margin, not a radius — a genuine new-value candidate if you want a named token here |
| `Views/DialogCalibration.qml` — `CalibrationItem` delegate (lines 104,114-115,122,128,134,156,166,227,255,271,286) | No | ~4 distinct non-margin values reused 2-3× each within the one delegate: `75` (label width), `100` (×3, field/switch widths), `30` (×2, progress bar heights), `150` (×3, button-column widths) |
| `Views/DialogDeviceInformation.qml` — unnamed `Repeater` delegate (86,105,109,113,117,121,125,128-129,144) | No | 7 distinct column widths (50,75,50,100,100,100,320) reused across header row (static) and delegate row (this) — flagged in the original review (§3.2) for a full rework onto `Kobold.Controls`/`ScrollList`; likely better resolved there than as standalone tokens |
| `Views/ScriptManager.qml` — `ScriptUI` delegate (108,116,142,185; 126/153 are the tooltip duplication) | No (excl. tooltip lines) | `108,116,142,185` are distinct one-off values inside the delegate, not yet cross-referenced against each other for reuse |
| `Views/DialogManageModes.qml` — its `ScrollList` delegate (92,102,122-124,143) | No | All 4 flagged lines are inside the one delegate component |

---

## Part 3 — locked decisions from the AMA session (already agreed, referenced above)

- **Margins/paddings** that don't match `gapS(4)/gapM(8)/gapL(12)` round to
  the nearest of those three (5→4, 10→8or12, 15→12, 20→12, 30→12, 50→... use
  judgment, no gap tier above 12 exists). No new gap token.
- **Dialog window sizing** (`minimumWidth`/`minimumHeight`/`width`/`height`
  at the dialog-root level): stop growing `dialogWidth*`/`dialogHeight*`.
  New or existing raw dialog sizes get `Metrics.dp(N)` inline, not a new
  named token — including `Controls/TextInputDialog.qml:14-15`
  (→ `Metrics.dp(200)`/`Metrics.dp(60)`, deliberately NOT migrated onto
  `dialogWidthXS` despite the coincidental comment).
- **`BetterProgressBar.qml:46`** (`Theme.accent` fill): keep as-is; add an
  explicit *exception* note to `kobold-qml.md`'s accent inventory (not a
  peer 8th bullet) — it's a legitimate state indicator, just not a "thin
  marker" like the other six uses.
- **`DialogCalibration.qml:245-249`** (unsaved-changes fill): replace with a
  border-outline overlay matching `ToolButton`'s existing focus-ring geometry
  exactly (`border.width: 2`, `anchors.margins: -2`), colored `Theme.warning`
  instead of `Theme.accent`.
- **§2.8** (MergeAxis/DualAxisDeadzone unassigned-source text): fix in
  plugin QML via a ternary on `valueLabel` (`isValid ? label :
  "<slot-specific instruction>"`), not in `InputIdentifier.label`
  (`gremlin/ui/device.py`), since the instruction text is inherently
  slot-specific in a way the shared Python fallback isn't.

---

## Part 4 — duplicated raw-px formulas (from the original review, unresolved)

Two formulas repeat verbatim across multiple files — a duplication issue
layered on top of being raw px. Candidates for exactly one named token each,
regardless of the static/delegate split above (both happen to have delegate
occurrences, so inlining `dp()` isn't an option for at least some of their
sites):

- **Tooltip width clamp** `contentWidth > 500 ? 500 : contentWidth + 20` — 6
  sites: `Controls/InputCaptureButton.qml:99`, `Views/DialogDeviceInformation.qml:91`,
  `Views/ScriptManager.qml:126,153`, `Views/ScriptConfiguration.qml:236,371`,
  `Views/ConfigGroup.qml:196`. All but the `InputCaptureButton`/`DialogDeviceInformation`
  sites are inside a delegate.
- **Tab-button width formula** `_metric.width + 50` — 5 sites:
  `Views/Main.qml:583,600` (static), `Views/DeviceList.qml:44` (delegate),
  `:67,87` (static).

> Can we turn these into functions, e.g. Metrics.tolltipWidth and Metrics.tabButtonWidth?

---

## Suggested next steps (for manual work, not yet done)

1. Decide `bodyMin`'s fate (wire it up or delete).
2. Work through the 32 low-usage tokens in Part 1 with fresh eyes — keep the
   shell/structural ones (footer, toolbar, menuBar, etc.), reconsider the
   `dialogWidth*`/`dialogHeight*` family and the input-viewer cluster tokens
   against the "no new tokens for one-off sizes" policy now in effect.
3. Apply the 53 static `Metrics.dp(N)` wraps in Part 2.
4. Decide on the delegate-context values in Part 2 (existing-token reuse,
   new tokens, or deferral to the `DialogDeviceInformation` §3.2 rework).
5. Add the two named tokens for the duplicated formulas in Part 4, and
   replace all 11 call sites.
