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
${data["decorator_name"]} = gremlin.input_devices.JoystickDecorator(
    name="${data['device_name']}",
    device_id=${device_id},
    mode="${mode_name}"
)
    % endfor
% endfor

% for device_id, modes in callbacks.items():
    % for mode_name, callbacks_data in modes.items():
        % for entry in callbacks_data:
${util.indent(entry["code_block"].static, 0)}
        % endfor
    % endfor
% endfor

<%
template_map = {
    InputType.JoystickAxis: "axis_callback.tpl",
    InputType.JoystickButton: "button_callback.tpl",
    InputType.JoystickHat: "hat_callback.tpl",
    InputType.Keyboard: "button_callback.tpl"
}
%>

% for device_id, modes in callbacks.items():
    % for mode_name, callbacks_data in modes.items():
        % for entry in callbacks_data:
<%include
    file="${template_map[entry['input_item'].input_type]}"
    args="
        input_item=entry['input_item'],
        decorator_name=entry['decorator_name'],
        mode_index=entry['mode_index'],
        parameter_list=entry['parameter_list'],
        device_name=entry['device_name'],
        code_block=entry['code_block']
    "
/>
        % endfor
    % endfor
% endfor
