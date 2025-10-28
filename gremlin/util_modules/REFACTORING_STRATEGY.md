# Util.py Refactoring Strategy

## Current Status
- **File:** `gremlin/util.py`
- **Size:** 1,041 lines
- **Functions:** 45 total

## Planned Module Structure

```
gremlin/util_modules/
├── __init__.py              # Package initialization
├── xml_helpers.py           # 20 functions - XML parsing, properties
├── path_utils.py            # 2 functions - Path and resource handling
├── calibration.py           # 3 functions - Axis calibration, deadzone
├── file_operations.py       # 3 functions - File I/O, FileWatcher
└── misc.py                  # 17 functions - Miscellaneous utilities
```

## Function Categorization

### XML/Parsing Functions (20)
- `read_bool()`, `parse_bool()`, `safe_read()`, `safe_format()`
- `read_property()`, `read_properties()`, `_process_property()`
- `create_property_node()`, `create_subelement_node()`
- `read_subelement()`, `read_action_id()`, `read_action_ids()`
- `read_uuid()`, `determine_value_type()`
- And more XML parsing utilities

### Path/Resource Functions (2)
- `resource_path()`
- `userprofile_path()`

### Calibration Functions (3)
- `create_calibration_function()`
- `with_center_calibration()`
- `axis_calibration()`

### File I/O Functions (3)
- `FileWatcher` class
- File monitoring utilities

### Miscellaneous (17)
- `clamp()`, `rad2deg()`, `deg2rad()`
- `axis_value_to_direction()`
- `hat_tuple_to_direction()`, `hat_direction_to_tuple()`
- `format_name()`, `valid_mode_name()`
- `display_error()`, `get_guid()`
- And other utility functions

## Implementation Plan

1. **Phase 1:** Create focused modules
   - Extract XML functions → `xml_helpers.py`
   - Extract calibration → `calibration.py`
   - Extract path utils → `path_utils.py`
   - Extract file ops → `file_operations.py`
   - Remaining → `misc.py`

2. **Phase 2:** Update `gremlin/util.py`
   - Import all from submodules
   - Maintain backward compatibility
   - Update `__all__` exports

3. **Phase 3:** Update imports across codebase
   - Search for `from gremlin.util import`
   - Update to use specific modules
   - Run tests to verify

## Backward Compatibility

The original `gremlin/util.py` will become:

```python
# Backward compatibility - re-export everything
from gremlin.util_modules.xml_helpers import *
from gremlin.util_modules.calibration import *
from gremlin.util_modules.path_utils import *
from gremlin.util_modules.file_operations import *
from gremlin.util_modules.misc import *

__all__ = [...]  # All exported functions
```

## Benefits

- **Single Responsibility:** Each module has one clear purpose
- **Easier Testing:** Focused test files per module
- **Better Discovery:** Developers find functions faster
- **Reduced Coupling:** Clear separation of concerns
- **Maintainability:** Smaller files easier to understand

## Status: DOCUMENTED - Implementation pending

This strategy can be executed incrementally without breaking changes.
