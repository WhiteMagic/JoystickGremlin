@gremlin.input_devices.keyboard("${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}", "${mode}", always_execute=${input_item.always_execute})
def keyboard_${mode_index}_${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}(${param_list}):
    is_pressed = event.is_pressed
${"\n".join(code["body"])}

