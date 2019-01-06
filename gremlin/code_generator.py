# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
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

import logging
import os
import re
import sys

import gremlin.common
from mako.lookup import TemplateLookup
from mako.template import Template

import gremlin


class CodeGenerator:

    """Generates a Python script representing the entire configuration."""

    def __init__(self, config_profile):
        """Creates a new code generator for the given configuration.

        :param config_profile profile for which to generate code
        """
        self.code = ""
        self.generate_from_profile(config_profile)

    def generate_from_profile(self, config_profile):
        """Generates the code for the given configuration.

        :param config_profile the profile for which to generate the code
        """
        assert (isinstance(config_profile, gremlin.profile.Profile))

        # Create output by rendering it via the template system
        tpl_lookup = TemplateLookup(directories=["."])
        tpl = Template(
            filename="templates/gremlin_code.tpl",
            lookup=tpl_lookup
        )
        module_imports = self._process_module_imports(config_profile.imports)
        self.code = tpl.render(
            gremlin=gremlin,
            module_imports=module_imports,
        )

    def _process_module_imports(self, imports):
        # Create fully normalized set of system path names
        system_paths = [os.path.normcase(os.path.abspath(p)) for p in sys.path]

        # Split each import apart into path and file name and add fully
        # normalized paths to the list of system paths and maintain a name
        # of python modules to load
        module_list = []
        for fname in imports:
            path, module_fname = os.path.split(
                os.path.normcase(os.path.abspath(fname))
            )
            module = os.path.splitext(module_fname)[0]
            if module in module_list:
                gremlin.util.display_error(
                    "Duplicate module name \"{}\"".format(module)
                )
                logging.getLogger("system").exception(
                    "Attempted loading a duplicate module \"{}\", aborting.".format(module)
                )
            module_list.append(module)

            if path not in system_paths:
                system_paths.append(path)

        sys.path = system_paths
        return module_list

    def write_code(self, fname):
        """Writes the generated code to the given file.

        :param fname path to the file into which to write the code
        """
        code = re.sub("\r", "", self.code)
        with open(fname, "w") as out:
            out.write(code)
