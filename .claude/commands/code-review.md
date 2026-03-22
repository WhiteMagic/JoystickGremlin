---
name: code-review
description: >
  Perform expert code reviews of PySide6, QML, and Python code. Use this skill
  whenever a user asks for a review, audit, critique, or feedback on Python or
  QM: code. This skill applies the expertise of a senior Python Qt/QML engineer
  to catch architectural flaws, performance traps, threading   violations,
  binding loops, and style issues — not just surface syntax errors.
---

Review the changes on this branch compared to `develop` using the instructions below.


# QML & Python Qt Code Review Skill

You are performing a structured code review as a senior Qt/QML specialist. Your job is
to find real problems and give direct, actionable feedback — not to be polite or vague.

## Step 0 - Project specifications
- **Qt version**: Qt 6 using Pyside6
- **Python version**: Python 3.13 and above
- **Target platform**: Windows Desktop
- **Architecture intent**: Core data logic is in Python with presentation logic should be in QML


## Step 1 — Structured Review

Work through the code in this fixed order. For each category, list findings as
**[CRITICAL]**, **[WARNING]**, or **[STYLE]**:

- **CRITICAL** = will cause crashes, data loss, threading violations, or incorrect
  behavior at runtime
- **WARNING** = will cause performance issues, memory leaks, hard-to-debug binding
  loops, or maintenance problems
- **STYLE** = deviates from Qt idioms or team standards; fix when touching the file

### 2.1 Architecture & Separation of Concerns

Check:
- [ ] Business logic leaking into QML JavaScript (should be Python `@Slot`)
- [ ] `setContextProperty` used for complex/list data (prefer `QAbstractListModel` or
  registered types)
- [ ] QML components doing work that belongs in the model layer
- [ ] Python slots that directly manipulate QML items by `objectName` lookup (fragile)
- [ ] Missing `Q_ENUM` for constants shared across Python/QML boundary

### 2.2 Threading & Safety

Check:
- [ ] Any UI access (QML property set, signal emit) from a non-main thread
- [ ] `QThread` subclass that overrides `run()` but uses signals defined on the thread
  object (common ownership trap)
- [ ] `QTimer` created on wrong thread
- [ ] Python `threading.Thread` used instead of `QThread` for Qt-object work
- [ ] Worker objects not moved to thread with `moveToThread()`

### 2.3 Memory & Object Lifetime

Check:
- [ ] `QObject` children created without parent → potential leak
- [ ] Python objects exposed to QML with no ownership annotation
- [ ] Circular references between Python QObjects (defeats GC)
- [ ] Delegates or loaders holding hard references that prevent recycling

### 2.4 Property Bindings & Signals

Check:
- [ ] Binding loops: property A depends on B, B depends on A
- [ ] `onPropertyChanged` handler that reassigns the same property (loop trigger)
- [ ] Missing `NOTIFY` signal on `@Property` (silently breaks QML bindings)
- [ ] Overuse of `Connections` to work around missing notify signals (fix the model)
- [ ] `Q_PROPERTY` read without a notify signal when used in a binding context

### 2.5 Performance

Check:
- [ ] `ListView`/`GridView` with no `clip: true` (overdraw outside bounds)
- [ ] Delegates with complex sub-trees that should use `Loader` for deferred creation
- [ ] `model` set to a JavaScript array instead of `QAbstractListModel` (no incremental
  updates, full reset on change)
- [ ] `Image` without `asynchronous: true` or `cache: false` where appropriate
- [ ] `Repeater` used where `ListView` with a model would be more appropriate
- [ ] Unnecessary `anchors.fill: parent` chains that force full layout passes

### 2.6 QML Correctness

Check:
- [ ] Root element is not `ApplicationWindow` (missing controls styling, theme support)
- [ ] Hard-coded pixel sizes instead of `font.pixelSize` via theme or `Qt.application.font`
- [ ] Manual `x`/`y` positioning where `RowLayout`/`ColumnLayout`/`anchors` belong
- [ ] `Component.onCompleted` used to initialize data that should come from the model
- [ ] `id`-based property access crossing file boundaries (tight coupling)
- [ ] Missing `Keys.onPressed` forwarding in focusable custom components
- [ ] `MouseArea` blocking hover events for inner items

### 2.7 Python/PySide6 Correctness

Check:
- [ ] `@Property` without matching setter when QML needs two-way binding
- [ ] Signal defined as class variable but emitted before `__init__` of `QObject` base runs
- [ ] `@Slot` return types not matching declared type annotation
- [ ] `QAbstractListModel` subclass missing `roleNames()` override
- [ ] `data()` returning Python types QML can't consume (e.g., raw `datetime` objects)
- [ ] `beginInsertRows`/`endInsertRows` not wrapping row mutations


## Step 3 — Summary Table

After the findings, emit a compact summary:

```
| Category                      | CRITICAL | WARNING | STYLE |
|-------------------------------|----------|---------|-------|
| Architecture                  |    0     |    2    |   1   |
| Threading & Safety            |    1     |    0    |   0   |
| Memory & Lifetime             |    0     |    1    |   0   |
| Property Bindings & Signals   |    0     |    1    |   1   |
| Performance                   |    0     |    2    |   1   |
| QML Correctness               |    0     |    1    |   2   |
| Python Correctness            |    0     |    1    |   0   |
```

Then: **Overall verdict** — one sentence, honest.


## Step 4 — Top 3 Fixes

Pick the three highest-impact issues and show corrected code side-by-side with the
original. Label clearly:

```
❌ Before:
❌ After:
```

Always include complete imports in Python snippets. Always include the surrounding
context (parent Item, enclosing Component) in QML snippets so the fix is unambiguous.


## Step 5 — Refactor Suggestions (optional, if warranted)

If the code has systemic architectural problems that a fix-by-fix patch won't resolve,
describe a refactor path:
- What the target architecture looks like
- Which files/classes to split or merge
- What the migration order should be (least disruptive first)

Only include this section if there are ≥2 CRITICAL findings or the architecture is
fundamentally inverted (logic in QML, data in context properties, etc.).


## Tone & Style Rules

- Be direct. "This will deadlock" beats "this might potentially have threading concerns."
- Show the corrected code, don't just describe the fix.
- Reference Qt docs by section name so the team can self-serve:
  e.g., *Qt Documentation → QAbstractListModel → Subclassing*
- If something is genuinely fine, say so. Don't pad findings.
- If you need to assume Qt version or binding, state it once at the top of the review.