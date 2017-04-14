<%namespace name="util" module="templates.functions"/>
<%!
from gremlin.common import DeviceType, InputType
import gremlin
%>\
import importlib
import gremlin
from vjoy.vjoy import AxisName

% for entry in profile.imports:
${entry} = gremlin.util.load_module("${entry}")
% endfor

tts = gremlin.tts.TextToSpeech()

# Create all required decorators
% for device_id, modes in decorators.items():
    % for mode_name, data in modes.items():
${data.decorator_name} = gremlin.input_devices.JoystickDecorator(
    name="${data.device_name}",
    device_id=${device_id},
    mode="${mode_name}"
)
    % endfor
% endfor

# Create action setup code
% for entry in setup:
${entry}
% endfor


# Create container and action combinations used in the callbacks
% for device_id, modes in callbacks.items():
    % for mode_name, callbacks_data in modes.items():
        % for input_item in callbacks_data:
${util.indent(input_item.code_block.container, 0)}
        % endfor
    % endfor
% endfor

<%
template_map = {
    InputType.JoystickAxis: "axis_callback.tpl",
    InputType.JoystickButton: "button_callback.tpl",
    InputType.JoystickHat: "hat_callback.tpl",
    InputType.Keyboard: "keyboard_callback.tpl"
}
%>

% for device_id, modes in callbacks.items():
    % for mode_name, callbacks_data in modes.items():
        % for input_item in callbacks_data:
<%include
    file="${template_map[input_item.input_item.input_type]}"
    args="
        input_item=input_item.input_item,
        decorator_name=input_item.decorator_name,
        mode_index=input_item.mode_index,
        parameter_list=input_item.parameter_list,
        device_name=input_item.device_name,
        code_block=input_item.code_block
    "
/>
        % endfor
    % endfor
% endfor
