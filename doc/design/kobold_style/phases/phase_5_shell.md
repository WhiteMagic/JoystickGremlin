# Phase 5 — Surrounding structure (the shell)

**Goal:** the frame around the two panes (SPEC §10): menu bar, toolbar, tab strip, footer, and the
split layout that holds the left and right panes.

**Prereqs:** main guide §0–§5. **Depends on:** Phases 1–3 (2 for the controls used inside). **Enables:**
the app's chrome; hosts panes from Phases 4 and 6.

---

## Concepts for this phase

**"Shell" = the app chrome**, everything that isn't the two content panes: the top menu bar, the
toolbar, the device/section tab strip, and the bottom status footer, plus the split container.

**The tab strip is one exclusive selection set.** The device tabs *and* the `Scripts`/`Settings`
tabs are the **same control type**, one selection group (exactly one active at a time). A **1px
vertical rule** separates the two groups — that grouping is what carries the "these tabs are a
different kind of thing" meaning. Do **not** use greying, icons, or a different control to distinguish
them. Not-current ≠ unavailable, so **no greying** of inactive tabs.

**Active tab = three channels, none of them a fill:** a 2px `accent` underline + SemiBold text +
`bgSelected` background. **Never** an accent *fill* (R4).

**The toolbar's `Configuring mode` control stays put and keeps its label.** It is an *editor* control
("which mode am I authoring?"), and users have repeatedly misread it as switching the *live* mode — so
its label is load-bearing. Don't rename it, don't move it.

**The footer is a plain adjacency readout.** `State: Running · Editing: Default · Running: Combat`.
The three facts sitting next to each other **are** the whole message. Divergence between the editing
mode and the executing mode is **routine, not an error** — so there is no divergence warning, no icon,
no colour/tone shift. Just the three readouts.

**Heights are fixed tokens** (× scale): menu bar 26, toolbar 34, tab strip 36, footer 24, body 780
(SPEC §4/§10). Pull them from `Metrics`.

---

## What you're building

Placement follows the §4.6 split: generic, QQC2-adjacent controls (`MenuBar`, `SplitView`,
`ToolButton`) are **style templates** in `style/qml/Kobold/`; the app-composition pieces (device tab
strip, split container wiring, footer) are custom components destined for `Kobold.Internal` — though
some currently live in legacy top-level `qml/` (`Main.qml`, `DeviceTabBar.qml`, `DeviceList.qml`)
pending migration.

### Root window

- Use **`ApplicationWindow`** as the root (not a bare `Window`) so Controls styling and menus work.
- Target size 1400×900; left pane min 400, right pane min 900.

### Menu bar (26)

- `File | Tools | Help`. Standard menus using the styled `Menu`/`MenuItem` from Phase 2.

### Toolbar (34)

- Buttons: `New`, `Save`, `Load`, `Active`, `Input Viewer`, `Options`, and the `Configuring mode`
  selector on the right — **keep its label and position.**

### Tab strip (36)

- One exclusive selection set containing device tabs + `Scripts` + `Settings`.
- A **1px `line` vertical rule** separates the device group from `Scripts`/`Settings`.
- Active tab: 2px `accent` underline + `FontType.semiBold` + `Theme.bgSelected`. Inactive: normal
  weight, `bg`, `fg` text — **no greying, no icons, never accent-filled.**

### Split layout

- Left pane (Phase 4) | right pane (Phase 6), with the pane minimums above. A 1px `line` divider is
  fine; no shadow between panes.

### Footer (24)

- Three readouts: `State: <…>` · `Editing: <…>` · `Running: <…>`, plain `fg`/`fgMuted` text, adjacency
  only, no warning/icon/tone even when editing ≠ executing.

---

## Definition of Done

- [ ] Fixed heights resolve from `Metrics` (26/34/36/24 × scale); nothing hardcoded.
- [ ] Device tabs and Scripts/Settings are one selection set of one control type; exactly one active;
      a 1px vertical rule separates the two groups.
- [ ] Active tab shows underline + SemiBold + `bgSelected`; inactive tabs are **not greyed**, have no
      icons, and are never accent-filled.
- [ ] The whole shell renders in the Kobold style. The right pane (action tree) is **not yet
      styled** at this point — that arrives in Phases 6–7; it is a phase boundary, not a permanent
      carve-out.
- [ ] `Configuring mode` keeps its label and toolbar position.
- [ ] Footer shows the three readouts as plain adjacency, with **no** divergence warning/icon/tone,
      even when Editing and Running differ.
- [ ] Linter script passes without failures.

## Watch-outs

- The instinct to grey inactive tabs or add icons is exactly what §10 forbids — resist it.
- Don't invent a "modes diverge!" affordance in the footer; divergence is normal.
- Menus/toolbar popups: opaque fill + 1px border, no shadow (R2).

**Spec refs:** §10. **Guide refs:** §3.2, §4.6.
