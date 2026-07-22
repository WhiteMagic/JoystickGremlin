# Phase 6 — Action-tree scaffolding

**Goal:** the core-owned structure of the right pane's action tree (SPEC §8): the recursive action
rows, slot headers, indentation, and guide lines — **without** the plugin config bodies (those are
Phase 7). This is the most grammar-dense phase; read SPEC §8 in full alongside this.

**Prereqs:** main guide §0–§5, especially §5 (domain model). **Depends on:** Phases 1–3 (2 for
controls). **Enables:** Phase 7 (plugins fill the bodies this phase frames).

---

## Concepts for this phase

**The tree renders the action data model** (guide §5). An **action** is the one node type: a name, a
type config, and N named **slots**; slots can contain child actions. The tree is recursive: an action
contains slots, slots contain actions, and so on.

**Core owns the scaffolding; plugins own only the config body.** This phase builds *everything the
core draws* around and between actions — the chevron, the type icon, the name, the remove button, the
slot headers, the indentation, and the guide lines. The **config body** ("what's under the header")
is supplied by the plugin (Phase 7). Framing this cleanly here is what lets plugins be simple and
unable to break the tree.

**Two recursive elements:** the **action row** and the **slot header.** Learn both precisely:

- **Action row (28px)** — `[chevron 16] [type icon 16] [name] [TriggerMode?] [error?] [remove]`.
  - The **type icon is the drag handle** (`cursor: grab`). No separate drag column.
  - The **name is plain text, not a bordered field** — 14px, with a **1px transparent border** that
    takes `line` + `bgAlt` colour **on hover**. The border always exists (so nothing moves when it
    appears) — this is the **single sanctioned R1 exception**.
  - The action row has **no hover state of its own.** It is a container of controls; each control
    answers for itself. A full-width hover band would drown the name field's 1px border — don't add
    one.
  - `TriggerMode` appears only when `actionBehavior === "button" && canChangeActivation`.

- **Slot header (24px)** — `[12px fgMuted label] [1px line rule → flex] [Add action ▾]`.
  - This is **scaffolding, not content.** The `Add action` at rest is 12px `fgMuted` with **no
    chrome** (no background, 1px *transparent* border). **On hover:** a 1px `line` border + `fg` text
    appear — **only an edge**, no fill. 8px gap between the label and the caret. 24px hit height.
  - **Accent is never used here** (it would repeat per slot). The slot header is the *only* thing
    that says "actions live below me."

**Depth, indentation, guides — the heart of §8:**
- An action's **config, slot headers, and child actions all sit one 16px step in** from the action's
  header, sharing one 1px vertical **guide** line.
- **Config comes first and is unlabelled** — it is simply what's under the header.
- **Depth 0 has no indent.** `RootAction` is invisible (no config, no indent); top-level actions sit
  at depth 0.
- **A guide exists *only* to group child actions.** No children → **no visible guide line.** But the
  body still **reserves** the guide's 1px as a *transparent* border, so a config-only body aligns
  exactly with a guided sibling's, and every dimension stays even.
- Result: **the visible guides are a precise map of where the tree branches.** A test: cover the
  labels — you should still be able to point at where each slot starts.

**Binding header & sequences:**
- An input carries **N independent action sequences.** Each sequence is its own tree.
- Binding header: `[grip] [description ____] Treat as (○)Button (•)Hat [Add action] [!] [×]`.
  `Treat as` = **radios** (≤2 options, both visible; axes and hats only; buttons have none).
- The **binding header's `Add action` is a bordered button** (deliberately — chrome above the tree is
  chromed), unlike the slot-header `Add action` inside the tree (scaffolding, edge-on-hover only).
- Sequences are **separated by 8px of space + each sequence's 8px padding, with NO rule between
  them.** A rule would imply they're rows of one list; they are independent trees.
- `New action sequence` at the bottom is an ordinary push button — **not filled.**

**Drag & drop:**
- **Grab the type icon** (`cursor: grab`).
- **Drop targets are row-edge bands** — hit-test the upper/lower half of each row (~12px), independent
  of the gap. Not gap-dwellers.
- Feedback is a **2px insertion line in `line`** (from `Metrics.insertionLine`) — **not accent.**
- **No parting animation** — the drag ghost + insertion line is enough.

**Special renders:** **Macro steps are NOT child actions** — render them as a **table**. If they look
like nesting, the UI is lying.

---

## What you're building (internal components)

- **`ActionRow.qml`** (28px) — the row layout above, with the plain-text name field (transparent 1px
  border → `line`+`bgAlt` on hover), type-icon-as-drag-handle, conditional `TriggerMode`, conditional
  error icon (`error` colour), remove `[×]`. No full-width hover band.
- **`SlotHeader.qml`** (24px) — label (`fgMuted` 12px) · 1px `line` rule (flex) · `Add action ▾`
  (no chrome at rest, `line` edge + `fg` on hover; never accent).
- **Indentation + guides** — a container that applies the 16px step and draws the 1px guide **only
  when the body has child actions**, otherwise reserves a transparent 1px so alignment holds. This is
  the crux of §8 — get the "no children → no line, but reserve the width" rule exactly right.
- **`BindingHeader.qml`** — grip, editable description, `Treat as` radios, bordered `Add action`
  button, warning `[!]`, remove `[×]`.
- **Sequence container** — stacks N sequences with 8px space + 8px padding and **no rule between**.
- **Drag & drop** — grab type icon; row-edge band hit-testing; 2px `line` insertion line; no
  animation.
- **Macro table** renderer (steps as a table, not nested actions).

Leave a clearly-marked **body slot** where a plugin's config view will mount in Phase 7 (positioned
at the correct indent, sharing the guide).

---

## Definition of Done

- [ ] "Cover the labels" test passes: with labels hidden, you can still point at where each slot
      starts, because the guides map the branching exactly.
- [ ] Depth 0 has no indent; `RootAction` is invisible; each nesting level steps 16px and shares one
      1px guide.
- [ ] A config-only body (no children) shows **no** guide line but still aligns pixel-for-pixel with a
      guided sibling (transparent 1px reserved).
- [ ] The action row has **no** full-width hover band; only the name field's 1px border reacts on
      hover (the one R1 exception).
- [ ] Slot-header `Add action` shows only an edge on hover (no fill), never accent; the binding-header
      `Add action` is a bordered button.
- [ ] Sequences are separated by space + padding with **no rule between**; `New action sequence` is an
      unfilled push button.
- [ ] Drag grabs the type icon; drop uses row-edge bands; feedback is a 2px `line` insertion line (not
      accent); no parting animation.
- [ ] Macro steps render as a table, not as nested actions.

## Watch-outs

- The guide rule is subtle: **no children → no line, but still reserve the 1px transparent border.**
  Skipping the reservation breaks alignment and the even-grid.
- Don't give the action row its own hover fill — it drowns the name field's border.
- Don't put a rule between sequences; don't animate drops; don't use accent for the insertion line or
  the slot-header `Add action`.
- Keep the plugin body slot generic — this phase must not assume anything about a specific action's
  config UI.

**Spec refs:** §8 (read in full), §5. **Guide refs:** §5, §4.6.
