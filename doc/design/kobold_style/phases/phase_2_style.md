# Phase 2 — Custom Qt Quick Controls style

**Goal:** every *basic* control (button, checkbox, radio, dropdown, menu, text field, …) renders in
the new design, everywhere, with no changes at call sites.

**Prereqs:** main guide §0–§5. **Depends on:** Phase 1 (tokens must exist). **Enables:** all UI phases.

---

## Concepts for this phase

**What "a custom style" actually is.** In Qt Quick Controls, a *style* is a directory of QML files,
each named after a control (`Button.qml`, `CheckBox.qml`, …). When you write `import QtQuick.Controls`
and use a `Button`, Qt renders it using *your* `Button.qml` if your style provides one, or falls back
to the built-in `Basic` style if it doesn't. So you customise the *look* of every control app-wide by
supplying these files — **without touching any code that uses the controls.** That is the entire point
of choosing a custom style over hand-built controls.

**Template vs. style.** Each of your style files roots a *template* type from `QtQuick.Templates`
(imported `as T`), e.g. `T.Button`. The template is the invisible machinery: it tracks state
(hovered, pressed, checked, focused, enabled), handles keyboard/mouse, exposes the right properties,
and provides accessibility. **You do not reimplement any of that.** You only supply the *visuals* by
assigning three well-known child items:

- **`background`** — the fill/border behind the control.
- **`contentItem`** — the label/text/icon in front.
- **`indicator`** — the extra mark for controls that have one (the checkbox tick, the radio dot, the
  combobox arrow).

Everything else (size, hit area, signals) comes from the template. You read the template's state
properties (`control.hovered`, `control.checked`, `control.down`, `control.visualFocus`,
`control.enabled`) to pick token colours.

**States you must handle** (from Phase 1 tokens): rest (`bg`/`bgAlt`), hover (`bgHover`), pressed
(`down`), checked/selected (`bgSelected` and/or the accent mark), focus (a 2px accent outline, offset
-2px), disabled (`fgDisabled`), and error where relevant (`error`). Per R1, none of these may change
layout/size — only fills/borders/marks.

**The accent rule (R4) is a style-level invariant here.** Checked checkboxes/radios show an **accent
border + accent mark, never a filled box.** No control ever gets an accent *fill*. There is no primary
button. Accent appears only as: the tab underline, the selected-row bar, the focus outline, the
checkbox/radio mark, and the engaged-toggle icon shade.

---

## What you're building

### Style registration (do this once, in the entry point)

```python
QQuickStyle.setStyle("Kobold")          # BEFORE the engine loads any Controls-importing QML
QQuickStyle.setFallbackStyle("Basic")       # anything you don't implement falls back to Basic
```
The `Kobold` directory must be discoverable on the QML import path (guide §4.7). If you see
"current style does not support customization of this control", the style dir isn't registered/on the
path — fix that before anything else. **`CONFIRM-2`:** verify the exact 6.11 packaging against
*Creating a Custom Style*.

> **Naming note — the style and the namespace root are both called `Kobold`.** These are two
> different things that must not resolve to the same directory. The **style** is the module/dir
> `Kobold` holding the control templates (`Button.qml`, …); the **token/component modules** are its
> submodules `Kobold.Foundation`, `Kobold.Controls`, `Kobold.Internal` (nested directories beneath).
> `Kobold` and `Kobold.Foundation` are distinct QML modules and coexist fine (exactly as `QtQuick`
> and `QtQuick.Controls` do), but `QQuickStyle.setStyle("Kobold")` must find the *style* dir, not the
> namespace root — so ensure the style dir contains the control files (and a `module Kobold` qmldir)
> and that the submodule dirs don't shadow it on the import path. Fold this into the `CONFIRM-2`
> verification.

### Control templates (initial set)

Each file lives in the `Kobold/` style dir and follows this skeleton (Button shown):

```qml
import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation                      // Theme, Metrics, FontType

T.Button {
    id: control
    implicitHeight: Metrics.ctrlH               // 24px, the one app-wide control height
    implicitWidth: Math.max(Metrics.ctrlH * 2, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM
    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: Metrics.radius                  // 2px on interactive controls
        color: !control.enabled ? Theme.bgAlt
             : control.down     ? Theme.bgSelected
             : control.hovered  ? Theme.bgHover
             :                    Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line
        // focus ring: a 2px accent outline, inset -2px (R4: accent = state only)
        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
        }
    }
}
```

Implement, at minimum:

- **`Button`** and **`ToolButton`** — push commands. Never accent-filled.
- **`CheckBox`** — the `indicator` is an accent-bordered box with an accent **tick** when checked;
  **never a filled box**. Unchecked = `line` border, no fill change on layout.
- **`RadioButton`** — accent ring + accent **dot** when checked; 2–3 options, all visible.
- **`ComboBox`** — the real value-selector (`▾`). Popup fill = `bgAlt`, 1px `line` border, **no
  shadow** (R2). Selected item uses `bgSelected`.
- **`Menu` + `MenuItem`** — same opaque-fill-plus-1px-border rule, no elevation.
- **`TextField`** — `bgAlt` fill, `line` border, `fg` text, `accent` focus.
- **`SpinBox`** — value shown in **mono** (`FontType.mono`) since it's a fixed-width readout.
- **`ScrollBar`**, **`ToolTip`** — minimal, 1px border, opaque, no shadow.

> **Not restyled primitives, but app components (decide here, build later):** the action-selector
> "menu button" (SPEC §7 — no value, label never changes, *not* a combo) and toggle buttons
> (armed/engaged) are app components, likely in Phase 5/7, not overrides of a stock control.

---

## Definition of Done

- [ ] Each implemented control renders from tokens in **both** shipped themes and **all three** zoom
      levels (100/150/200%), with correct rest/hover/pressed/checked/focused/disabled/error visuals.
- [ ] Checkbox and radio show an accent **mark**, never a filled box (R4).
- [ ] Focus is a 2px accent outline at offset -2px; nothing moves/resizes on focus or hover (R1).
- [ ] Zero shadows, gradients, translucency anywhere (R2); popups are opaque fill + 1px `line`.
- [ ] All heights resolve to the single 24px control height (× scale); no raw px, no raw hex.

## Watch-outs

- **Never reimplement template behaviour** — only `background`/`contentItem`/`indicator`. If you find
  yourself handling key events or state machines, stop; the template already does it.
- Don't set explicit widths/heights that fight the 24px height or the 2px grid — drive from `Metrics`.
- The combobox popup and menus are the classic place a shadow sneaks in. There is no shadow. Ever.
- Read the template's own state props (`control.down`, `control.hovered`, `control.checked`,
  `control.visualFocus`, `control.enabled`) — don't invent your own MouseArea/hover tracking.
- **Switch the app-wide default font here.** Phase 1 deliberately left `self.setFont(...)` on
  `"Segoe UI"` (`joystick_gremlin.py`) and only registered the IBM Plex faces with `QFontDatabase` —
  changing the global font before the Kobold style rendered anything would have reflowed every
  existing Universal-styled control for no visible benefit. Once Phase 2's controls actually render,
  flip `self.setFont(...)` to IBM Plex Sans (`FontType.sans`/`FontType.regular`) as part of this
  phase's own Definition of Done — don't forget it.

**Spec refs:** §7, §2 (R1/R2/R4). **Guide refs:** §4.5.
