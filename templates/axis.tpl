@${decorator}.axis(${input_item.input_id}, always_execute=${input_item.always_execute})
def ${device_name}${helpers["wid"](input_item)}_${mode_index}_axis_${input_item.input_id}(${param_list}):
    value = event.value
${"\n".join(code["body"])}
