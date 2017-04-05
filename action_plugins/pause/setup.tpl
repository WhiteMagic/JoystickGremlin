<%namespace file="../../templates/blocks.tpl" import="*"/>
${axis_button(
    id,
    input_type,
    InputType,
    entry,
    "pause_{:d}(is_pressed)".format(id)
)}