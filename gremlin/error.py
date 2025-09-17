# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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


class GremlinError(Exception):

    """Generic exception raised for gremlin related errors.

    This class also functions as the base class for all other
    exceptions.
    """

    def __init__(self, value):
        logging.getLogger("system").exception(value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class ProfileError(GremlinError):

    """Exception raised when an error occurs with a profile related
    operation.
    """

    def __init__(self, value):
        super().__init__(value)


class KeyboardError(GremlinError):

    """Exception raised when an error occurs related to keyboard inputs."""

    def __init__(self, value):
        super().__init__(value)


class MouseError(GremlinError):

    """Exception raised when an error occurs related to mouse inputs."""

    def __init__(self, value):
        super().__init__(value)


class MissingImplementationError(GremlinError):

    """Exception raised when a method is not implemented."""

    def __init__(self, value):
        super().__init__(value)


class VJoyError(GremlinError):

    """Exception raised when an error occurs within the vJoy module."""

    def __init__(self, value):
        super().__init__(value)


class VJoyConcurrencyError(VJoyError):

    """Exception raised when vJoy is accessed from multiple threads."""

    def __init__(self, value):
        super().__init__(value)


class PluginError(GremlinError):

    """Exception raised when an error occurs withing a user plugin."""

    def __init__(self, value):
        super().__init__(value)