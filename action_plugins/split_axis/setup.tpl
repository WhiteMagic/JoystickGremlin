def split_axis_${id}(value):
    if value < ${entry.center_point}:
        range = -1.0 - ${entry.center_point}
        vjoy[${entry.axis1[0]}].axis(${entry.axis1[1]}).value = \
            ((value - ${entry.center_point}) / range) * 2.0 - 1.0
        vjoy[${entry.axis2[0]}].axis(${entry.axis2[1]}).value = -1.0
    else:
        range = 1.0 - ${entry.center_point}
        vjoy[${entry.axis2[0]}].axis(${entry.axis2[1]}).value = \
            ((value - ${entry.center_point}) / range) * 2.0 - 1.0
        vjoy[${entry.axis1[0]}].axis(${entry.axis1[1]}).value = -1.0
split_axis_wrapper_${id} = gremlin.action_containers.run_function(
    split_axis_${id}, True, False
)