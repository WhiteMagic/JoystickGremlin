# Kobold: UI Style and Theming

Kobold is Joystick Gremlin's custom Qt Quick Controls 2 style: a set of control templates plus token singletons. Color is themeable JSON data while dimensions, fonts and icons are fixed constants and are not themeable.

## Rules

- **No shadows.** A floating surface (`Menu`, `ComboBox` popup, `ToolTip`) is an opaque fill plus a 1px border, nothing else.
- **No derived colours.** Every color is a `Theme.*` token. No alpha, `Qt.rgba`, `Qt.lighter`/`darker`/`tint`, `color-mix`, gradients, or `opacity` used as a tint.
- **Hover never changes layout or size.** It may repaint freely. Fills, borders, and overlays appearing and disappearing are all fine, so long as nothing reflows or resizes. A border that must show on hover is therefore always present and merely transparent at rest.
- **Accent is state, not decoration.** Selection, focus, checkbox/radio marks, an engaged toggle, and a live value or position. No primary button, no `accentFg`, because nothing ever sits on accent.
- **No staged disclosure.** No accordions, wizards, drawers, "advanced" sections or overflow menus.

## Tokens

Values live in `Theme`, `Metrics` and `FontType`. Look them up there, they are closed sets.

### Color

Access values through `Theme.*`, never directly from `themeManager`. The only exception is `Metrics` reading `themeManager.uiScale`.  `Theme.qml` is a deliberately thin facade over the Python `ThemeManager` so that consumer reads stay on the QML side of the boundary. Do not add a `Theme.color(name)` accessor either.

### Color Schemes

A scheme is one JSON file under `style/themes/`, validated at load against `kobold-colors.schmea.json`. It defines exactly the 11 colour keys, 6-digit hex, no alpha, and a required `meta.appearance` of `light` or `dark`.

| token | role |
|---|---|
| `bg` | Base/window surface. Action tree background. Input rows. |
| `bgAlt` | **Recessed relative to `bg`, in both themes.** Control fills, popup fill, left-pane well. |
| `bgHover` | Hover fill |
| `bgSelected` | Selected fill |
| `line` | Every 1px: borders, separators, control borders, indent guides, slot rules  |
| `fg` | Primary text: identifiers, action labels, values |
| `fgMuted` | Secondary: descriptions, slot labels, units, `+n` |
| `fgDisabled` | Disabled, empty states |
| `accent` | **Selection + focus only** |
| `error` | Invalid action icon, error hints |
| `warning` | Warning hints |

### Dimensions

`Metrics` holds every size. Three things matter beyond looking a value up:

- There are exactly three gap tiers: `gapS`, `gapM`, `gapL`. A spacing that is none of them is a defect, and there is nothing above `gapL`.
- `controlHeight` is a single height for every control in the app. Adding a second one is a design change, not a tweak.
- `hairline` and `accentMark` do not scale by the usual rule. They use explicit per-zoom tables. A 2px line is `2 * Metrics.hairline`, never a new token.

### Type and Icons

- `FontType` provides two families, `sans` and `mono`, and two weights, `regular` and `semiBold`. Sizes come from `Metrics.textBody` and `Metrics.textDetail`, the only two, always in pixels. There is no bold and no italic, emphasis is semi bold.

- Mono is mechanical, not semantic. Use it where character cells have to line up: spin box values, chart labels, GUIDs. Row titles and key combinations stay sans, because they do not sit in a column.

- Icons are 16x16 `currentColor` SVGs, recoloured by a Python image provider. Draw them only through `AppIcon`, giving it a `name` and a `role`. Its `source` is a binding, so a scheme change recolours it on its own. Never add an imperative refresh.

## Scaling

Three scalings exist, 100%, 150%, and 200% as multiplied integer tokens. Never a scene-graph transform, and never `QT_SCALE_FACTOR`. The only invariant is that every token resolves to a whole pixel at every scale.

- Never call `Metrics.dp(N)` in a delegate, read a named token, or a `readonly property` computed once on the file's root. Evaluating `Metrics.dp(N)` every frame would be disastrous for performance.
- A one-off size does not become a token, a dialog's own width, a column width: inline `Metrics.dp(N)`, or a `readonly property` on that file's root if it recurs within the file. Growing the token list to dodge the raw-pixel lint is the mistake.

## Icons

- Bootstrap Icons, native 16×16 viewbox, filled paths, no stroke, `currentColor`.
- Ship as individual SVG files, NOT the webfont.
- `currentColor` → an icon inherits `fg`/`fgMuted`/`error`/`warning`/`accent` from context. Never a per-icon colour.
- Chips carry no icons — 12px is too small to read a glyph.
- Accent-shading an icon is a *state* channel only (canonical case: Active toggle).
- Plugin authors ship SVG to the same convention: 16×16 viewbox, filled, single colour.
- A shared collection of icons is accessible by name.

## Modules

- **Kobold style**: `style/qml/Kobold/*.qml`, the control templates. Selected via `QQuickStyle.setStyle("Kobold")`, doesn't need to be imported.
- **`Kobold.Foundation`**: `Theme`, `Metrics`, `FontType`, `AppIcon`. Used by everything.
- **`Kobold.Controls`**: Files that do not depend on other `Kobold` types, i.e. basic control widgets.
- **`Kobold.Composites`**: Assemblies of `Kobold` types, holding no application state, i.e. dedicated but reusable widgets.
- **`Kobold.Views`**: Application-only complex assemblies with dedicated singular purpose, plugins must never import this.

Each tier's `qmldir` imports the one below, so one import line gets everything under it. Type names must not collide with `QtQuick.Controls`, which is why the kit has no `Button`, `CheckBox` or `ComboBox`, and why the list component is `ScrollList`, never `ListView`.

## Writing a control template

Root the matching `QtQuick.Templates` type imported `as T` and assign only `background`, `contentItem`, `indicator` (and `up`/`down.indicator`, `handle`, `popup` where they exist). The template already tracks state, handles keyboard and mouse, sizes the control and provides accessibility. Never reimplement template behaviour. If you are writing a `MouseArea` or a key handler in a template, stop. Read `control.hovered`, `control.down`, `control.checked`, `control.visualFocus`, `control.enabled`, `control.activeFocus`.

States change fills, borders and marks only, never layout or size. A checked checkbox or radio is an accent border plus an accent mark, never a filled box.

## Never in a `.qml` file

- A raw hex colour, or a raw pixel value in a styling position
- `Qt.rgba`, `Qt.lighter`, `Qt.darker`, `Qt.tint`, `color-mix`, or a gradient
- `layer.effect` used for a shadow
- `opacity` used as a tint. Using it to genuinely show or hide something is fine
- `pointSize` or `pt`, or a `pixelSize` that did not come from a `Metrics` font token

## Verification

```bash
poetry run python scripts/lint_style.py              # raw hex/px, effects, pointSize
poetry run pytest test/unit                          # the CI gate; includes the lint
.venv/Scripts/pyside6-qmllint.exe -I style/qml FILE  # type resolution, layout misuse
```

`lint_style.py` is line-based and has blind spots. It does not catch `opacity` as a tint, and its property list is case-sensitive, so `Layout.preferredWidth: 100` passes. A clean run is not a clean file. Never widen its literal allow-list to make a check pass.

`pyside6-qmllint` catches what it cannot, notably `width`/`height` set on a layout-managed item. Trust it over the IDE's live diagnostics, which lag on `Kobold.*` imports. Its `[unqualified]` warnings on the four context properties (`backend`, `uiState`, `signal`, `themeManager`) are expected and unavoidable; `[unqualified]` on a type's *own* properties is a false positive.
