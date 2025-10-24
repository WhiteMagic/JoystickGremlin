# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
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

"""
Domain layer for Joystick Gremlin.

This package contains domain models, events, and interfaces that form the
core business logic of the application. The domain layer is independent of
UI and infrastructure concerns.

Structure:
- events.py: Core Event class for input events
- interfaces.py: Action and profile interfaces (IActionData, ILibrary, etc.)
- ui_interfaces.py: UI component interfaces (IBindingModel)

Clean Code Principle: Separation of Concerns, Dependency Inversion (SOLID)

REFACTORED: Split from monolithic __init__.py into focused modules for better
maintainability and clearer separation of concerns.
"""

# Re-export everything for backward compatibility
from gremlin.domain.events import Event
from gremlin.domain.interfaces import (
    ISerializable,
    IProfileElement,
    IActionData,
    ILibrary,
    IContainer
)
from gremlin.domain.ui_interfaces import IBindingModel

__all__ = [
    # Events
    'Event',
    
    # Core interfaces
    'ISerializable',
    'IProfileElement',
    'IActionData',
    'ILibrary',
    'IContainer',
    
    # UI interfaces
    'IBindingModel',
]
