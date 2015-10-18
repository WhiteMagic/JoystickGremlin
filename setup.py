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

# Shortcut table for desktop icon
shortcut_table = [(
    "DesktopShortcut",      # Shortcut
    "DesktopFolder",        # Directory_
    "Joystick Gremlin",     # Name
    "TARGETDIR",             # Component_
    "[TARGETDIR]\joystick_gremlin.exe",  # Target
    None,                     # Arguments
    None,                     # Description
    None,                     # Hotkey
    None,                     # Icon
    None,                     # IconIndex
    None,                     # ShowCmd
    "TARGETDIR",             # WkDir
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
            ("doc/getting_started.html", "doc/getting_started.html"),
            python_path + "\Lib\site-packages\PyQt5\libEGL.dll",
            python_path + "\Lib\site-packages\PyQt5\Qt5Svg.dll",
            python_path + "\Lib\site-packages\pyHook\_cpyHook.pyd",
        ],
        "path": sys.path + ["."],
    },
    "bdist_msi": {
        "upgrade_code": "{9089B45A-754D-11E5-A79D-C03496548060}",
        "data": msi_data
    }
}

executables = [
    Executable(
        script="joystick_gremlin.py",
        icon="gfx/icon.ico",
        base=base
    )
]

setup(
    name="Joystick Gremlin",
    version="3.0",
    description="Joystick Gremlin application",
    options=options,
    executables=executables
)
