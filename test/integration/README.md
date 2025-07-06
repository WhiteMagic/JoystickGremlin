# End-to-End Integration Tests

## Objective

To test large portions of the Joystick Gremlin software stack using a vJoy device as a loopback.

## How it works

The integration test is a standard pytest suite. The rough ordering of steps is:

1.  Once per session, a Joystick Gremlin app is created (`pytest-qt` is not used, since we are not
    testing the GUIs)
2.  Once per session, vJoy devices are detected.
    1.  If no vJoy devices are found, the integration tests are skipped.
3.  Once per test module, vJoy devices are assigned input and output roles for testing purposes.
    1.  If none of the vJoy devices have enough axes/buttons/hats, the integration tests are skipped.
4.  Once per test module, a profile is loaded, existing inputs and outputs are swapped with the
    detected vJoy devices, and written to a temporary location.
    1.  This approach is adopted to make it easy to generate a profile from the Gremlin UI using
        a real DirectInput device.
    2.  In most test modules, it should be sufficient to partition some axes, buttons and hats as
        test inputs, and the rest as outputs (multiple vJoy devices not needed).
5.  The modified profile is loaded into Joystick Gremlin, which is then activated.
6.  Inputs are written to some axes, buttons and hats, and outputs are verified per the action
    expectations.

## Code Layout

[`conftest.py`](./conftest.py) has the common fixtures; for simplicity all integration tests
should strive to use these and not override them.

Each module in this directory should consist of tests against a single profile. It is recommended
that each profile contain tightly scoped functionality to make it easier to track down failures.

Each module should define a fixture `profile_name`, that returns the name of the profile in the
[`xml`](./xml/) directory. It is recommended to use a class to organize tests. Each test would
typically use three fixtures:

1.   `tester` to run assertions.
2.   `vjoy_control_device` as the vJoy device that will have control inputs written to.
3.   `vjoy_di_device` as the vJoy device that will have mapped outputs read and verified.
     1.   In most tests, these can be the same device, but they are instances of different
          classes.

It is generally recommended to parameterize the tests and verify multiple input-output pairs.
See [`test_e2e_profile_simple.py`](./test_e2e_profile_simple.py) for a minimal example.

## Creating profiles for integration tests

Typically the steps would be:

1.  Open Joystick Gremlin, start a new profile.
2.  Map axes, buttons, and hats from a real DirectInput device to a vJoy device. Take care to
    always maps these to different indices e.g.
    1.   Map DirectInput device axes 1-4 to vJoy axes 5-7.
    2.   Map DirectInput buttons 1-16 to vJoy buttons 17-32.
    3.   Map DirectInput POVs 1-2 to vJoy POVs 3-4.
3.  Save the profile to the [`xml`](./xml/) directory.

## Running

It is recommended to run the integration tests using `-v`, e.g.:

```
JoystickGremlin> pytest -v test/integration
```

# Action Plugin Integration Tests

The action plugin integration tests are located in the `action_plugins` subdirectory.

# Objective

To test the interplay of action plugins using `IntermediateOutput` to feed inputs and check
outputs.

## Ability to run quickly, and on GitHub actions.

By using only `IntermediateOutput` device for inputs and outputs, the tests can be run quickly,
and on GitHub actions where we do not install vJoy. `DirectInput` is also bypassed.

# How it works

The action plugin integration tests are similar to the end-to-end tests, but with a few key
differences:

1.  The profile is directly modified via Python APIs, and activated.
2.  The inputs are written to the `IntermediateOutput` device, and the outputs are verified,
    also from the `IntermediateOutput` device.

# Code Layout

Similar to the end-to-end tests (and many fixtures are re-used via pytest fixture inheritance),
but with the following differences/overrides for the fixtures:

1.  `_activate_gremlin` is overridden to not load a profile but directly activate the current one.
2.  (Only) `assert_io_*` methods are used to verify `IntermediateOutput` device outputs.
