---
title: Scripts
parent: Technical
nav_order: 2
---

# Scripts

{: .note }
Content has yet to be written.


## Migration from R13

- Replace `from gremlin.user_plugin import *` with `from gremlin.user_script import *`.
- All variables have a new positional argument, `is_optional` in 3rd position.
- `gremlin.joystick_handling.VJoyProxy` now is `vjoy.vjoy.VJoyProxy`.
- Every `PhysicalInputVariable` has a `.decorator(mode)` method that takes a `ModeVariable` as argument and can be used as a decorator on callbacks.
- `VirtualInputVariable` changed in a few ways:
  - Exposes `vjoy_id`, `input_id`, and `input_type` as properties.
  - Provides a `remap(value)` method which allows direct vJoy assignment.
- Hat type inputs no longer accept a tuple `(int, int)` as value but now require `gremlin.types.HatDirection` as value type. Converting a tuple into the correct direction is achieved via `gremlin.types.HatDirection.to_enum(tuple_value)`


## Variable Types

The following describes the different variable types available for use in a script. The implementation of these can be found in the [GitHub Source Code](https://github.com/WhiteMagic/JoystickGremlin/blob/develop/gremlin/user_script.py){:target="_blank"}.

### Bool

`BoolVariable(name, description, is_optional, initial_value)`


### Float

`FloatVariable(name, description, is_optional, initial_value, min_value, max_value)`


### Integer

`IntegerVariable(name, description, is_optional, initial_value, min_value, max_value)`


### Keyboard

`KeyboardVariable(name, description, is_optional)`


### Logical Device

`LogicalVariable(name, description, is_optional, valid_types)`


### Mode

`ModeVariable(name, description, is_optional)`


### Selection

`SelectionVariable(name, description, is_optional, option_list, default_index)`


### String

`StringVariable(name, description, is_optional, initial_value)`


### Physical Input

`PhysicalInputVariable(name, description, is_optional, valid_types)`


### Virtual Input

`VirtualInputVariable(name, description, is_optional, valid_types)`
