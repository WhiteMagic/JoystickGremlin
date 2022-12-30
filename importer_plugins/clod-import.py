"""Populates bindings from IL-2 CLoD config file to current Profile

Lines starting in "[" or ";" are ignored. Config entries that do not
relate to key bindings (such as "difficulty"; axis sensitivity and
dead zones; and chat window settings) are ignored.

Since hats are not supported by Joystick Gremlin bindings,
"Pov" entries are bound to VJoy buttons instead.

Optional arguments:

    -m, --device_map <VJoy_ID> <CLoD_ID>
            VJoy ID number and associated CLoD ID string; only one
            pair may be specified per flag; multiple flags may be
            specified
            
    --ignore_unmapped
            joystick devices which have not been mapped to a VJoy ID
            will be ignored; if this is not specified, all unmapped
            joystick devices are reassigned to the first available 
            VJoy device

    --ignore_keyboard
            keyboard assignments found in the config file will NOT
            be imported; if this is not specified, all keyboard
            assignments will be imported to vjoy buttons

Arguments example: 

    To assign bindings from "vJoy_Device-66210FF9" to VJoy 1 and to
    remap all remaining buttons and axes to the first available VJoy:
    
    -m 1 66210FF9
    
    To additionally ignore any keyboard buttons (i.e. those that
    have not been assigned to a secondary device):
    
    -m 1 66210FF9 --ignore_keyboard
                        
"""

import re
import shlex
import argparse
import gremlin.error

import_filter = "CLoD Config (*.ini)"
_comment_flags = ["[", ";"]
_ignore_keyboard = False
_ignore_unmapped = False
_vjoy_map = {}

_axis_string_to_id = {
    "AXE_X":    1,
    "AXE_Y":    2,
    "AXE_Z":    3,
    "AXE_RX":   4,
    "AXE_RY":   5,
    "AXE_RZ":   6,
    "AXE_U":    7,
    "AXE_V":    8,
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, clod_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        vjoy_id, clod_id = values
        try:
            vjoy_id = int(vjoy_id)
        except ValueError:
            raise gremlin.error.ImporterError((
                "Invalid VJoy_ID argument: '{}' is not a valid integer"
                ).format(vjoy_id))
        clod_id = clod_id.replace("vJoy_Device-","")
        
        # append and return
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, clod_id])
        setattr(namespace, self.dest, items)

def main(file_lines, arg_string):
    """Process passed args, run importer with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _vjoy_map, _ignore_keyboard, _ignore_unmapped
    
    try:
        args = _parse_args(shlex.split(arg_string))
    except gremlin.error.ImporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check importer description for details."
        raise gremlin.error.ImporterError(msg)
    
    _ignore_keyboard = args.ignore_keyboard
    _ignore_unmapped = args.ignore_unmapped
    if args.device_map is not None:
        for vjoy_id, clod_id in args.device_map:
            _vjoy_map["vJoy_Device-{}".format(clod_id)] = vjoy_id
    
    return _import(file_lines)

def _parse_args(args):
    """Parse optional arg string
    
    Joystick Gremlin hangs if argparse exists with a write to terminal.
    To avoid this:
    
        1. Set `add_help=False` to invalidate '-h' or '--help' outputs
        2. Use `parser.parse_known_args(args)` to filter for unknown args
        
    Here we also raise an ImporterError if unknown args were passed.
    Although this is not strictly necessary, it to the user's benefit to
    error on a typo rather than silently ignoring it.
    
    param: args argument list from arg_string.split()
    """
    
    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument("-m", "--device_map", 
                        nargs=2, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID','CLOD_ID'), 
                        help="vjoy id and associated CLoD id"
                        )
    parser.add_argument("--ignore_unmapped", 
                        action='store_true',
                        help="do not import unmapped joystick devices"
                        )
    parser.add_argument("--ignore_keyboard", 
                        action='store_true',
                        help="do not import keyboard assignments"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ImporterError(msg)
    return valid

def _import(file_lines):
    """Parse non-commented file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    found = {}
    for line in file_lines:
        if line.strip() and line.strip()[0] not in _comment_flags:
            item = _clod_item2vjoy_item(line)
            if item:
                input_type = next(iter(item))
                if input_type in found.keys():
                    found[input_type].update(item[input_type])
                else:
                    found.update(item)
    return found

def _clod_item2vjoy_item(clod_item):
    """Interpret clod entry to vjoy output
    
    :param clod_item CLoD .ini line to parse
    :return vjoy_item dict entry
    """
    assignment = clod_item.split("=")[0].strip()
    binding = clod_item.split("=")[-1].strip()
    clod_dev = assignment.split("+")[0]
    clod_input = assignment.split("+")[-1]
    
    # remove "Pov" assignments in device string 
    # i.e. "Pov270 DevXXX" returns "DevXXX"
    clod_dev = re.sub(r"^Pov\d+\s","",clod_dev)
    
    # return empty if invalid assignment
    if not _is_valid_assignment(assignment) \
       or not _is_valid_binding(binding):
        return {}
    
    # get vjoy_id
    if clod_dev in _vjoy_map:
        vjoy_id = _vjoy_map[clod_dev]
    elif not _ignore_unmapped:
        vjoy_id = ""
    else:
        return {}
    
    # get input_type and id
    if clod_input in _axis_string_to_id:
        input_type = "axis"
        input_id = _axis_string_to_id[clod_input]
    elif "Key" in clod_input:
        input_type = "button"
        input_id = int(clod_input.split("Key")[-1])
    elif "Pov" in clod_input:
        input_type = "button"
        input_id = "" # bindings don't support hats, so assign to button
    elif not _ignore_keyboard:
        input_type = "button"
        input_id = ""
    else:
        return {}
        
    # assemble return
    vjoy_item = {}
    vjoy_item[input_type] = {}
    vjoy_item[input_type][binding] = {
        "input_id": input_id,
        "device_id": vjoy_id,
        "description": ""
    }
    return vjoy_item

def _is_valid_assignment(clod_assignment):
    """Returns false if a clod keyword is found"""
    
    invalid_keywords = [
        "hotkeys",
        "difficulty",
        "lastSingleMiss"
    ]
    
    if clod_assignment in invalid_keywords:
        return False    # non-bindable keyword -- ignore
    elif re.search(r"^[-?|\d]\d+$", clod_assignment):
        return False    # multi-digit string for LastFocus field -- ignore
    elif re.search(r"^\d+:-?\d+$", clod_assignment):
        return False    # digit:digit string for ChatWindow field -- ignore
    else:
        return True
    
def _is_valid_binding(clod_binding):
    """Returns false if a non-keyword is found"""
    
    if re.sub(r"[-\.\s]","",clod_binding).isdigit():
        return False    # string of digits for axis sensitivities -- ignore
    else:
        return True