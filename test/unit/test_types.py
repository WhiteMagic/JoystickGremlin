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

import pytest

from gremlin import error, types


@pytest.mark.parametrize("enum_value", list(types.PropertyType))
def test_property_classmethod_converters(enum_value):
    """Test that converting PropertyType to string and back returns the original value."""
    str_value = types.PropertyType.to_string(enum_value)
    result_enum = types.PropertyType.to_enum(str_value)
    assert (
        result_enum == enum_value
    ), f"{enum_value=} is not {result_enum=} (via {str_value=})"


def test_property_type_invalid_string():
    """Test that an invalid string raises an error."""
    with pytest.raises(error.GremlinError):
        types.PropertyType.to_enum("invalid_string")
