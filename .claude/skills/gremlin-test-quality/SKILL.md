---
name: gremlin-test-quality
description: Assess and improve how well Joystick Gremlin tests are written (Python, PySide6/QML, pytest, pytest-qt) - clarity, assertion quality, determinism and timing, fixture use, parametrization, speed, and incidental coupling such as positional arguments or values copied from profiles. Use when asked to polish, tidy, harden, de-flake or improve existing tests, when asked whether tests are well written, and when gremlin-test-review hands over kept tests or an agent has just written a test that passed the gate. Does not decide whether a test should exist; that is gremlin-test-review.
---

# Gremlin test quality

This skill judges how a test is written, never whether it should exist. Every
test it is pointed at is treated as worth keeping: deciding existence and level
is `gremlin-test-review`'s job, and the user calls that skill when they want it.
Do not report duplicates, suggest deletions, or question the test's level.

A badly written test that is worth keeping still costs time: it breaks on
harmless changes, fails without saying why, flakes on timing, or hides what it
checks. The aim is to remove those costs without changing what the test
protects.

The same over-generation risk that applies to tests applies to suggestions: a
reviewer can always find something. **Report a finding only if it has a
concrete maintenance or diagnosis cost that can be stated in one line.** There
is no nit or style tier. A test with no such finding is counted as fine and not
commented on.

Leave anything ruff or pyright enforces (import order, annotations, line
length, SPDX header, unused imports) to those tools. Do not report it; a single
closing line may point to `poetry run ruff check` if such issues are visible.

## Modes and invocation

| Invocation | Who | Behavior |
|---|---|---|
| `/gremlin-test-quality <target>` | user | assess, report, wait for decisions |
| `/gremlin-test-quality --auto <target>` | gremlin-test-review or another agent | assess, apply every finding that does not change meaning, report |

`<target>` is a file, directory, test id, or a diff/branch. If no target is
given, ask what to assess. Do not guess a scope.

## Output style

Plain and professional. No emoji, no decorative symbols, no headings beyond
what the report format below uses, no praise or filler. One line per reason.

## Test levels (project taxonomy)

Needed to judge which harness and fixtures a test should use. The level itself
is not questioned here.

| Level | Location | Harness |
|---|---|---|
| 1. Unit | `test/unit/` | public API of one module/class; `xml_dir` for profile XML; `qtbot` for Qt models/signals |
| 2. Simulated system | `test/action_interaction/` (and legacy `test/integration/action_plugins/`) | `jgbot`, `profile_dir`, profiles based on `template.xml`, ids from `input_definitions` |
| 3. E2E | `test/integration/` | vJoy loopback; `tester`, `vjoy_control_device`, `vjoy_di_device`; one profile per module from `test/integration/xml/` |
| 4. Automated ui test | not yet established | conventions not defined; judge on the general criteria only and say so |

## Quality dimensions

Use these names in the `dimension` column. Sources are listed at the end.

1. **intent clarity** - The name states the behavior and the expected outcome.
   Arrange, act, and assert are visible. The test can be understood without
   opening helpers: essential inputs are in the test body, only irrelevant
   setup is factored out (DAMP over DRY) [SWE-Google-12].
2. **assertion quality** - Asserts observable behavior (emitted events, output
   state, returned values, saved XML, model data) through public APIs, not
   private attributes or harness internals [SWE-Google-12, ToTT-Behavior,
   Khorikov]. One behavior per test [SWE-Google-12]. The assertion actually
   checks what the name claims (watch for `==` on objects whose equality
   ignores the field of interest, and for inputs that cannot tell fields apart,
   such as giving `value` and `raw_value` the same number so a mixed-up copy
   still passes). A test that counts or collects events checks each of them
   and, at level 2, ends with the no-further-event check; adding those
   assertions changes meaning. Failure output shows expected and actual
   [SWE-Google-12]. No loops or conditionals computing expected values
   [SWE-Google-12].
3. **determinism and timing** - No fixed sleeps where a signal, event, or
   condition can be awaited (`qtbot.waitSignal`, `qtbot.waitUntil`,
   `jgbot.next_event`, which already waits) [pytest-qt]. Where a fixed
   duration is the point (holding past a window), use `jgbot.wait` /
   `qtbot.wait`, which process Qt events while waiting; `time.sleep` does
   not [pytest-qt: reference, `QtBot.wait`]. Timing margins are stated relative to
   the configured window. `@pytest.mark.flaky` is a symptom; find and fix the
   cause. No state leaked through session-wide singletons (`EventListener`,
   `Backend`, `ModeManager`, `Configuration`) [Beck: deterministic, isolated].
4. **fixture use** - Uses the existing fixtures and helpers (`jgbot`,
   `profile_dir`, `xml_dir`, `ldev`, `tester`, `get_fake_device_guid`, ...)
   instead of reimplementing them or hardcoding paths. Public harness methods
   over private ones (`jgbot.event_count()` over `jgbot._event_logger`).
