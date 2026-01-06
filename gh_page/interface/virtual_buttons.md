---
title: Virtual Buttons
parent: Interface
nav_order: 2
---

# Virtual Buttons

Each input has a natural behaviour or type of states it can be in. However, certain actions require a binary state reflecting the behaviour of a button, i.e. *pressed* and *released*. In order for axis and hat inputs to support this they require to specify the condition under which they should be considered *pressed* and *released*, effectively turning them into a virtual button. This is often needed, for example when using individual hat directions as buttons when a game doesn't support mapping individual hat directions. A common use with axis is to enable afterburners when the throttle reaches 100% thrust.

Every axis and hat action sequence has a toggle at the top that allows treating the input for that action sequence as a button. Using this allows specifying the condition under which the virtual button is considered *pressed* as well as adding button-specific actions to the action set.

## Axis

![Virtual axis button](/assets/images/virtual_axis_button.png)
{: .text-center }

Actions associated with axis inputs have a range based setup which simulates a button press when the axis enters the specified range and releases the virtual button when it leaves the range. In addition to being able to specify the range for the button you can also specify the direction from which the range has to be entered to be triggered. This allows triggering two different actions for the same range depending on the direction it is traversed.


## Hat

![Virtual hat button](/assets/images/virtual_hat_button.png)
{: .text-center }

The eight directions of POV hats can be treated as states in which the virtual button is considered pressed. It is possible to select multiple directions at once and any one of the selected directions will be considered as part of a single virtual button.
