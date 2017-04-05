def indent(context, content, spaces):
    text = ""
    lines = [line for line in content.splitlines() if len(line) > 0]
    if len(lines) > 0:
        text += "{}\n".format(lines[0])
        for line in lines[1:-1]:
            text += "{}{}\n".format(" " * spaces, line)
        if len(lines) > 1:
            text += "{}{}".format(" " * spaces, lines[-1])
    return text
