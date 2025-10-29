# -*- coding: utf-8; -*-

"""Profile modules package.

This package contains focused modules extracted from gremlin.profile
for better organization and maintainability.

Modules:
- virtual_buttons: Virtual button abstractions (axis/hat as buttons)
- settings: Profile settings management
- mode_hierarchy: Mode hierarchy and management
- script_manager: Script and script manager classes
- library: Action library
- input_items: Input item classes
"""

# Re-export all classes for convenience
from gremlin.profile_modules.virtual_buttons import (
    AbstractVirtualButton,
    VirtualAxisButton,
    VirtualHatButton
)
from gremlin.profile_modules.settings import Settings
from gremlin.profile_modules.mode_hierarchy import ModeHierarchy
from gremlin.profile_modules.script_manager import Script, ScriptManager
from gremlin.profile_modules.library import Library
from gremlin.profile_modules.input_items import InputItem, InputItemBinding

__all__ = [
    # Virtual buttons
    'AbstractVirtualButton',
    'VirtualAxisButton',
    'VirtualHatButton',
    
    # Settings
    'Settings',
    
    # Mode hierarchy
    'ModeHierarchy',
    
    # Scripts
    'Script',
    'ScriptManager',
    
    # Library
    'Library',
    
    # Input items
    'InputItem',
    'InputItemBinding',
]

# Package documentation
# This package follows Single Responsibility Principle by separating
# different concerns of the profile system into focused modules.

