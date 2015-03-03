@${decorator}.hat(${input_item.input_id}, always_execute=${input_item.always_execute})
def ${device_name}_${mode}_hat_${input_item.input_id}(${param_list}):
    value = event.value
${"\n".join(code["body"])}

