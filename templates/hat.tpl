<%!
    import gremlin.util
    def wid(input_item):
        hid, wid = gremlin.util.extract_ids(gremlin.util.device_id(input_item.parent.parent))
        if wid != -1:
            return "_{}".format(wid)
        else:
            return ""
%>\
@${decorator}.hat(${input_item.input_id}, always_execute=${input_item.always_execute})
def ${device_name}${wid(input_item)}_${mode}_hat_${input_item.input_id}(${param_list}):
    value = event.value
${"\n".join(code["body"])}

