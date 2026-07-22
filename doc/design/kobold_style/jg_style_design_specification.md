# Joystick Gremlin R14 — UI spec (condensed)

Implementation reference. Every value here is decided. Nothing is open.
Long-form version with rationale and rejected alternatives: `gremlin_r14_design_brief.md`.

**What it is:** a Windows desktop utility for remapping HOTAS hardware. Power users bind
100–200 inputs across 4–6 devices, in long sessions, beside a game. It is an instrument,
not a product. Dense, literal, calm. No onboarding, no delight, no marketing UI.

**Identity = the organisation of data.** Top: menu + toolbar + tabs. Left: inputs of the
selected device. Right: action config of the selected input. Plus nested actions.
Preserve exactly. Identity is *not* carried by colour or typeface.

---

## 1. Data model

```
<input> -> device-id, input-type(axis|button|hat), input-id, mode
        -> action-configuration: root-action(UUID) + behavior
<library> -> every <action id=UUID type=...>, flat. Owns its own config.
             <actions><action-id>UUID</action-id> = a REFERENCE, not containment.
```

- Library owns config. Inputs hold references. **Format is fixed; do not change it.**
- **Sharing is native**: one `<action>` can be referenced by two roots (that is how
  multi-input actions appear on two inputs — it is literally one object).
- **One node type: the action.** Every action = editable name + type config + N named slots.
- **Slot counts are dynamic**: Condition 2 (True/False), Tempo 2, Hat 4 or 8 (changes with
  its own 4/8-way config), Chain N (user adds/removes), Map to vJoy 0.
- **`RootAction` is invisible**: no config, no indent. **Top-level actions sit at depth 0.**
- **Macro's steps are NOT child actions.** Render as a table. If they look like nesting, the
  UI is lying.

---

## 2. Hard rules

| | |
|---|---|
| **R1** | **Layout is static.** Nothing appears/disappears/moves/resizes on hover. Hover may only add an overlay containing a **superset** of what is on screen. **One knowing exception**: the action-name field's border (§8). |
| **R2** | **No shadows, ever.** Floating surfaces = 1px border + opaque fill. No elevation, blur, translucency. |
| **R3** | **No derived colours.** Every colour is a named token or it is a bug. No alpha, no tints, no `color-mix`. |
| **R4** | **Accent = state only. Never a fill.** No primary button anywhere. Nothing ever sits on accent → no `accentFg`. |
| **R5** | **Everything visible at once.** No staged disclosure: no accordions, wizards, drawers, "advanced" sections, overflow menus. |

---

## 3. Colour — exactly 11 tokens

Themes are **data**. A scheme is user-authorable. Ship default light + dark as two instances
of one contract. **Do not design "dark mode"** — design the contract, instantiate twice.
The user owns legibility of a scheme they author; do not defensively design around it.

| token | role |
|---|---|
| `bg` | base/window surface. Action tree background. Input rows. |
| `bgAlt` | **recessed relative to `bg`, in both themes.** Control fills, popup fill, left-pane well. |
| `bgHover` | hover fill |
| `bgSelected` | selected fill |
| `line` | every 1px: borders, separators, control borders, indent guides, slot rules, drag insertion line |
| `fg` | primary text: identifiers, action labels, values |
| `fgMuted` | secondary: descriptions, slot labels, units, `+n` |
| `fgDisabled` | disabled, empty states |
| `accent` | **selection + focus only** |
| `error` | invalid action icon, error hints |
| `warning` | warning hints |

**Accent's complete inventory:** 2px tab underline · 2px selected-row bar · focus outline
(`2px, offset -2px`) · checkbox/radio **mark** (border + tick, never a filled box) ·
engaged toggle icon shade. ~2–4 accent marks on screen at any moment.

**Exception:** `AxesStateSeries` needs an 8-colour data-series palette. That is a separate
contract, out of scope. Everything else is these 11.

**Defaults shipped:**

```
light: bg #ffffff  bgAlt #f2f2f4  bgHover #e8e8ec  bgSelected #dcdce2  line #c4c4cc
       fg #17171a  fgMuted #6a6a74  fgDisabled #a6a6b0
       accent #1060c0  error #c0281c  warning #9a5c00
dark:  bg #242429  bgAlt #1b1b1e  bgHover #2e2e34  bgSelected #3a3a42  line #4a4a54
       fg #e6e6ea  fgMuted #94949e  fgDisabled #5c5c66
       accent #58a6ff  error #ff7b6b  warning #e0a63c
```

