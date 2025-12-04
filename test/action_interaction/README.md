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

The test framework leverages `pytest-qt` to make it possible to interact with Qt's signal & slot system without blocking the main thread. This functionality is accessible via the `jgbot` fixture (similar to pytest-qt's `qtbot` fixture) which exposes useful functions to interact with Gremlin.

The documentation of the `JoystickGremlinBot` provides an overview of the available functionality. Additionally, the existing tests show some of the ways in which the provided functions can be leveraged.