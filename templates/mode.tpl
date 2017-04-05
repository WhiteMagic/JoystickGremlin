<%!
from gremlin.event_handler import InputType
from gremlin.profile import DeviceType
import gremlin
%>
% if mode.parent.type != DeviceType.Keyboard:
${decorator} = gremlin.input_devices.JoystickDecorator(
    name="${mode.parent.name}",
    device_id=${gremlin.util.device_id(mode.parent)},
    mode="${mode.name}"
)
% endif