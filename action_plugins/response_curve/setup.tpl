% if entry.mapping_type == "cubic-spline":
${curve_name} = gremlin.spline.CubicSpline(${helpers["coords_to_string"](entry.control_points)})
% elif entry.mapping_type == "cubic-bezier-spline":
${curve_name} = gremlin.spline.CubicBezierSpline(${helpers["coords_to_string"](entry.control_points)})
% endif
