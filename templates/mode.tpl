<%
from gremlin.event_handler import InputType
%>
% if len(mode._config[InputType.Keyboard]) == 0:
${decorator} = gremlin.input_devices.JoystickDecorator("${mode.parent.name}", ${mode.parent.index}, "${mode.name}")
% endif
