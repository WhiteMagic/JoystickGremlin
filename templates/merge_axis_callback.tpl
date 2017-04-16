<%page args="entry,decorator_data,index"/>
<%namespace name="util" module="templates.functions"/>
<%
    var_lower = "merge_axis_{:04d}_lower".format(index)
    var_upper = "merge_axis_{:04d}_upper".format(index)
    fn_lower = "merge_axis_lower_cb_{:04d}".format(index)
    fn_upper = "merge_axis_upper_cb_{:04d}".format(index)
    dev_l = util.get_device_id(
        entry["lower"]["hardware_id"],
        entry["lower"]["windows_id"]
    )
    dev_u = util.get_device_id(
        entry["upper"]["hardware_id"],
        entry["upper"]["windows_id"]
    )
    dec_lower = decorator_data[dev_l][entry["mode"]].decorator_name
    dec_upper = decorator_data[dev_u][entry["mode"]].decorator_name
    function_name = "merge_axis_{:04d}".format(index)
%>
${var_lower} = 0
${var_upper} = 0

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


def ${function_name}(vjoy):
    vjoy[${entry["vjoy"]["device_id"]}].axis(${entry["vjoy"]["axis_id"]}).value = (${var_lower} - ${var_upper}) / 2.0