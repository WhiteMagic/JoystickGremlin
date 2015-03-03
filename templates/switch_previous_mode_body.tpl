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
        gremlin.control_action.switch_to_previous_mode()