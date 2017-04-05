@${decorator}.hat(${input_item.input_id}, always_execute=${input_item.always_execute})
def ${device_name}${helpers["wid"](input_item)}_${mode_index}_hat_${input_item.input_id}(${param_list}):
    """${input_item.description}"""
    direction = event.value
${"\n".join(code["body"])}

