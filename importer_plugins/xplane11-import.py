"""Populates profile bindings from XPlane 11 profile (.prf) file from template.

Optional arguments:

    -x, --axis_map <VJoy_ID> <first_AXIS_use_id> <last_AXIS_use_id>
            VJoy ID number and corresponding axis first/last indices 
            within the given .prf file template; each vjoy mapping must 
            include the vjoy id, axis start index, and axis last
            index, in that order
            
    -b, --butn_map <VJoy_ID> <first_BUTN_use_id> <last_BUTN_use_id>
            VJoy ID number and corresponding butn first/last indices 
            within the given .prf file template; each vjoy mapping must 
            include the vjoy id, butn start index, and butn last
            index, in that order
    
    --ignore_unmapped
            joystick devices which have not been mapped to a VJoy ID
            will be ignored; if this is not specified, all unmapped
            joystick devices are reassigned to the first available 
            VJoy device

Arguments example: 

    To only import axis items 0 through 7 to VJoy 1 and button items 
    50 to 75 to VJoy 2, use:
    
    -x 1 0 7 -x 2 50 75 --ignore_unmapped
    
    To additionally import remaining entries to the first unbound in 
    the profile, simply remove "--ignore_unmapped"

To find the axis/button start index for each vjoy device, manually 
bind the VJoy X axis and VJoy Button 1 in XPlane 11 in a new, empty profile.
Save the profile in XPlane 11, then navigate to the corresponding 
.prf file on disk. Open the .prf file in a text editor, then search for the 
first non-empty entry binding (for axes, this is any value other than "0"; 
for buttons, this is any value other than "sim/none/none"). 

Each entry should look one of the following: 
    "_joy_AXIS_use<AXIS_use_id>"
    "_joy_BUTN_use<BUTN_use_id>"

You can then enter the <AXIS_use_id> and <BUTN_use_id> as input arguments to 
this exporter for the VJoy ID used. Repeat the process for all VJoy devices.
    
"""

import re
import argparse
import gremlin.error
from gremlin.common import InputType

import_filter = "XPlane 11 Profile (*.prf)"
_ignore_unmapped = False

# common data for input types
_axis = InputType.JoystickAxis
_butn = InputType.JoystickButton
_type_data = {
    _axis: {
        "vjoy_map": {}, 
        "first_id": {}, 
        "default": "0", 
        "entry_format": r"_joy_AXIS_use{} {}"
    },
    _butn: {
        "vjoy_map": {}, 
        "first_id": {}, 
        "default": "sim/none/none", 
        "entry_format": r"_joy_BUTN_use{} {}"
    },
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, clod_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        for i in values:
            try:
                i = int(i)
            except ValueError:
                raise gremlin.error.ExporterError((
                    "Invalid map argument: '{}' is not a valid integer"
                    ).format(i))
        
        # append and return
        vjoy_id, first_id, last_id = values
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, first_id, last_id])
        setattr(namespace, self.dest, items)

def main(file_lines, arg_string):
    """Process passed args, run importer with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _type_data, _ignore_unmapped
    
    try:
        args = _parse_args(arg_string.split())
    except gremlin.error.ImporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check importer description for details."
        raise gremlin.error.ImporterError(msg)
    
    _ignore_unmapped = args.ignore_unmapped
    if args.axis_map is not None:
        for vjoy_id, first, last in args.axis_map:
            vjoy_map = {str(key): vjoy_id for key in range(int(first), int(last))}
            _type_data[_axis]["vjoy_map"].update(vjoy_map)
            _type_data[_axis]["first_id"][vjoy_id] = first
    if args.butn_map is not None:
        for vjoy_id, first, last in args.butn_map:
            vjoy_map = {str(key): vjoy_id for key in range(int(first), int(last))}
            _type_data[_butn]["vjoy_map"].update(vjoy_map)
            _type_data[_butn]["first_id"][vjoy_id] = first
    return _import(file_lines)

def _parse_args(args):
    """Parse optional arg string
    
    Joystick Gremlin hangs if argparse exists with a write to terminal.
    To avoid this:
    
        1. Set `add_help=False` to invalidate '-h' or '--help' outputs
        2. Use `parser.parse_known_args(args)` to filter for unknown args
        
    Here we also raise an ExporterError if unknown args were passed.
    Although this is not strictly necessary, it to the user's benefit to
    error on a typo rather than silently ignoring it.
    
    param: args argument list from arg_string.split()
    """
    
    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument("-x", "--axis_map", 
                        nargs=3, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID', 'FIRST_AXIS_ID', 'LAST_AXIS_ID'), 
                        help="vjoy id and associated first and last axis ids"
                        )
    parser.add_argument("-b", "--butn_map", 
                        nargs=3, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID', 'FIRST_BUTN_ID', 'LAST_BUTN_ID'), 
                        help="vjoy id and associated first and last button ids"
                        )
    parser.add_argument("--ignore_unmapped", 
                        action='store_true',
                        help="do not import unmapped joystick devices"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ExporterError(msg)
    return valid

def _import(file_lines):
    """Parse non-commented file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    found = {}
    for line in file_lines:
        item = _xp11_item2vjoy_item(line)
        if item:
            input_type = next(iter(item))
            if input_type in found.keys():
                found[input_type].update(item[input_type])
            else:
                found.update(item)
    return found

def _xp11_item2vjoy_item(xp11_item):
    """Return vjoy item from xplane 11 entry"""
    
    # match strings for valid axis or button items
    axis_match = _type_data[_axis]["entry_format"].format("\d*", "\S*")
    butn_match = _type_data[_butn]["entry_format"].format("\d*", "\S*")
    
    # match strings for axis or button items defaults
    axis_empty = (_type_data[_axis]["entry_format"]
                 ).format("\d*", _type_data[_axis]["default"])
    butn_empty = (_type_data[_butn]["entry_format"]
                 ).format("\d*", _type_data[_butn]["default"])
    
    # find non empty axes or buttons
    if   ( re.match(axis_match, xp11_item) and 
           not re.match(axis_empty, xp11_item) ):
        vjoy_item = _parse_entry_of_type(xp11_item, _axis)
    elif ( re.match(butn_match, xp11_item) and
           not re.match(butn_empty, xp11_item) ): 
        vjoy_item = _parse_entry_of_type(xp11_item, _butn)
    else: # return empty if neither found
        vjoy_item = {}
        
    return vjoy_item

def _parse_entry_of_type(xp11_item, input_type):
    """Parse xplane 11 entry using given type"""
    
    input_type_name = InputType.to_string(input_type)
    vjoy_map = _type_data[input_type]["vjoy_map"]
    
    # get binding, vjoy_id, and input_id
    binding = xp11_item.split()[1]
    input_id = re.sub(r"^\D*", "",xp11_item.split()[0])
    if input_id in vjoy_map:
        vjoy_id = vjoy_map[input_id]
        first_id = int(_type_data[input_type]["first_id"][vjoy_id])
        input_id = int(input_id) - first_id + 1
    elif not _ignore_unmapped:
        vjoy_id = ""
        input_id = ""
    else:
        return {}
    
    # assemble return
    vjoy_item = {}
    vjoy_item[input_type_name] = {}
    vjoy_item[input_type_name][binding] = {
        "input_id": input_id,
        "device_id": vjoy_id,
        "description": ""
    }
    return vjoy_item