---

## 4. Sizing

Scaling is **pure zoom** at **100 / 150 / 200%** (everything multiplies).
→ **every dimension must be an integer at 100% AND 150%** → **2px grid, even numbers.**
(13px is illegal: ×1.5 = 19.5.) **All font sizes in px, never pt.**

| | |
|---|---|
| Grid | **2px**. Gaps: **4 / 8 / 12 only** |
| Text | **14px** body/labels/row titles · **12px** secondary/detail |
| Control height | **24px — one height for the entire app.** The `Base`/`Compact` split is *deleted*, not unified |
| Icon | **16px** |
| Indent per level | **16px** |
| Border | **1px** — the sole non-integer at 150%, accepted |
| Radius | **2px on interactive controls only.** Layout containers: **0** |
| Window | 1400×900 target |
| Left pane | min **400px** · Right pane | min **900px** |
| Menu bar 26 · Toolbar 34 · Tab strip 36 · Footer 24 · Body 780 |
| Input row | **48px** uniform + 4px gap = 52px pitch. Unbound rows are the same height |
| Action row | **28px** |

Reference: Fluent body is 14/20, caption 12/16, floor 12px regular. We run one step
tighter, deliberately. R14's 16px (pointSize 12) is two steps *above* Fluent body.

---

## 5. Type

**IBM Plex Sans + IBM Plex Mono.** SIL OFL 1.1. True superfamily (mono derived from sans).
Bundle **OTF/TTF in the Qt resource file** — not a system font. Source: `github.com/IBM/plex`.
**Weights: 400 and 600 only.**

**Mono is mechanical, not semantic** — only where character-cell alignment or fixed-width
readout matters: spin values (`-1.0000`, `0.0500`), axis values, thresholds, GUIDs, VID/PID.
Row titles (`Button 8`) stay sans. Key combos (`F8`, `Left Shift + F7`) stay sans — they do
not align in a column. Do **not** invent a "mono = machine, sans = human" rule.

**Bold and italic are dropped.** Use SemiBold for emphasis.

---

## 6. Icons

**Bootstrap Icons 1.13.1. MIT. 16px.** Native 16×16 viewBox, **filled paths, no stroke**,
`currentColor`.

**Ship as individual SVG files, NOT the webfont.** R14 renders icons as font glyphs
(`font.pixelSize: 24` on a Text element) — *that* is what is replaced. The set stays.
No `font.pixelSize`, no font fallback, no glyph metrics.

- `currentColor` → an icon inherits `fg`/`fgMuted`/`error`/`warning`/`accent` from context.
  Never a per-icon colour.
- **Chips carry no icons** — 12px is too small to read a glyph.
- **Accent-shading an icon is a *state* channel only** (canonical case: Active toggle).
- Plugin authors ship SVG to the same convention: 16×16 viewBox, filled, single colour.
- The ~39 glyphs must be **curated deliberately** for a shared grammar. R14's were picked
  one at a time (speedometer / joystick / plus-square) and read as noise.

---

## 7. Widgets

| widget | means | examples |
|---|---|---|
| **Checkbox** | on/off, yes/no | `Press`, `Release`, `Symmetric`, `Invert activation` |
| **Radio** | 2–3 exclusive, all visible | `Treat as`, `Absolute/Relative`, `4 way / 8 way` |
| **Toggle button** | armed/engaged state | `Rec`, toolbar `Active` |
| **Push button** | command | `Invert Curve`, `New action sequence` |
| ~~**Switch**~~ | **DELETED APP-WIDE**, including Options | — |

- **Checkbox/radio checked = accent border + accent mark. Never a filled box** (R4).
- **`Invert Curve` is a command, not a state** → push button.
- **The action selector is a menu button, NOT a combo.** No value, no selection state,
  label never changes (`Add action ▾` before and after). Every other `▾` in the app is a
  real value selector; this is the sole exception. One act, not select-then-click.

---

## 8. Right pane — the action tree

**Two recursive elements: the action row and the slot header.**

### Action row (28px)

`[chevron 16] [type icon 16] [name] [TriggerMode?] [error?] [remove]`

