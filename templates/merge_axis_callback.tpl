<%
    var_lower = "merge_axis_{:04d}_lower".format(idx)
    var_upper = "merge_axis_{:04d}_upper".format(idx)
    fn_lower = "merge_axis_lower_cb_{:04d}".format(idx)
    fn_upper = "merge_axis_upper_cb_{:04d}".format(idx)
    dec_lower = decorator_map[entry["lower"][0]][entry["mode"]]
    dec_upper = decorator_map[entry["upper"][0]][entry["mode"]]
    function_name = "merge_axis_{:04d}".format(idx)
%>

@${dec_lower}.axis(${entry["lower"][1]}, always_execute=False)
def ${fn_lower}(event, vjoy):
    global ${var_lower}
    ${var_lower} = event.value
    ${function_name}(vjoy)

@${dec_upper}.axis(${entry["upper"][1]}, always_execute=False)
def ${fn_upper}(event, vjoy):
    global ${var_upper}
    ${var_upper} = event.value
    ${function_name}(vjoy)
