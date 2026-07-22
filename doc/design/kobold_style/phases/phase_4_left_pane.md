# Phase 4 — Left pane (the input list)

**Goal:** build the left-hand list of inputs for the selected device (SPEC §9): a recessed well of
free-standing rows, each showing an input's identifier, an optional description, and structure chips.

**Prereqs:** main guide §0–§5. **Depends on:** Phases 1–3. **Enables:** device navigation; feeds the
right pane's selection.

---

## Concepts for this phase

**What the left pane shows.** For the currently-selected device, a vertical list of its inputs
(axes, buttons, hats). Power users have 100–200 of these, so this is a real list-performance surface —
use a `ListView` with delegate recycling (`reuseItems: true`) and shallow delegates.

**"Recessed well."** The pane background is `bgAlt` (a colour that is *recessed* relative to `bg` in
both themes). The rows sit *on top* as `bg`-coloured cards with a 1px `line` border and 2px radius, so
they read as free-standing buttons floating in the well — achieved with colour + border only, **no
shadow** (R2).

**Identifier vs. description vs. chips — three different things, never duplicated:**
- **Identifier** (row 1, left): the input's compound name, e.g. `Button 4 - Top Right Button`,
  `Slider - Throttle`, `Hat 1 - POV Hat`. **Always shown in full; never trimmed.**
- **Description** (row 1, right, 12px `fgMuted`, ellipsised): the accumulated names of actions the
  user *modified* (defaults are not accumulated). So description communicates **intent**. If no
  actions were modified, there is **no description** — and a 48px empty row is *complete*, not
  truncated.
- **Chips** (row 2): flat labels showing the **structure** — full action names, no icons, no
  abbreviations, with a `+n` overflow marker. So chips communicate **structure**.
- **Intent (description) and structure (chips) never say the same thing.**

**`+n` overflow — measure, don't guess.** Render *all* chips, measure, and drop only the ones that
genuinely don't fit, replacing them with `+n`. Example: an axis with 4 actions shows all four at
400px; a hat with 8 overflows and shows `+n`. Do not pre-truncate by count.

**Selection = two channels.** A selected row uses `bgSelected` fill **and** a 2px `accent` bar at the
row's left edge. Both, together.

---

## What you're building

### `InputRow.qml` (internal component)

- Fixed height **48px** (× scale), **4px** gap between rows (52px pitch). Unbound rows are the same
  48px height — an empty row is complete.
- Card: `color: Theme.bg`, `border` 1px `Theme.line`, `radius: Metrics.radius`, 8px side margin.
- **Row 1:** identifier left (`fg`, 14px, **no elision — always full**) + description right
  (`fgMuted`, 12px, elided) — but description is empty when no modified actions exist.
- **Row 2:** the chips row (see below).
- **Selection:** when selected, `color: Theme.bgSelected` **and** a 2px `Theme.accent` bar anchored to
  the row's left edge.

### Chips

- Flat labels: `bgAlt` (or `bg`) fill, 1px `line`, `fg` text, **full action names**, **no icons**
  (12px is too small to read a glyph), **no abbreviations**.
- **Overflow:** lay them out, measure available width, and show `+n` only for chips that don't fit
  (`fgMuted`). `+n` appears **only** on real overflow.
- Chip display is driven by the existing Options setting `Action sequence information` (`Full` /
  `None`) — **do not add a new setting.**

### The list

- `ListView` over the selected device's inputs, `reuseItems: true`, delegate = `InputRow`.
- Pane background `bgAlt`.

---

## Definition of Done

- [ ] Pane is `bgAlt`; rows are `bg` cards with 1px `line`, 2px radius, 8px side margin, 4px gap — no
      shadow.
- [ ] Identifier always shows in full (never elided); description is right-aligned `fgMuted` 12px and
      **absent** when no actions were modified.
- [ ] An input with no actions renders as a complete 48px row, not a truncated one.
- [ ] Chips show full names, no icons, no abbreviations; `+n` appears only when measured chips overflow
      (verify: 4-action axis shows all at 400px; 8-action hat overflows).
- [ ] Selected row shows `bgSelected` **and** a 2px accent left bar.
- [ ] Description (intent) and chips (structure) never duplicate content.

## Watch-outs

- Don't truncate chips by count — render, measure, then drop. This is the single most common way to
  get §9 wrong.
- The empty row is *complete*. Don't add placeholder text or greying to "fill" it.
- Reserve for a future hover popup (full tree) but **don't build it** now.
- Keep delegates shallow for scroll performance; read tokens as cached properties (see Phase 1 perf
  note).

**Spec refs:** §9. **Guide refs:** §4.6, §5.
