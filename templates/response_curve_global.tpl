<%!
    def coords2str(container):
        return "[{}]".format(", ".join(["({:.4f}, {:.4f})".format(e[0], e[1]) for e in container]))
%>\
${curve_name} = gremlin.spline.CubicSpline(${coords2str(entry.control_points)})