- **Type icon is the drag handle.** `cursor: grab`. Zero extra columns.
- **Name = plain text, not a bordered field.** 14px, 1px **transparent** border that takes
  `line` + `bgAlt` on hover. Border always exists → nothing moves. *(Knowing R1 exception.)*
- **The action row has NO hover state of its own.** It is a container of controls. Each
  control answers for itself. A full-width band drowns the name field's 1px border.
- TriggerMode only when `actionBehavior === "button" && canChangeActivation`.

### Slot header (24px) — scaffolding, not content

`[12px fgMuted label] [1px line rule → flex] [Add action ▾]`

| | |
|---|---|
| `Add action` at rest | 12px `fgMuted`, **no chrome**: no background, 1px transparent border |
| on hover | **1px `line` border + `fg` text. NO fill.** Only an edge appears |
| gap label→caret | **8px** |
| hit height | **24px** |
| accent | **never** — it repeats per slot |

**The binding header's `Add action` is a bordered button, deliberately.** Chrome above the
tree is chromed; scaffolding inside it is not. It appears once per sequence, not six times.

### Grammar

An action's **config**, **slot headers** and **child actions** all sit **one 16px step in**
from its header, sharing one 1px guide.

- **Config comes first and is unlabelled.** It is simply what is under the header.
- **A slot header is the only thing that says "actions live below me."**
- **Depth 0 has no indent.**

```
▾ ⬦ Condition ──────────────────────────── [×]
│  When [All ▾] of the following conditions are met      Add condition ▾
│  [Rec] Joystick - HOTAS Warthog — Button 3  [Press ▾]  [×]
│  True ───────────────────────────────────  Add action ▾
│  ▾ ⬦ Landing / Lights ─────────────────── [×]
│     [vJoy Device 1 ▾] [Hat 3 ▾]                  ← leaf: indent, no guide
│  False ──────────────────────────────────  Add action ▾
│  ▾ ⬦ Power management ─────────────────── [×]
│  │  Button mode (•)4 way ( )8 way
│  │  North ───────────────────────────────  Add action ▾
│  │  ▾ ⌨ Map to Keyboard ☑Press ☑Release  [×]
│  │     Key combination [Rec] F8                  ← leaf: indent, no guide
```

### Guides

> **A guide exists to group child actions. No children → no guide.**

- A body holding **only config** gets the 16px indent and **no line**.
- It still **reserves** the guide's 1px as a `transparent` border → config aligns exactly
  with a guided sibling's, and every dimension stays even.
- Result: **the guides are a map of exactly where the branching is.**

### Action config

- **Each action owns its own layout.** Plugin authors are expected to exhibit judgement.
- **Align within an action, not across actions.** Labels left-align, controls to one column.
  Raggedness across actions is accepted. **No global label column.**
- Sentence-case labels, no colons.
- **Inline-sentence configs are permitted**: `When [All ▾] of the following conditions are met`
  is a sentence, not a row. Do not force it into `Mode: [All ▾]`.

### Sequences

- An input carries N **independent** action sequences.
- Binding header: `[grip] [description ______] Treat as (○)Button (•)Hat [Add action] [!] [×]`
- `Treat as` = **radios** (≤2 options, both visible). Axes and hats only; buttons have none.
- **Separated by 8px of space + each sequence's 8px padding. NO rule between them.**
  Each is an independent tree; a line implied they were rows of one list.
- `New action sequence` = ordinary push button at the bottom. Not filled.

### Drag & drop

- **Grab the type icon** (`cursor: grab`).
- **Drop targets = row-edge bands** (hit-test upper/lower half of each row, ~12px),
  **independent of the gap**. Not gap-dwellers.
- Feedback = **2px insertion line in `line`**. Not accent.
- **No parting animation.** The drag ghost + insertion line is enough.

---

## 9. Left pane — the input list

- Pane = `bgAlt` (recessed well). Rows = `bg`, 1px `line` border, 2px radius, free-standing
  buttons with 8px side margin, 4px gap.
- **Row 1:** identifier (left, **always in full, never trims**) + description (**right-aligned**,
  12px `fgMuted`, ellipses).
- **Row 2:** chips.
- Identifiers are long and compound: `Button 4 - Top Right Button`, `Slider - Throttle`,
  `Hat 1 - POV Hat`.
