<%!
    import gremlin.util
    def list2python(params):
        if len(params) == 0:
            return ""
        elif len(params) == 1:
            return "\"{0}\"".format(params[0])
        else:
            return "[" + ", ".join(["\"{0}\"".format(v) for v in params]) + "]"

    def format_condition(cond):
        if cond.on_press and cond.on_release:
            return "if True:"
        elif cond.on_press and not cond.on_release:
            return "if is_pressed:"
        elif not cond.on_press and cond.on_release:
            return "if not is_pressed:"
        else:
            return "if False:"

    def wid(input_item):
        hid, wid = gremlin.util.extract_ids(gremlin.util.device_id(input_item.parent.parent))
        if wid != -1:
            return "_{}".format(wid)
        else:
            return ""
%>\
@${decorator}.button(${input_item.input_id}, always_execute=${input_item.always_execute})
def ${device_name}${wid(input_item)}_${mode_index}_button_${input_item.input_id}(${param_list}):
    is_pressed = event.is_pressed
${"\n".join(code["body"])}

