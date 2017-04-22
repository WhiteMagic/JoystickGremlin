<%page args="input_item, decorator_name, mode_index, parameter_list, device_name, code_block"/>
<%namespace name="util" module="templates.functions"/>
@gremlin.input_devices.keyboard("${util.key_lookup_name(input_item)}", "${input_item.parent.name}", always_execute=${input_item.always_execute})
def keyboard_${mode_index}_${util.key_identifier(input_item)}(${parameter_list}):
    """${input_item.description}"""
    value = gremlin.actions.Value(event.is_pressed)
    ${util.indent(code_block.body, 4)}