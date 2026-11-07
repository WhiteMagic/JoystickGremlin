---
name: gremlin-test-review
description: Critically review or gate tests for the Joystick Gremlin project (Python, PySide6/QML, pytest, pytest-qt): decides whether each test should exist and at which level. Use whenever tests in this repo are being reviewed, cleaned up, or judged for value, and whenever an agent is about to write a new test — run the gate first to decide whether the test should exist at all and at which level (unit, action_interaction, integration e2e, automated ui test). Also use when someone asks "are these tests any good", "which tests can we delete", "where should this test go", or after tests were generated in bulk. How well a kept test is written is gremlin-test-quality's job.
---

# Gremlin test review

Tests are code with an ongoing maintenance cost. A test earns its place only if
the regressions it catches are worth the cost of reading, running, and updating
it every time the code changes. LLM agents can produce tests faster than anyone
can maintain them, and they fail toward volume: tests that restate the
implementation, test Python or Qt itself, or repeat each other with cosmetic
differences. This skill exists to counter that.

This skill decides existence and level only. How well a kept test is written
(clarity, assertions, timing, fixtures, coupling) is judged by
`gremlin-test-quality`; do not report writing-quality issues here.

**Stance: every test must justify its existence.** The default answer to "should
this test exist" is no, until the test shows what it protects.

The sourced criteria, the catalogue of low-value test patterns, and the
PySide6/pytest-qt mechanics are in the "Review criteria" part at the end of
this file. Use them for every verdict.

## Modes and invocation

Decide the mode from the invocation:

| Invocation | Mode | Who | Changes applied |
|---|---|---|---|
| `/gremlin-test-review <target>` | review | user | none until the user decides |
| `/gremlin-test-review --auto <target>` | review | agent | moves applied; deletions only listed; kept and moved tests handed to `gremlin-test-quality --auto` |
| `/gremlin-test-review gate ...` | gate | agent | none, verdict only |

`<target>` is a file, directory, test id, or a diff/branch. If no target is
given in review mode, ask what to review. Do not guess a scope.

`--auto` and gate run in a fresh subagent, so the agent that wrote or changed the
tests does not judge them. That agent spawns a `general-purpose` subagent (no
fork, no worktree, which would lack uncommitted tests) and relays its result. The
prompt is only the invocation: `/gremlin-test-review --auto <target>`, or
`/gremlin-test-review gate` with the behavior, the level, and the draft test. A
subagent given such a prompt runs the skill itself.

## Test levels (project taxonomy)

The project's levels are authoritative (`AGENTS.md`, `test/*/README.md`).
Users and agents use generic terms loosely ("integration test" often means
`action_interaction`). Map their wording to a level, state the mapping you
chose in one line, and move on — do not lecture about terminology.

| Level | Location | What it exercises | Runs in CI |
|---|---|---|---|
| 1. Unit | `test/unit/` | One module/class through its public API. No activated profile, no input pipeline. Qt models/signals via `qtbot` are fine. | yes |
| 2. Simulated system | `test/action_interaction/` | Real profile XML + real action execution; inputs and outputs via `LogicalDevice` using the `jgbot` fixture. Timing, chaining, modes, action interplay. | yes |
| 3. E2E | `test/integration/` | Full stack with vJoy loopback (DirectInput read-back). Skipped without vJoy. | no (local only) |
| 4. Automated ui test | not yet established | Drives the real QML UI. | — |

- **Pick the cheapest level that can observe the behavior.** A test belongs at
  level 3 only if what it checks depends on vJoy/DirectInput; anything that
  `LogicalDevice` can observe belongs at level 2, where it runs in CI.
- **Automated ui test** is justified only when the behavior is observable
  exclusively through the UI (QML bindings, navigation, user-visible state).
  Tool-specific conventions are not defined yet; when reviewing such tests,
  judge them on the general criteria and say that level-specific conventions
  are unavailable rather than inventing them.
- `test/integration/action_plugins/` is a legacy leftover holding level-2
  tests. Never recommend it as a destination for new tests. Review existing
  tests there on their merits as level 2; mention relocation only as a
  low-priority note.

## The admission bar

A test is worth having when all four hold:

1. **Not already covered.** Search the existing tests for the same behavior
   (grep for the function, action, profile, or input involved) before judging.
   Duplicate coverage is the most common reason a test should not exist.
