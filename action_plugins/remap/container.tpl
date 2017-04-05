% if input_type == InputType.JoystickAxis:
    gremlin.action_containers.ActionFactory.map_axis(${entry.vjoy_device_id}, ${entry.vjoy_input_id})
% elif input_type in [InputType.JoystickButton, InputType.Keyboard]:
    gremlin.action_containers.ActionFactory.map_button(${entry.vjoy_device_id}, ${entry.vjoy_input_id})
% elif input_type == InputType.JoystickHat:
    gremlin.action_containers.ActionFactory.map_hat(${entry.vjoy_device_id}, ${entry.vjoy_input_id})
% endif