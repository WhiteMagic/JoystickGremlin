---
title: Changelog
nav_order: 9
---

# Release 14

This release is a complete rewrite of the user interface and how the profile architecture. Along the way a lot of other things have changed, some of which are summarised below.

- User interface entirely redone in QML using PySide6
  - Drag & drop for action reordering
  - Collapsing actions
  - Dark mode support
  - Turning axis or hat into a button accessible at the top of an action sequence
- Profile architecture completely redone with actions and inputs no longer being tied together
  - Assigning existing actions to different inputs
  - Copying contents of an action to new inputs
  - Only actions which can be nested to an arbitrary depth
  - Actions can exist on multiple inputs, enabling, multi-input actions
- Conditions are actions too now
- User configurable folder for third-party action plugins
- An internal logical device was added that can be used as an internal storage
- Mode switching supports more complicated flows
- Improved various tools such as calibration and 1:1 mapping
- Improved actions
  - Piecewise linear response curve added
  - More control over the activation of "Map to X" actions

A side effect of these changes, especially the profile architecture, is that previous profiles are not compatible. For now there is no conversion tool and there may never be one as writing a robust one likely will take significant amount of time to write and especially test. There are also some aspects that are still missing. Depending on their utility they will over time be added back in.