2. **Could plausibly regress.** There is real logic that a reasonable future
   change could break: branching, arithmetic, parsing, state machines, timing,
   mode inheritance, XML round-trips. Trivial accessors, enum values, framework
   behavior, and constants do not qualify.
3. **Would catch a real break.** Name a realistic code change that breaks this
   behavior for users, including changes outside the function under test (e.g.
   renaming a registered option), and confirm from the test that it would fail.
   A branch being executed is not enough. If realistic breaks leave the test
   green, it does not qualify.
4. **At the cheapest level that can observe it** (see above).

Explicitly favored, so skepticism does not strip meaningful coverage:
- Regression tests tied to a real bug (issue, report, or a profile from a user).
- Boundary behavior: value ranges, deadzones, curve endpoints, mode inheritance
  edges, timing windows (tempo, double tap, auto release).
- Tests that pin user-visible profile compatibility (loading existing XML).

## Gate mode

Input from the calling agent: one behavior to test (one sentence), the intended
level, and the draft test. Each behavior gets its own gate call. If a call has
several behaviors or no draft, return `do-not-write` with that as the reason.
Run the gate again when the design of the code or of the test changes.

1. Search existing tests for coverage of the behavior; read the matches.
2. Read the code that implements the behavior enough to judge whether it can
   plausibly regress.
3. Apply the admission bar to the draft.
4. Return exactly this block and nothing else:

```
verdict: write | write-at-different-level | do-not-write
level: unit | action_interaction | integration | automated-ui
reason: <1-3 sentences, naming the criterion that decided it>
existing_coverage: <test ids/paths, or "none">
requirements: <only for write*: what the test must assert to be worthwhile,
               which fixtures/profiles to use, what to avoid>
```

