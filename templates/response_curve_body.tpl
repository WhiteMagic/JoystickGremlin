<%!
    import action.common
    def format_condition(condition):
        if isinstance(condition, action.common.ButtonCondition):
            if condition.on_press and condition.on_release:
                return "    if True:"
            elif condition.on_press:
                return "    if is_pressed:"
            elif condition.on_release:
                return "    if not is_pressed:"
            else:
                return "    if False:"
        else:
            return "    if True:"
%>\
${format_condition(entry.condition)}
        value = gremlin.input_devices.deadzone(value, ${entry.deadzone[0]}, ${entry.deadzone[1]}, ${entry.deadzone[2]}, ${entry.deadzone[3]})
        value = ${curve_name}(value)