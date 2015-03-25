<%!
    import gremlin.util
    def str2bool(text):
        return text.lower() in ["true", "yes", "t", "1"]

    def wid(input_item):
        hid, wid = gremlin.util.extract_ids(gremlin.util.device_id(input_item.parent.parent))
        if wid != -1:
            return "_{}".format(wid)
        else:
            return ""
%>\
@${decorator}.axis(${input_item.input_id})
def ${device_name}${wid(input_item)}_${mode}_axis_${input_item.input_id}(${param_list}):
    value = event.value
${"\n".join(code["body"])}
