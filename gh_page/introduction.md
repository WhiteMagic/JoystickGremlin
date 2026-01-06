---
title: Introduction
nav_order: 3
---

# Introduction

Joystick Gremlin is a program that allows the configuration of joystick like devices, similar to what CH Control Manager and Thrustmaster's T.A.R.G.E.T. do for their respectively supported joysticks. However, Joystick Gremlin works with any device be it from different manufacturers or custom devices that appear as a DirectInput device to Windows. Joystick Gremlin uses the virtual joysticks provided by vJoy to map physical to virtual inputs and apply various other transformations such as response curves to analogue axes. In addition to managing joysticks, Joystick Gremlin also provides keyboard macros, a flexible mode system, scripting using Python, and many other features.

The main features are:

- Works with arbitrary joystick like devices.
- User interface for common configuration tasks.
- Merging of multiple physical devices into a single virtual device.
- Axis response curve and dead zone configuration.
- Arbitrary number of modes with inheritance and customisable mode switching.
- Macros with joystick, keyboard, and mouse inputs.
- Internal logical device for advanced actions.
- Python scripting support.

Joystick Gremlin provides a graphical user interface, described in [Interface](/interface), which allows commonly performed tasks, such as input remapping, axis response curve setups, and macro recording to be performed easily. Functionality that is not accessible via the UI can be implemented with [User Scripts](/interface/user_scripts).