5. **parametrization** - Each case covers a distinct branch or boundary; cases
   that take the same path are padding. Ids say what the case is
   (`ids=["north", ...]` or `pytest.param(..., id=...)`), not `0`, `1`, `2`.
6. **speed** - No avoidable profile loads, waits longer than the behavior
   requires, or heavy setup for a light check [Khorikov: fast feedback; Beck:
   fast].
7. **incidental coupling** - The test hardcodes something that will change for
   reasons unrelated to the behavior under test:
   - positional arguments to constructors or functions with several
     parameters (adding or reordering a parameter breaks or silently shifts
     values); use keyword arguments, or a helper that supplies irrelevant
     defaults
   - values copied from configuration or profiles with no stated link
     (e.g. waiting `0.2` s against the `0.1` s threshold in `double_tap.xml`)
   - raw ids or paths where named constants or fixtures exist
     (`inout.IN_BUTTON_1`, `profile_dir`)
   - full object or tuple literals compared when only one field is the point
     of the test

   Not a defect: literal expected values for the behavior under test. Those
   stay literal; computing them reintroduces implementation logic into the
   test [SWE-Google-12]. Choose the fix per case (keyword argument, named
   constant next to the profile, fixture, or a comment tying the value to its
   source); do not add derivation logic to the test.

## Assessment

1. Read the target tests, the code under test, and the conftest fixtures the
   tests use or should use. For profile-driven tests, read the profile.
2. For each test, check the seven dimensions. Keep a finding only if its cost
   fits in one line.
3. For each finding, decide whether the fix **changes meaning**: it alters
   what the test asserts or how many tests there are (splitting a test,
   changing expected values, adding or removing assertions on new behavior).
   Renames, keyword arguments, fixtures, replacing sleeps with waits, adding
   failure messages, and readable ids do not change meaning.

## Report

```
<target>: N tests - fine F, findings in K

| # | test id | dimension | issue | fix | changes meaning |
|---|---------|-----------|-------|-----|-----------------|
| 1 | test_x.py::test_a | incidental coupling | waits 0.2 s with no link to the 0.1 s threshold in double_tap.xml | named constant beside the profile reference, or comment tying it to the threshold | no |
| 2 | test_x.py::test_b | assertion quality | checks single and double tap in one test | split into two tests | yes |
```

One row per finding; a test may have several rows. Fine tests appear only in
the count.

**User mode:** stop after the report. The user replies with decisions
("apply all", "apply 1, 3"); apply only those.

**Auto mode:** apply every `no` row, then output the report with an `applied`
column, followed by the `yes` rows listed as awaiting confirmation. Never apply
a `yes` row in auto mode.

## Applying changes

1. Run the affected tests before editing: `poetry run pytest <test ids>`.
   Record pass/fail per test.
2. Apply the changes. Follow `AGENTS.md` conventions (SPDX header,
   `from __future__ import annotations`, annotations, absolute imports, no
   function-local imports).
3. Run the same tests again. If a test that passed before now fails, revert
   that test's changes and report it as not applied, with the failure output.
4. Report the before/after result in one line per file.

## Project principles

Short, general principles for this project. They take precedence over the
dimensions above when they conflict; say so in the issue column when one
decides a finding. One line plus a short rationale each.

- `jgbot.next_event()` is the wait in level 2 tests; an extra sleep before it
  is always a finding. - It already blocks until an event or a timeout.
- Timing values in a test are tied to the profile value they depend on, by
  name or comment. - Profile thresholds change; unlinked waits silently stop
  testing the window.
- `jgbot.load_profile` is called at most once per test. - It starts the code
  runner without stopping the previous one, so a second call leaves the first
  profile's callbacks and signal connections active.

### Adding principles

In user mode, when the user overrules a finding, consider whether the override
generalizes into a principle (not a case-specific exemption). If it does, offer
once to add it here, showing the exact wording and rationale before writing.
Never add principles in auto mode.

## Sources

- [Khorikov] Vladimir Khorikov, *Unit Testing: Principles, Practices, and
  Patterns*, Manning, 2020. https://manning.com/books/unit-testing
- [Beck] Kent Beck, *Test Desiderata*.
  https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b3
- [SWE-Google-12] *Software Engineering at Google*, ch. 12 "Unit Testing".
  https://abseil.io/resources/swe-book/html/ch12.html
- [ToTT-Behavior] Google Testing Blog, "Testing on the Toilet: Test Behavior,
  Not Implementation", 2013-08-05.
  https://testing.googleblog.com/2013/08/testing-on-toilet-test-behavior-not.html
- [pytest-qt] pytest-qt documentation: signals
  https://pytest-qt.readthedocs.io/en/latest/signals.html, waitUntil
  https://pytest-qt.readthedocs.io/en/latest/wait_until.html, reference
  https://pytest-qt.readthedocs.io/en/latest/reference.html
- [Project] `AGENTS.md`, `test/integration/README.md`,
  `test/action_interaction/README.md`.
