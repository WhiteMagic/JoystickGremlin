# Phase 3 — Playground + lint

**Goal:** a permanent gallery that renders every control across the full state/theme/zoom matrix, plus
the CI lint and unit tests that mechanically enforce the design rules. This is both the implementation
loop for later phases and the enforcement home for SPEC §12.

**Prereqs:** main guide §0–§5. **Depends on:** Phases 1–2. **Enables:** confident work on 4–7.

---

## Concepts for this phase

**Playground / gallery.** A small standalone QML app whose only job is to display every component in
every state, so a human can eyeball correctness and an LLM can verify what it just built. Think of it
as a living catalogue: implement a control → it appears here → check it → move on. It is **not a
throwaway**; it stays in the repo forever as the reference and the visual-check surface.

**The verification matrix.** The bugs in a token/metrics system hide in *combinations*, not single
states. So the gallery must let you view every control across three axes at once:
- **State:** rest, hover, pressed, checked/selected, focused, disabled, error.
- **Theme:** both shipped schemes (toggle live).
- **Zoom:** 100 / 150 / 200 % (toggle live — this exercises the `Metrics` scaling).

**Lint (static checks).** Plain text/regex scans over the QML source that fail the build when a
forbidden pattern appears. They turn SPEC §12's "grep for X" into automated gates. They catch raw
hex, raw px, shadows, gradients, etc. — drift that a human won't reliably spot.

**Metrics-resolution test.** A unit test that *computes* every `Metrics` token at each of the three
scales and asserts the result is an integer (or a declared exception like a hairline). This catches
grid violations that are invisible to the eye — e.g. a token that lands on 1.5 px at 150% because
someone used an odd base number.

**Why no screenshots yet.** Pixel-diff regression tests are deferred (they generate baseline churn
while the design is still moving). During this phase, verification = the gallery (human eyes) + lint +
the resolution/schema tests. See guide §7 for the trigger to add screenshots later.

---

## What you're building

### 1. The gallery app (`scripts/gallery.py`)

- Its own `main.qml`. A control panel with: a **theme toggle** (switch the active scheme via
  `ThemeManager`), a **zoom selector** (100/150/200 → drives `Metrics.scale` via the config value),
  and optionally a "disabled" master toggle.
- A scrollable grid/list of **sections**, one per control, each showing that control in every state
  side by side. Label each state.
- Include the tokens themselves: a swatch strip of all 11 colours, and text specimens (Sans/Mono ×
  400/600 × 12/14) so type and colour regressions show up immediately.
- As later phases add components (InputRow, ActionRow, chips, shell bits), add a gallery section for
  each. The gallery grows with the system.

### 2. Lint scripts (`scripts/`)

Scan `.qml` (and `.py` where relevant). Rules — mirror guide §7 / SPEC §12:

- **Raw hex colour** anywhere outside `themes/*.json` → defect (must be `Theme.*`).
  Regex idea: `#[0-9a-fA-F]{3,8}\b` in `.qml`.
- **Raw px in styling positions** (width/height/spacing/margins/radius/border width/font size) that
  isn't a `Metrics.*` reference → defect. (Allow `0`, `-2` focus offset, and `1` only where a literal
  hairline is explicitly sanctioned — keep the allowlist tiny and documented.)
- **Forbidden effects:** `box-shadow`, `gradient`, `Qt.rgba(`, `color-mix`, `layer.effect` used for
  shadow, `opacity` used as a tint → must be zero.
- **Font:** `pointSize`/`pt` → defect (px only). `font.pixelSize` literals must be `{12,14}` and come
  from `Metrics`.

### 3. Unit tests

- **Metrics resolution:** enumerate every `Metrics` token; for `scale ∈ {1.0, 1.5, 2.0}` assert
  integer-or-declared-exception. This is the check a human cannot do by looking.
- **Scheme schema:** every shipped scheme validates against `scheme.schema.json`; exactly 11 colour
  keys; no alpha; `meta.appearance` valid if present.

---

## Definition of Done

- [ ] Gallery runs; theme and zoom toggles work live and visibly re-render every control.
- [ ] Every implemented control appears with all its states, in a labelled section.
- [ ] Lint is working and **fails on a planted violation** (add a raw hex, an odd px, a shadow → red).
- [ ] Metrics-resolution test **fails on a planted 13 px token**; scheme-schema test fails on a
      planted bad scheme.
- [ ] A human can look at the gallery in both themes × three zooms and sign off.

## Watch-outs

- Keep the gallery a first-class app with its own entry point — resist the urge to make it a
  throwaway snippet; later phases depend on it.
- The lint's px allowlist is where discipline erodes. Keep it minimal and comment every entry.
- No screenshot tests in this phase (deferred). Don't add baseline images now.

**Spec refs:** §12. **Guide refs:** §7.
