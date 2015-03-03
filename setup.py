# -*- coding: utf-8 -*-

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

# Builds the Joystick Gremlin application.
#
# Three files, libEGL.dll, Qt5Svg.dll, and _cpyHook.pyd are explicitly
# copied to the output directory since cx_freeze cannot deduce them
# being required.

import os
import sys
from cx_Freeze import setup, Executable


base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

python_path = os.path.dirname(sys.executable) + "\\"

# Shortcut creation directives for MSI installer
shortcut_table = [(
    "StartMenuShortcut",
    "StartMenuFolder",
    "Joystick Gremlin",
    "TARGETDIR",
    "[TARGETDIR]joystick_gremlin.exe",
    None,
    None,
    None,
    None,
    None,
    None,
    "TARGETDIR"
)]
msi_data = {"Shortcut": shortcut_table}

options = {
    "build_exe": {
        "compressed": False,
        "includes": [
            "atexit",
        ],
        "packages": [
            "action",
            "gremlin",
            "mako",
            "sdl2",
            "vjoy",
        ],
        "include_files": [
            "SDL2.dll",
            "vjoy/vJoyInterface.dll",
            "templates/",
            "gfx/",
            "about/",
            python_path + "\Lib\site-packages\PyQt5\libEGL.dll",
            python_path + "\Lib\site-packages\PyQt5\Qt5Svg.dll",
            python_path + "\Lib\site-packages\pyHook\_cpyHook.pyd",
        ],
        "path": sys.path + ["."],
    },
    "bdist_msi": {
        "upgrade_code": 1,
        "data": {
            "Shortcut": shortcut_table,
        }
    }
}

executables = [
    Executable(
        script="joystick_gremlin.py",
        base=base
    )
]

setup(
    name="Joystick Gremlin",
    version="1.0",
    description="Joystick Gremlin application",
    options=options,
    executables=executables
)