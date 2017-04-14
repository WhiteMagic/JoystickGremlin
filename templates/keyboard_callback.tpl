<%page args="input_item, decorator_name, mode_index, parameter_list, device_name, code_block"/>
<%namespace name="util" module="templates.functions"/>
@gremlin.input_devices.keyboard("${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}", "${input_item.parent.name}", always_execute=${input_item.always_execute})
def keyboard_${mode_index}_${gremlin.macro.key_from_code(input_item.input_id[0], input_item.input_id[1]).name}(${parameter_list}):
    """${input_item.description}"""
    value = gremlin.actions.Value(event.is_pressed)
    ${util.indent(code_block.body, 4)}