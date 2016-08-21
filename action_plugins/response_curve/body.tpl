${helpers["format_condition"](entry.condition)}
        value = gremlin.input_devices.deadzone(value, ${entry.deadzone[0]}, ${entry.deadzone[1]}, ${entry.deadzone[2]}, ${entry.deadzone[3]})
        value = ${curve_name}(value)