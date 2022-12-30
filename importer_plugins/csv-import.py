"""Populates bindings from CSV to current Profile

The CSV file must specify binding and assignment pairs in two 
separate columns. Optionally, a third column may be specified 
for binding descriptions. The first row in the CSV file
is assumed to contain column headers only; the remaining rows
each specify a single binding, assignment, and description set. 

In each row, any appropriate string may be used for the binding
and (optional) description entries. Each assignment entry must
specify an input type (either "axis" or "button"). Additionally,
a desired VJoy device may be specified. If the binding or 
assignment entries are missing from a row, that row is skipped.

The following are examples of valid assignment strings:

    "vjoy_1-x_axis"     # specifies the x-axis from VJoy 1
    "vjoy_1-ax1"        # specifies the 1st axis (X) from VJoy 1
    "vjoy_2-btn_2"      # specifies button 2 from VJoy 2
    "vjoy_2-2"          # specifies button 2 from VJoy 2
    "axis"              # specifies first unbound axis
    "button"            # specifies first unbound button

If a vjoy assignment is specified, "vjoy" must be present. The
axis/button assignment must be listed after the vjoy identifier
and separated from it with a dash ("-"). To specify an "axis" 
input type, the axis/button assignment string must begin with 
"ax" or consist of one of the following:

    "x_axis"
    "y_axis"
    "z_axis"
    "x_rot"
    "y_rot"
    "z_rot"
    "dial"
    "slider"

All other non-empty entries are assumed to be button 
assignments, although either "b", btn", or "button" is
suggested. It is suggested to use underscores ("_") instead
of spaces. All assignment strings are case-insensitive.

The binding, assignment, and (optional) description columns may
be in any order. Column identifiers must be provided as
positional arguments to the importer. Each column identifier
consists of either an integer index (where the first column 
index is equal to "1") or as a column header string. If any
column identifier cannot be found (e.g. the string entered
is not present in the header row or the column index 
exceeds the number of columns), an error is raised.

Positional arguments:

    binding_column_identifier
            Binding column index (first column = "1") or 
            case-sensitive header string; if header string is 
            specified, it must be present in the first CSV row
    
    assignment_column_identifier
            Assignment column index (first column = "1") or 
            case-sensitive header string; if header string is 
            specified, it must be present in the first CSV row

Optional arguments:

    -d, --description_column <column identifier>
            Description column index (first column = "1") or 
            case-sensitive header string; if header string is 
            specified, it must be present in the first CSV row
                        
"""

import re
import shlex
import argparse
import gremlin.error

import_filter = "Comma-separated list (*.csv)"
_delimiter = ","
_num_headers = 1
_binding_col = None
_assignment_col = None
_description_col = None

_axis_string_to_id = {
    "x_axis":    1,
    "y_axis":    2,
    "z_axis":    3,
    "x_rot":     4,
    "y_rot":     5,
    "z_rot":     6,
    "dial":      7,
    "slider":    8,
}

def main(file_lines, arg_string):
    """Process passed args, run importer with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Argument spec, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _binding_col, _assignment_col, _description_col
    
    try:
        args = _parse_args(shlex.split(arg_string))
    except gremlin.error.ImporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check importer description for details."
        raise gremlin.error.ImporterError(msg)
    
    header = file_lines[_num_headers-1].strip().split(_delimiter)
    _binding_col = _get_column_index(header, args.binding_column)
    _assignment_col = _get_column_index(header, args.assignment_column)
    _description_col = _get_column_index(header, args.description_column)
    
    return _import(file_lines[_num_headers:])

def _parse_args(args):
    """Parse arg string
    
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
    parser.add_argument("binding_column",
                        help="column number for list of bindings"
                        )
    parser.add_argument("assignment_column",
                        help="column number for list of vjoy assignments"
                        )
    parser.add_argument("-d", "--description_column",
                        help="column number for list of descriptions",
                        default=None
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ImporterError(msg)
    return valid

def _get_column_index(header, column_id):
    """Return column index from header string and identifier"""
    if column_id is None:
        return column_id

    try:
        return int(column_id) - 1
    except ValueError:
        pass

    try:
        return header.index(column_id)
    except ValueError:
        pass
    
    raise gremlin.error.ImporterError(("Could not find column '{}'!").format(column_id))

def _import(file_lines):
    """Parse file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    found = {}
    for line in file_lines:
        item = _delineated_line2vjoy_item(line)
        if item:
            input_type = next(iter(item))
            if input_type in found.keys():
                found[input_type].update(item[input_type])
            else:
                found.update(item)
    return found

def _delineated_line2vjoy_item(line):
    """Interpret line to get vjoy output
    
    :param delineated line string
    :return vjoy_item dict entry
    """
    
    global _binding_col, _assignment_col, _description_col
    
    # parse assignment, binding, and description from csv row
    row = line.split(_delimiter)
    try:
        binding = row[_binding_col].strip()
        assignment = row[_assignment_col].strip().lower()
        if _description_col is not None:
            description = row[_description_col].strip()
        else:
            _description_col = -1 # needed for error checking
            description = ""
    except IndexError:
        last_col = max([_binding_col, _assignment_col, _description_col])
        msg = (("Cannot access column {}! "
                "File only contains {} columns"
               ).format(last_col, len(row)))
        raise gremlin.error.ImporterError(msg)
            
    # return empty if invalid entry
    if not _is_valid_assignment(assignment) \
       or not _is_valid_binding(binding):
        return {}
    
    # get vjoy id
    vjoy_str = assignment.split("-")[0]
    if re.search(r"vjoy.*\d+",vjoy_str):
        vjoy_id = re.findall(r"\d+",vjoy_str)[0]
    else:
        vjoy_id = ""
        
    # get input_type
    csv_input = assignment.split("-")[-1]
    if (csv_input in _axis_string_to_id or
        re.findall(r"^ax",csv_input)):
        input_type = "axis"
    else:
        input_type = "button"
        
    # get input_id
    found_num = re.findall(r"\d+",csv_input)
    if csv_input in _axis_string_to_id:
        input_id = _axis_string_to_id[csv_input]
    elif found_num:
        input_id = found_num[0]
    else:
        input_id = ""
        
    # assemble item to return
    vjoy_item = {}
    vjoy_item[input_type] = {}
    vjoy_item[input_type][binding] = {
        "device_id": vjoy_id,
        "input_id": input_id,
        "description": description
    }
    return vjoy_item

def _is_valid_assignment(assignment):
    """Returns false if invalid assignment is found"""
    
    if not assignment:
        return False    # empty string -- ignore
    elif not assignment.split("-"):
        return False    # invalid entry -- ignore
    elif re.search("vjoy", assignment.split("-")[-1]) is not None:
        return False    # vjoy given without an input type
    else:
        return True
    
def _is_valid_binding(binding):
    """Returns false if invalid binding is found"""
    
    if not binding:
        return False    # empty string -- ignore
    else:
        return True