${helpers["format_condition"](entry.condition)}
        gremlin.control_action.cycle_modes([${", ".join("\"{}\"".format(mode) for mode in entry.mode_list)}])