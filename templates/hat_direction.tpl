@${decorator}.hat(${int(input_item.input_id / 10)}, always_execute=${input_item.always_execute})
def ${device_name}${helpers["wid"](input_item)}_${mode_index}_hat_${input_item.input_id}(${param_list}):
    value = event.value
    if gremlin.util.hat_tuple_to_index(value) == ${(input_item.input_id % 10)}:
%for block in code["body"]:
%for line in block.split("\n"):
    ${line}
%endfor
%endfor
