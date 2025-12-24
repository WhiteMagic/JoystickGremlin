# -*- coding: utf-8; -*-

# Copyright (C) 2025 Lionel Ott
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

import pathlib
import pytest

# Mock before any imports happen
from unittest.mock import Mock
import tempfile
import gremlin.util
gremlin.util.userprofile_path = Mock(return_value=tempfile.mkdtemp())

import joystick_gremlin
import gremlin.ui.backend
import gremlin.mode_manager

# Import and execute modules to ensure configuration is happy

@pytest.fixture(scope="session")
def qapp_cls() -> type[joystick_gremlin.JoystickGremlinApp]:
    return joystick_gremlin.JoystickGremlinApp


@pytest.fixture(scope="session")
def test_root_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent
