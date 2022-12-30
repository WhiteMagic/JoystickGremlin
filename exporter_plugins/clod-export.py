"""Populates profile bindings to IL-2 CLoD config file from template.

Optional arguments:

    -m, --device_map <VJoy_ID> <CLoD_ID>
            VJoy ID number and associated CLoD ID string; only one
            pair may be specified per flag; multiple flags may be
            specified

    -i, --ignore_flag <ignore_flag>
            binding assignments starting with IGNORE_FLAG are ignored; 
            ignored bindings are not listed in the output file; 
            multiple flags may be specified, but each flag may only 
            consist of one character; default = '#'
                        
Arguments example: 

    To register VJoy 1 as "vJoy_Device-66210FF9", VJoy 2 as 
    "vJoy_Device-A4E92C9", and to ignore any bindings set in Joystick 
    Gremlin starting with '#':
    
    -m 1 66210FF9 -m 2 A4E92C9 -i #
                        
To find the CLoD ID for each VJoy device, manually bind one VJoy 
output in CLoD. CLoD will report VJoy device bindings in the format:

"vJoy_Device-<CLoD_ID>+Key#=<binding>"

You may then register that CLoD_ID with its corresponding VJoy_ID as 
described above.
    
"""

import argparse
import gremlin.error
from gremlin.common import InputType

template_filter = "CLoD Config (*.ini)"
_comment_flags = ["[", ";"]
_ignore_flags = []
_vjoy_map = {}

_axis_id_to_string = {
    1: "AXE_X",
    2: "AXE_Y",
    3: "AXE_Z",
    4: "AXE_RX",
    5: "AXE_RY",
    6: "AXE_RZ",
    7: "AXE_U",
    8: "AXE_V",
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, clod_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        vjoy_id, clod_id = values
        try:
            vjoy_id = int(vjoy_id)
        except ValueError:
            raise gremlin.error.ExporterError((
                "Invalid VJoy_ID argument: '{}' is not a valid integer"
                ).format(vjoy_id))
        clod_id = clod_id.replace("vJoy_Device-","")
        
        # append and return
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, clod_id])
        setattr(namespace, self.dest, items)

def main(bound_vjoy_dict, template_file, arg_string):
    """Process passed args, run exporter with passed binding list and template
    
    :param bound_vjoy_dict BoundVJoy item dictionary, keyed by binding string; provided by Joystick Gremlin
    :param template_file Config template file contents; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Config file contents list with updated bindings; to be saved by Joystick Gremlin with writelines()
    """
    global _vjoy_map, _ignore_flags
    
    try:
        args = _parse_args(arg_string.split())
    except gremlin.error.ExporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check exporter description for details."
        raise gremlin.error.ExporterError(msg)
    
    _ignore_flags = args.ignore_flag
    if args.device_map is not None:
        for vjoy_id, clod_id in args.device_map:
            _vjoy_map[vjoy_id] = "vJoy_Device-{}".format(clod_id)
    
    return _export(bound_vjoy_dict, template_file)

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
    parser.add_argument("-m", "--device_map", 
                        nargs=2, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID','CLOD_ID'), 
                        help="vjoy id and associated CLoD id"
                        )
    parser.add_argument("-i", "--ignore_flag", 
                        nargs='?', 
                        action='append', default=["#"],
                        type=lambda x: x if len(x) <=1 else False, # limit flag to one char at a time
                        help="binding assignments starting with IGNORE_FLAG are ignored"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ExporterError(msg)
    return valid

def _export(bound_vjoy_dict, template_file):
    
    oldfile = template_file
    newfile = []
    
    bound_vjoy_dict = _remove_commented_items(bound_vjoy_dict)
    
    # overwrite old bindings in-place
    for line in oldfile:
        line = line.strip()
        if line and line[0] not in _comment_flags:
            binding = line.split("=")[-1].strip()
            assignment = line.split("=")[0].strip()
            if binding in bound_vjoy_dict.keys():
                bound_item = bound_vjoy_dict[binding]
                line = _vjoy_item2clod_item(bound_item)
                bound_vjoy_dict.pop(binding)
            elif assignment.split("+")[0] in _vjoy_map.values():
                # remove old assignment from output data
                line = "; ={}".format(binding)
        newfile.append(line + "\n")
    
    # append unsorted bindings to file
    newfile.append("\n[Unsorted Gremlin Bindings]\n")
    for bound_item in bound_vjoy_dict.values():
        newfile.append(_vjoy_item2clod_item(bound_item) + "\n")
        
    return newfile

def _remove_commented_items(bound_vjoy_dict):
    """Removes bindings flagged with comment string"""
    cleaned_vjoy_list = {}
    for binding, vjoy_item in bound_vjoy_dict.items():
        if binding[0] not in _ignore_flags:
            cleaned_vjoy_list[binding] = vjoy_item
    return cleaned_vjoy_list
        
def _vjoy_item2clod_item(bound_item):
    """Return vjoy to string for clod
    
    :param bound_item BoundVJoy instance to write
    """
    # get correct device ID as recognized by CLoD
    try:
        device_str = _vjoy_map[bound_item.vjoy_id]
    except KeyError:
        msg = ("Missing device_map argument: "
               "CLoD_ID not defined for vJoy Device {:d}"
              ).format(bound_item.vjoy_id)
        raise gremlin.error.ExporterError(msg)
    
    # get correct axis/button naming for clod
    input_type = bound_item.input_type
    if input_type == InputType.JoystickAxis:
        input_str = _axis_id_to_string[bound_item.input_id]
    elif input_type == InputType.JoystickButton:
        input_str = "Key{:d}".format(bound_item.input_id - 1)
    else:
        msg = ("Invalid binding: "
               "CLoD export not defined for outputs of type \"{}\""
              ).format(InputType.to_string(input_type))
        raise gremlin.error.ExporterError(msg)
    
    return  "{}+{}={}".format(device_str,input_str,bound_item.binding)
