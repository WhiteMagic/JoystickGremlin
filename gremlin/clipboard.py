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

from . import common


@common.SingletonDecorator
class Clipboard:

    """Responsible for storing and restoring action related data."""

    def __init__(self):
        """Creates a new instance, initializing empty clipboard."""
        self.item_data = None

    def copy(self, item_data):
        """ Saves item_data to clipboard """
        self.item_data = item_data

    def paste(self):
        """ Returns item_data saved in clipboard """
        return self.item_data

