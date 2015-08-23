# -*- coding: utf-8; -*-

# Copyright (C) 2015 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt5 import QtGui, QtPrintSupport

from mako.template import Template

import gremlin
from gremlin.common import UiInputType

templates = {
    "pdf": {

    "tpl_main": Template("""<!DOCTYPE html>

<html>

<head>
    <meta charset="utf-8">

    <style type="text/css">
        td.inherit {
            color: #c0c0c0;
            width: 100px;
        }
        td.input_name {
            width: 200px;
        }
        td.description {

        }
    </style>
</head>

<body>

<div>
%for mode in modes:
${mode}
%endfor
</div>

</body>

</html>"""),

    "tpl_mode": Template("""
<h4>${mode}</h4>

%for device in devices:
<table class="table table-condensed table-striped">
${device}
</table>
%endfor
"""),

    "tpl_device": Template("""
<tr>
    <th colspan="3">${device}</th>
</tr>
%for entry in data:
<tr>
    <td class="input_name">${entry[0]}</td>
    <td></td>
    <td class="description">${entry[1]}</td>
    <td class="inherit">
    %if entry[2] is not None:
    ${entry[2]}
    %endif
    </td>
</tr>
%endfor
""")
    },

    "html": {

    "tpl_main": Template("""<!DOCTYPE html>

<html>

<head>
    <meta charset="utf-8">

    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap-theme.min.css">

    <script src="http://code.jquery.com/jquery-2.1.4.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>

    <style type="text/css">
        td.inherit {
            color: #c0c0c0;
            width: 100px;
        }
        td.input_name {
            width: 200px;
        }
        td.description {

        }
    </style>
</head>

<body>

<div class="container">

<div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
%for mode in modes:
${mode}
%endfor
</div>

</div>

</body>

</html>"""),

    "tpl_mode": Template("""
<div class="panel panel-default">
    <div class="panel-heading" role="tab" id="heading${mode}">
        <h4 class="panel-title">
        % if mode_id == 0:
            <a data-toggle="collapse" data-parent="#accordion"
                href="#collapse${mode_id}" aria-expanded="true"
                aria-controls="collapse${mode_id}">
                ${mode}
            </a>
        % else:
            <a class="collapsed" data-toggle="collapse"
                data-parent="#accordion" href="#collapse${mode_id}"
                aria-expanded="false" aria-controls="collapse${mode_id}">
                ${mode}
            </a>
        % endif
        </h4>
    </div>

    <div id="collapse${mode_id}" class="panel-collapse collapse in"
        role="tabpanel" aria-labelledby="heading${mode_id}">
        <div class="panel-body">

            %for device in devices:
            <table class="table table-condensed table-striped">
            ${device}
            </table>
            %endfor

        </div>
    </div>
</div>
"""),

    "tpl_device": Template("""
<tr>
    <th colspan="3">${device}</th>
</tr>
%for entry in data:
<tr>
    <td class="input_name">${entry[0]}</td>
    <td class="description">${entry[1]}</td>
    <td class="inherit">
    %if entry[2] is not None:
    ${entry[2]}
    %endif
    </td>
</tr>
%endfor
""")
    }
}


def recursive(device, tree, storage):
    """Recursively parses a profile and stores the contents in the required form.

    :param device the device of interest
    :param tree the subtree currently being processed
    :param storage the storage for the extracted data
    """
    for parent, children in tree.items():
        # Ensure the storage structure is correctly initialized
        if parent not in storage:
            storage[parent] = {}
        for child in children:
            if child not in storage:
                storage[child] = {}

        # Insert actions of parent into parent
        mode = device.modes[parent]
        for input_type, items in mode._config.items():
            for item in items.values():
                if len(item.actions) > 0:
                    key = (input_type, item.input_id)
                    storage[parent][key] = (item.description, None)

                    for child in children:
                        storage[child][key] = (item.description, parent)

        # Recursively process the remainder of the inheritance tree
        recursive(device,  children, storage)


def sort_data(data):
    """Returns a new list sorted by input type.

    :param data the data to sort
    :return the sorted data
    """
    sorted_data = []

    for input_type in gremlin.common.UiInputType:
        for key, value in sorted(data.items(), key=lambda x: x[0][1]):
            if input_type == key[0]:
                sorted_data.append(
                    [format_input_name(key[0], key[1]), value[0], value[1]]
                )

    return sorted_data


def generate_cheatsheet(file_format, fname, profile):
    """Generates HTML documentation of the provided profile.

    :param file_format the output format
    :param fname the file to store the cheatsheet in
    :param profile the profile to process
    """
    mode_names = sorted(list(profile.devices.values())[0].modes.keys())
    device_keys = sorted(profile.devices.keys())
    device_names = [profile.devices[key].name for key in device_keys]
    device_name_to_key = {}
    for i in range(len(device_keys)):
        device_name_to_key[device_names[i]] = device_keys[i]

    # Build device actions considering inheritance
    inheritance_tree = profile.build_inheritance_tree()
    device_storage = {}
    for key, device in profile.devices.items():
        device_storage[key] = {}
        recursive(device, inheritance_tree, device_storage[key])

    # Accumulate HTML code for the individual mode and device combinations
    device_content = {}
    for mode in mode_names:
        device_content[mode] = {}
        for i, dev in enumerate(device_keys):
            if len(device_storage[dev][mode]) > 0:
                device_content[mode][dev] =\
                    templates[file_format]["tpl_device"].render(
                        data=sort_data(device_storage[dev][mode]),
                        device=device_names[i]
                )

    # Put HTML segments together into a single document
    mode_content = []
    for mode in mode_names:
        if len(device_content[mode]) > 0:
            devices = []
            for name in sorted(device_names):
                if device_name_to_key[name] in device_content[mode]:
                    devices.append(device_content[mode][device_name_to_key[name]])

            mode_content.append(templates[file_format]["tpl_mode"].render(
                mode=mode,
                devices=devices,
                mode_id=len(mode_content)
            ))

    if file_format == "html":
        # Create a single HTML file
        with open(fname, "w") as out:
            out.write(templates[file_format]["tpl_main"]
                      .render(modes=mode_content))
    elif file_format == "pdf":
        doc = QtGui.QTextDocument()
        doc.setDefaultFont(QtGui.QFont("Courier", 10, QtGui.QFont.Normal))
        doc.setHtml(templates[file_format]["tpl_main"]
                    .render(modes=mode_content))
        printer = QtPrintSupport.QPrinter()
        printer.setOutputFileName(fname)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setColorMode(1)
        printer.setFontEmbeddingEnabled(True)
        doc.print(printer)
        printer.newPage()


def format_input_name(input_type, identifier):
    """Returns a formatted name of the provided input.

    :param input_type the type of the input
    :param identifier the identifier of the input
    :return formatted string of the provided input
    """
    type_map = {
        UiInputType.JoystickAxis: "Axis",
        UiInputType.JoystickButton: "Button",
        UiInputType.JoystickHat: "Hat",
        UiInputType.JoystickHatDirection: "Hat Direction",
        UiInputType.Keyboard: "Key",
    }

    if input_type == UiInputType.Keyboard:
        return gremlin.macro.key_from_code(identifier[0], identifier[1]).name
    elif input_type == UiInputType.JoystickHatDirection:
        input_id = int(identifier / 10)
        direction = int(identifier % 10)
        return "Hat {} {}".format(
            input_id,
            gremlin.common.index_to_direction(direction)
        )
    else:
        return "{} {}".format(type_map[input_type], identifier)
