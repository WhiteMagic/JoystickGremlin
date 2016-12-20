<%
    var_lower = "merge_axis_{:04d}_lower".format(idx)
    var_upper = "merge_axis_{:04d}_upper".format(idx)
    fn_lower = "merge_axis_lower_cb_{:04d}".format(idx)
    fn_upper = "merge_axis_upper_cb_{:04d}".format(idx)
    dev_l = get_device_id(
        entry["lower"]["hardware_id"],
        entry["lower"]["windows_id"]
    )
    dev_u = get_device_id(
        entry["upper"]["hardware_id"],
        entry["upper"]["windows_id"]
    )
    dec_lower = decorator_map[dev_l][entry["mode"]]
    dec_upper = decorator_map[dev_u][entry["mode"]]
    function_name = "merge_axis_{:04d}".format(idx)
%>

@${dec_lower}.axis(${entry["lower"]["axis_id"]}, always_execute=False)
def ${fn_lower}(event, vjoy):
    global ${var_lower}
    ${var_lower} = event.value
    ${function_name}(vjoy)

@${dec_upper}.axis(${entry["upper"]["axis_id"]}, always_execute=False)
def ${fn_upper}(event, vjoy):
    global ${var_upper}
    ${var_upper} = event.value
    ${function_name}(vjoy)
