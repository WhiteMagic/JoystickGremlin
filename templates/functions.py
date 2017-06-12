import gremlin.base_classes
import gremlin.util


def get_device_id(context, hardware_id, windows_id):
    return gremlin.util.get_device_id(hardware_id, windows_id)


def indent(context, content, spaces, end="\n"):
    text = ""
    lines = [line for line in content.splitlines() if len(line) > 0]
    if len(lines) > 0:
        text += "{}{}".format(lines[0], end)
        for line in lines[1:-1]:
            text += "{}{}{}".format(" " * spaces, line, end)
        if len(lines) > 1:
            text += "{}{}".format(" " * spaces, lines[-1])
    return text


def coords_to_string(context, coordinates):
    return "[{}]".format(", ".join(
            ["({:.4f}, {:.4f})".format(e[0], e[1]) for e in coordinates])
        )


def key_identifier(context, input_item):
    key = gremlin.macro.key_from_code(
        input_item.input_id[0],
        input_item.input_id[1]
    )
    return "key_{}".format(hex(key.virtual_code))


def key_lookup_name(context, input_item):
    key = gremlin.macro.key_from_code(
        input_item.input_id[0],
        input_item.input_id[1]
    )
    return key.lookup_name


def condition(context, cond):
    direction_to_tuple = {
        "center": "(0, 0)",
        "north": "(0, 1)",
        "north-east": "(1, 1)",
        "east": "(1, 0)",
        "south-east": "(1, -1)",
        "south": "(0, -1)",
        "south-west": "(-1, -1)",
        "west": "(-1, 0)",
        "north-west": "(-1, 1)"
    }

    if cond is None:
        return "None"
    else:
        if isinstance(cond, gremlin.base_classes.AxisActivationCondition):
            return "gremlin.actions.AxisButton({}, {})".format(
                cond.lower_limit,
                cond.upper_limit
            )
        elif isinstance(cond, gremlin.base_classes.HatActivationCondition):
            return "gremlin.actions.HatButton([{}])".format(
                ", ".join([direction_to_tuple[v] for v in cond.directions])
            )