- **Description = accumulated action names the user MODIFIED** (defaults are not
  accumulated). So description = intent; chips = structure. **They never duplicate.**
  No actions → no description, and a 48px empty row is *complete*, not truncated.
- **Chips: flat, full names, no icons, `+n` overflow.**
  **`+n` appears only on genuine overflow** — render all, measure, drop only if they do not
  fit. `X Axis` (4 actions) shows all four at 400px; `Hat 1` (8) overflows.
  **No abbreviations.** The nested formula notation and `image://action_summary` both die.
- Hover popup showing the full tree = future work; reserve for it.
- Options → `Action sequence information` drives chip display (`Full` / `None`). Existing
  setting; do not add a new one.
- **Selection = `bgSelected` + a 2px accent bar at the row's left edge.** Two channels.

---

## 10. Shell

```
File | Tools | Help                                                     (26)
[New][Save][Load][Active][Input Viewer][Options] ... Configuring mode:[▾] (34)
[Dev1][Dev2][Dev3][Keyboard][Logical Device] │ [Scripts][Settings]      (36)
├────────────── 400 ───────────┼──────────── ≥900 ──────────────────────┤
│ input list                   │ action tree                       (780)│
State: Running   Editing: Default   Running: Combat                 (24)
```

**Tabs** — device tabs and Scripts/Settings are **one exclusive selection set**, one control
type. Active = **2px accent underline + SemiBold + `bgSelected`**. A **1px vertical rule**
separates the groups; grouping carries the "different extent" meaning.
**No greying** (not-current ≠ unavailable). **No icons.** **Never accent-filled.**

**Toolbar** — `Configuring mode` stays exactly where it is. It is an editor control ("which
mode am I authoring?"). Keep its label; users repeatedly assumed it switched the live mode.

**Footer** — `State: Running` · `Editing: Default` · `Running: Combat`.
`Executing mode` is a runtime readout. **Adjacency is the entire message: no divergence
warning, no icon, no tone shift.** Divergence is routine, not an error.

---

## 11. Multi-input actions (Merge Axis, Dual Axis Deadzone)

- One library item, **two hosts**. Declares its sources as properties (`axis1-guid/axis1-axis`).
- **Assignment is a two-location operation**: add on axis 1, assign slot 1; then navigate to
  axis 2, add the same instance, assign slot 2. The assign button **only ever assigns the
  currently selected input**.
- **Drift is accepted** (an action can outlive its declaration). Removal is unimplemented and
  not a priority. **Do not design a marker, bracket or annotation for it.**
- Both carry `activation-mode: disallowed` → **no TriggerMode, ever.** Reserve no space.

**Render as a labelled group + N source rows:**

```
Merged axes                                     ← the group label IS the message
  1   CH PRO PEDALS USB — X Axis      [assign]
  2   Not assigned — open the second axis and add
      this merge instance there to assign it.   ← instruction as default value
```

- **An unassigned source row is a first-class state carrying its instruction.** This is the
  whole feature; everything else is a readout.
- **One assign widget.** R14 uses `⦿Rec` in one and `↻` in the other for the same operation.
- Wording is per-plugin (`Merged axes` is Merge Axis's; the deadzone needs its own). The
  **pattern** is reusable, the string is not.
- **One canonical input identifier formatter, every context**, scoped `withDevice` true in
  configs, false in the left pane. R14 prints `Axis 1` in config and `X Axis` in the pane.

**Flagged, unsolved:** `merge-axis` has two editable names — `label` (the shared instance, in
the combo) and `action-label` (this node, in the header). One is shared, one is not, and
nothing says which. **Report it; do not invent a fix.**

---

## 12. Checks

Mechanical, no taste required. Run them.

1. **Grep for hex colours.** Any hex outside the 11-token table = defect.
2. **Grep for odd px.** Every dimension even at 100%. `1px` borders are the sole exception.
3. **Grep for** `box-shadow`, `gradient`, `rgba(`, `color-mix`, `opacity` → must be zero.
4. **Cover the labels in the tree.** You must still be able to point at where each slot starts.
5. **Count accent marks on screen.** ~2–4. Any accent *fill* = R4 violation.
6. **Hover any row.** If anything appears, disappears, moves or resizes — R1 violation.
   (Only sanctioned exception: the action-name field's border.)
7. **Font sizes present** must be exactly {12, 14}.
