# Release 16.1

## Important

Conditions and mode changes now should behave more "natural". This effectively means that button presses and releases are coupled in a manner of speaking. An action triggered by a button press should always expect to receive that button's release irrespective of the mode the release happens in or the  state of the action. There are a number of edge casses in this so this may not fully work as one would expect yet.

## New Features

- Automatic profile switching now has the notion of a "Default" profile which will be activated whenever no application driven profile is active.

## Bug Fixes

- Rework how condition actions handle condition state changes.
- Keyboard key F13 to F24 properly display their label.
- Fix vJoy related crashes.
- Ensure state shown in the UI matches that of the loaded profile.
- Always update action chips.
- Fix file encoding related issues.
- Macro button entries always default to "press" now.
- Improve audio playback handling.
- Keep button and hat activations visible for a minimum amount of time.
- Plethora of fixes to UI code to work around and reduce memory management issues.
- Behavior of actions around mode switches made consistent and behave more "natural".
