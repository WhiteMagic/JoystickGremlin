<%!
    import gremlin
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
%>\
@gremlin.input_devices.keyboard("${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}", "${mode}", always_execute=${input_item.always_execute})
def keyboard_${mode_index}_${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}(${param_list}):
    is_pressed = event.is_pressed
${"\n".join(code["body"])}

