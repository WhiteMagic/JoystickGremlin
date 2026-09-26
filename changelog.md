# Release 16

## Important

- The new dill library may cause issues, please report them. You can always switch
  to the legacy library through the options menu.
- The new UI has changed certain underlygin aspects and as such could lead to
  crashes when operating the UI, report these crashes too please.

## New Features

- New UI style designed for Gremlin.
  - Supports color themes, currently dark, light, and zenburn.
- New dill input library version.
  - Option to switch to the legacy version in case of problems.
  - Detects XInput devices and reads them through XInput rather than DirectInput.
  - Reduced latency, 1ms for polled deviced, and <0.5ms for well behaved DirectInput devices.
- UI to show log file contents of current session.
- Minimize to system tray option.
- Position and size of main window and input viewer are remembered.
- Map to vJoy actions pick first unused input when added.
- Two new merge axis modes added.


## Bug Fixes

- Most recent profiles now show in the menu.
- Profile activation now supports heuristic and last active modes.
- Reworked mouse motion logic to be more consistent and handle multiple simultaneous sources.
- Numerical issue in Bezier curves fixed.
- Hat as Button action change logic improvements.
- vJoy Axis condition using incorrect comparator.
- Script KeyboardVariable issues linked to numpad keys fixed.
- Logical devices are sorted with "natural" labels.