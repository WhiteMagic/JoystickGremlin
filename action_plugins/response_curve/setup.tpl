<%namespace name="util" module="templates.functions"/>
% if entry.mapping_type == "cubic-spline":
${curve_name} = gremlin.spline.CubicSpline(${util.coords_to_string(entry.control_points)})
% elif entry.mapping_type == "cubic-bezier-spline":
${curve_name} = gremlin.spline.CubicBezierSpline(${helpers["coords_to_string"](entry.control_points)})
% endif
${deadzone_name} = lambda value: gremlin.input_devices.deadzone(value, ${entry.deadzone[0]}, ${entry.deadzone[1]}, ${entry.deadzone[2]}, ${entry.deadzone[3]})
