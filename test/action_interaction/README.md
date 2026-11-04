# Action Interaction Testing

## Purpose
The goal of this test suite is to evaluate the interaction of actions with each other. Gremlin allows complicated and confusing combinations that can be subtly wrong or behave unintuitively. Manually testing these is impossible and error prone. Therefore a testing setup that allows configuring realistic action sets and verifying their execution results in the desired events being emitted is required.

## Requirements
The following is a list of desirable properties such a system should have:

- Easy to specify action sets to test, especially from user bug reports.
- Writing tests should be relatively simple.
- Reading and understand test intent should be easy.
- Handle multiple sets of long-running actions operating concurrently.
- Support of checking precise timing-related behaviour.
- Check the state of inputs.
- Assert the correct sequential emission of events.

## Usage
This test framework leverages Gremlin's logical device system. This means all tests use logical device inputs to send inputs and then publish to another set of logical inputs. For simplicity a `template.xml` profile exists within the `profiles` folder. That profile has four input and output instances defined for each of axis, buttons, and hat. The input entries should be used to specify the action sets to test while the output entries should be used to verify correct behaviour inside the test.

Tests address inputs by their label, so a copy of `template.xml` needs a descriptive label on every input and output the test uses. Labels are defined in the `logical-device` section of the profile and must be unique across all input types. This allows a test to be read without opening its profile:

```python
jgbot.press_button("Map to out_button")
assert jgbot.button("out_button")
assert EventSpec("out_button", True) == jgbot.next_event()
```

The test framework leverages `pytest-qt` to make it possible to interact with Qt's signal & slot system without blocking the main thread. This functionality is accessible via the `jgbot` fixture (similar to pytest-qt's `qtbot` fixture) which exposes useful functions to interact with Gremlin.

The documentation of the `JoystickGremlinBot` provides an overview of the available functionality. Additionally, the existing tests show some of the ways in which the provided functions can be leveraged.

## Naming Inputs
A label states what an input does and where the result goes. The same kind of action reads the same way in every profile.

| Kind | Form | Example |
| --- | --- | --- |
| Output | `out_` and a short name | `out_button`, `out_short`, `out_axis_1` |
| Output specific to a mode | `out_<something>_mode_<x>` | `out_inverted_mode_a` |
| Direct mapping | `Map to <output>` | `Map inverted to out_button` |
| Keyboard mapping | `Map to <keys>`, `+` for keys held together | `Map to RShift + M` |
| Action driving several outputs | action and setting, a colon, the outputs | `Delta 0.3: out_positive, out_negative` |
| Action with named branches | action, ` - `, each branch and its target | `Hat Buttons - N,S: out_north_south, E: out_east` |
| Nested action with several entries | `[ ]` around the group | `Default: [Tempo 0.2 on release - short: out_short, long: out_long], Second: Map to out_second` |
| Chain | numbered steps | `Chain 1: Press O 2: Release O` |
| Macro | `Macro <repeat type> [outputs]`, `set` when outputs stay on | `Macro hold [out_axis_2]` |
| Mode change | change type, `to <mode>` for a fixed target | `Temporary to Parent`, `Unwind`, `Cycle [Child 1, Child 2]` |
| Input that varies by mode | each mode spelled out | `A: Map to out_button_mode_a, B: Map to out_button_mode_b` |
| Input only used by a condition | its role | `condition_button` |

A label that exceeds the line length is split across string literals rather than shortened. Only a label that is too long to read inline and used often gets a module-level variable; everything else stays a literal string so the test shows what the input does.