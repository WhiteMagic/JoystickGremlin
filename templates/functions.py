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


def create_condition(context, condition):
    if isinstance(condition, gremlin.base_classes.AxisCondition):
        return "gremlin.actions.AxisCondition()"
    elif isinstance(condition, gremlin.base_classes.ButtonCondition):
        return "gremlin.actions.ButtonCondition({}, {})".format(
            condition.on_press,
            condition.on_release
        )
    elif isinstance(condition, gremlin.base_classes.HatCondition):
        valid_conditions = []
        if condition.on_n:
            valid_conditions.append((0, 1))
        if condition.on_ne:
            valid_conditions.append((1, 1))
        if condition.on_e:
            valid_conditions.append((1, 0))
        if condition.on_se:
            valid_conditions.append((1, -1))
        if condition.on_s:
            valid_conditions.append((0, -1))
        if condition.on_sw:
            valid_conditions.append((-1, -1))
        if condition.on_w:
            valid_conditions.append((-1, 0))
        if condition.on_nw:
            valid_conditions.append((-1, 1))
        return "gremlin.actions.HatCondition({})".format(
            "[{}]".format(
                ", ".join(["({:d}, {:d})".format(v[0], v[1]) for v in valid_conditions])
            )
        )


def coords_to_string(context, coordinates):
    return "[{}]".format(", ".join(
            ["({:.4f}, {:.4f})".format(e[0], e[1]) for e in coordinates])
        )
