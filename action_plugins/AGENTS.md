# Overview

- **Purpose:** Actions implement behavior that the user can assign to inputs, processing and modifying the input in arbitrary ways.
- **Contents:** Each action consists of three components:
  - **Data class:** Holds the data relevant to the action, manages this data and handles serialization.
  - **Model class:** Exposes the data to the QML UI by implementing properties and signals to modify *Data class* contents.
  - **Functor:** Responsible to execute the logic of the action based on the configuration stored in the *Data class*.
- **Discovery:** The `gremlin.plugin_manager.PluginManager` class finds plugins in specified folders and attempts loading them. On success they are registered inside the class and exposed to QML.
- **Options:** Actions can register global options such as default values via the `gremlin.config.Configuration` class

# Data Class

- Represents Gremlin's source of truth with regards to action configurations.
- Lives between the UI (allowing user interaction), the functor (allowing to react correctly to inputs), and the profile (where it gets saved to and loaded from XML files).
- Decides when an action is valid or if it is incorrectly configured.
- Is the entry point to any action being created, linking functor and UI model classes to itself.

- Fields to define:
  - `version`: Version of this action for possibly future versioning, currently always 1.
  - `name`: Name of the action used in the UI.
  - `tag`: XML string used when serializing the action, should have the form `name-of-action`, all lower case replacing spaces with dashes.
  - `icon`: Unicode of the bootstrap icon to use for the action.
  - `functor`: Class type of the functor class.
  - `model`: Class type of the UI model class.
  - `properties`: Set of `gremlin.types.ActionProperty` values that define the properties of the action.
  - `input_types`: Set of `gremlin.types.InputType` values defining which input types this action is valid for.
  - `child_behavior_type`: Optional, behavior given to child actions when it differs from the action's own, such as the "Hat to Buttons" action.
- Methods to implement:
  - `_from_xml`: Parses an XML node, populating the member variables.
  - `_to_xml`: Serializes the instance's member variables into an XML node.
  - `user_feedback`: Returns a list of issues to display to the user, indicating a misconfigured action.
  - `_valid_selectors`: The list of selector names of containers containing child actions.
  - `_get_container`: Returns the container for the given selector name.

# Model Class

- Exposes user modifiable values from the *Data class* to the QML UI.
- Supports operations a user needs to do on the action in order to configure it.
- Methods to implement:
  - `_action_behavior`: the behavior (axis, button, hat) this action has in the current input. Not needed when the data class sets `child_behavior_type`.
  - `_qml_path_impl`: the path of the QML file to dynamically load for this action.

# Functor

- Stores the *Data class* instances but no actual values from it.
- Can store state if the action requires statefulness for execution.
- The `__call__` method is called to execute the action.
  - `event` is the actual `gremlin.types.Event` instance that triggered the execution.
  - `value` is the derived value which contains the raw initial value as well as the current value after all previous actions have been executed.
- If an action contains child action containers the functor has to make sure to call their functors using the `event` and `value` arguments.
- Methods to implement:
  - `__call__`: Executes the action.