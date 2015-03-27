<%!
    def coords2str(container):
        return "[{}]".format(", ".join(["({:.4f}, {:.4f})".format(e[0], e[1]) for e in container]))
%>\
% if entry.mapping_type == "cubic-spline":
${curve_name} = gremlin.spline.CubicSpline(${coords2str(entry.control_points)})
% elif entry.mapping_type == "cubic-bezier-spline":
${curve_name} = gremlin.spline.CubicBezierSpline(${coords2str(entry.control_points)})
% endif