`requirements` should steer the agent away from the low-value patterns in
the review criteria below (e.g. "assert emitted events via jgbot.next_event,
not internal action state; one behavior per test").
For `write` and `write-at-different-level`, end `requirements` with: "after
writing, run `/gremlin-test-quality --auto <test id>`".

## Review mode

1. Read the target tests, the code under test, and the relevant conftest
   fixtures. For each test, search for overlapping tests elsewhere.
2. Give every test one verdict:
   - `keep` — meets the admission bar. Writing quality does not affect this
     verdict: a badly written test that protects something worthwhile is
     `keep`.
   - `move-level` — worthwhile but at the wrong level (name the target).
   - `delete` — fails the admission bar: duplicate, tautological, tests
     Python/Qt/mocks rather than Gremlin, no plausible regression, or stays
     green on a realistic break (name the break in the reason).
3. Report in this format:

```
<target>: N tests — keep K, move-level M, delete D

| # | test id | verdict | reason | criterion |
|---|---------|---------|--------|-----------|
| 1 | test_x.py::test_a | delete | asserts the mock returns what it was configured to return | tautology |
...

Duplicates:
- test_x.py::test_b, test_y.py::test_c — same behavior; keep test_y.py::test_c (covers the boundary too)
```

   List only non-`keep` tests in the table; `keep` appears only as a count.
   Reasons are one line. Name the criterion from the review criteria below.

4. **User mode:** stop after the report. The user replies with decisions
   (e.g. "apply all", "apply 1-4, keep 5"); apply only those.
   End the report with one line naming the kept tests, e.g. "Kept: 7 tests.
   `/gremlin-test-quality test_x.py` to assess quality." Do not run it.
   **Auto mode:** apply `move-level` changes, then run
   `/gremlin-test-quality --auto` on all `keep` and moved tests, then list the
   `delete` candidates for the user to confirm. Never delete in auto mode.
5. When applying changes: move each test unchanged except for what the new
   level requires; follow `AGENTS.md` conventions (SPDX header, `from __future__ import
   annotations`, annotations required by ruff ANN, absolute imports, no
   function-local imports, fixtures from the conftest files). Run the affected
   tests with `poetry run pytest <paths>` and report the result.

## Project principles

Short, general principles for this project. They take precedence over the
general criteria when they conflict; say so in the reason when one decides a
verdict. Keep each to one line plus a short rationale.

- Prefer level 2 (`jgbot`) over level 3 for action behavior. — Level 2 runs in
  CI and needs no vJoy.
- Tests exist to fail when a code change breaks something, so they run real code
  on real data; mocks and hand-written data are a last resort and stay as close
  to the real thing as possible. — Anything faked stops following the code, so
  the test stays green when the real thing breaks.

### Adding principles

In user mode, when the user overrules a verdict, consider whether the override
generalizes into a principle (not a case-specific exemption). If it does, offer
once to add it here, showing the exact one-line wording and rationale before
writing. Never add principles in auto or gate mode.

---

# Review criteria

Contents
1. Sources
2. What a test is worth (value criteria)
3. Low-value test catalogue (with criterion names)
4. Level-specific guidance for Joystick Gremlin
5. pytest / pytest-qt / PySide6 mechanics

Every criterion below names its source. When a verdict rests on a criterion,
cite its name (e.g. "tautology", "implementation-coupled") in the report.

## 1. Sources

- **[Khorikov]** Vladimir Khorikov, *Unit Testing: Principles, Practices, and
  Patterns*, Manning, 2020. https://manning.com/books/unit-testing
  Free chapter 1 excerpt: https://enterprisecraftsmanship.com/files/Unit-Testing-Chapter-1-Excerpt.pdf
  Key points used here: code (including test code) is a liability, not an
  asset; every test has a value and a maintenance cost, and tests whose cost
  exceeds their value should be removed. Four attributes of a good test:
  protection against regressions, resistance to refactoring, fast feedback,
  maintainability.
- **[Beck]** Kent Beck, *Test Desiderata*.
  https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b3
  Properties: isolated, composable, fast, inspiring, writable, readable,
  behavioral, structure-insensitive, automated, specific, deterministic,
  predictive. Properties trade off against each other; judge which ones a
  given test needs most.
- **[SWE-Google-12]** *Software Engineering at Google*, ch. 12 "Unit Testing".
  https://abseil.io/resources/swe-book/html/ch12.html
  Test via public APIs; test behaviors, not methods; one behavior per test;
  DAMP over DRY; no logic in tests; clear failure messages; avoid brittle tests.
- **[SWE-Google-13]** *Software Engineering at Google*, ch. 13 "Test Doubles".
  https://abseil.io/resources/swe-book/html/ch13.html
  Prefer real implementations; prefer state testing over interaction testing;
  interaction testing only when state cannot be checked or call count/order is
  the behavior, and only for state-changing calls; avoid overspecification.
- **[ToTT-Behavior]** Google Testing Blog, "Testing on the Toilet: Test
  Behavior, Not Implementation", 2013-08-05.
  https://testing.googleblog.com/2013/08/testing-on-toilet-test-behavior-not.html
- **[pytest-qt]** pytest-qt documentation. https://pytest-qt.readthedocs.io/en/latest/
  Signals: https://pytest-qt.readthedocs.io/en/latest/signals.html
  waitUntil: https://pytest-qt.readthedocs.io/en/latest/wait_until.html
  Model tester: https://pytest-qt.readthedocs.io/en/latest/modeltester.html
- **[Project]** `AGENTS.md`, `test/integration/README.md`,
  `test/action_interaction/README.md` in the repository.

## 2. What a test is worth

Weigh value against cost [Khorikov]:

- **Value** = regressions it would actually catch, in code that can plausibly
  change, that no other test already catches.
- **Cost** = lines to read and maintain, runtime, how often it breaks on
  harmless refactors, how hard its failures are to diagnose, setup it drags in
  (profiles, fixtures, vJoy).

A test that breaks when internals are restructured but behavior is unchanged
has negative value over time: it costs a fix on every refactor and catches
nothing [Khorikov: resistance to refactoring; Beck: structure-insensitive;
SWE-Google-12: brittle tests].

## 3. Low-value test catalogue

These are the patterns to look for, most of them typical of bulk-generated
tests. Criterion names in **bold** are what the report cites.

| Criterion | Pattern | Basis |
|---|---|---|
| **duplicate** | Same behavior already asserted elsewhere, possibly with different names, values, or level. Includes parametrizations whose extra cases exercise no new branch or boundary. | Khorikov (value vs cost) |
| **tautology** | Asserts what the test itself set up: a mock returns its configured value, a setter followed by its getter, a constructor stores its arguments. | Khorikov (protection against regressions) |
| **tests-the-framework** | Verifies Python, Qt, PySide6, pytest, or the stdlib (e.g. that `Signal.emit` reaches a connected slot, that an `Enum` member has its declared value, that a dataclass default is the default). | Khorikov (protection against regressions) |
| **no-plausible-regression** | Code under test has no logic a reasonable change could break (trivial property, constant, pass-through). | Khorikov (value vs cost) |
| **implementation-coupled** | Asserts private attributes, internal call order, or which helper was called, instead of observable outcome (emitted events, returned value, saved XML, model data). | ToTT-Behavior, SWE-Google-12, Khorikov (resistance to refactoring) |
| **interaction-overuse** | Uses mocks to verify calls where the real object (Profile, LogicalDevice, action) could be used and its resulting state checked. | SWE-Google-13 |
| **overspecified** | Checks every argument or unrelated calls/fields; fails for reasons unrelated to the behavior named in the test. | SWE-Google-13 |
| **wrong-level** | Behavior observable at a cheaper level (e.g. e2e vJoy test for something `jgbot` can observe; full profile activation to test a pure function). | Project, Khorikov (fast feedback) |
| **no-assertion** | Runs code and asserts nothing meaningful ("does not raise" without the absence of an exception being the behavior), or asserts only `is not None`. | Beck (predictive, inspiring) |

**implementation-coupled**, **interaction-overuse**, and **overspecified** are
grounds for `delete` only when nothing observable is protected once the
coupling is removed. If the test also protects real behavior, it is `keep`;
the coupling is a quality issue for `gremlin-test-quality`.

Not low-value, even though they may look small:
- A regression test for a real reported bug.
- A boundary or edge case of real logic (range limits, deadzone edges, timing
  windows, mode inheritance).
- A round-trip that protects loading existing user profiles.

## 4. Level-specific guidance (Joystick Gremlin)

From [Project] unless noted.

**Level 1 — `test/unit/`**
- Exercise a module through its public API. Profile parsing tests load XML from
  `test/unit/xml/` via the `xml_dir` fixture.
- Qt item models: assert on model data/role output; consider pytest-qt's
  `qtmodeltester` for model contract checks rather than hand-written checks of
  `rowCount`/`index` mechanics [pytest-qt: Model tester].
- Session-wide singletons (`EventListener`, `Backend`, `ModeManager`,
  `Configuration`) are set up once per session (see `test/conftest.py`); a unit
  test that mutates them without restoring state is **nondeterministic**.

**Level 2 — `test/action_interaction/`**
- Configure behavior in a profile under `profiles/` (based on `template.xml`)
  with descriptive input labels (naming rules in the folder's `README.md`), load
  it with `jgbot.load_profile`, drive inputs by label with `jgbot.press_button`,
  `tap_button`, `hold_button`, `set_axis_absolute`, `set_hat_direction`, etc.
- Assert on emitted events with `jgbot.next_event()` compared to
  `EventSpec(label, value)`, and on output state via
  `jgbot.axis/button/hat`. Asserting internal action
  state instead is **implementation-coupled**.
- Assert absence of extra events with
  `pytest.raises(jgbot.qtbot.TimeoutError): jgbot.next_event()` — that is the
  established pattern.
- Timing tests depend on `jgbot.wait(...)` and hold durations; keep margins
  relative to the configured time windows and say why a duration was chosen.
  A test needing `@pytest.mark.flaky(reruns=...)` is a quality issue for
  `gremlin-test-quality`, not a reason to delete.
- This is the right level for user bug reports involving action combinations
  (the README names easy reproduction from bug reports as a goal).

**Level 3 — `test/integration/`**
- vJoy loopback, skipped without vJoy, not run in CI. Each module tests one
  profile from `test/integration/xml/`, using the shared `tester`,
  `vjoy_control_device`, `vjoy_di_device` fixtures, parametrized over
  input/output pairs.
- Justified only for behavior that depends on the vJoy/DirectInput path itself.
  Action logic belongs at level 2.
- `test/integration/action_plugins/` is legacy level 2; never a destination.

**Level 4 — automated ui test**
- Conventions not yet established. Admission: behavior observable only through
  the QML UI. Do not invent tool conventions.

## 5. pytest / pytest-qt / PySide6 mechanics

- Run tests via poetry: `poetry run pytest <path>` [Project].
- Waiting on asynchronous Qt behavior: use `qtbot.waitSignal` /
  `qtbot.waitSignals` for signals and `qtbot.waitUntil` for conditions;
  asserting immediately after an action that completes asynchronously is
  flaky [pytest-qt: signals, waitUntil].
- Asserting a signal is *not* emitted: pytest-qt provides
  `qtbot.assertNotEmitted` [pytest-qt: signals].
- Never call Qt GUI APIs from non-main threads [Project].
- `pytest.raises()` for exception tests [Project].
- Parametrization is valuable only when cases cover distinct branches or
  boundaries; otherwise it is **duplicate** coverage at scale.
