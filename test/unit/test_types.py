# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pytest

from gremlin import (
    error,
    types,
)


@pytest.mark.parametrize("enum_value", list(types.PropertyType))
def test_property_classmethod_converters(enum_value):
    """Test that converting PropertyType to string and back returns the original value."""
    str_value = types.PropertyType.to_string(enum_value)
    result_enum = types.PropertyType.to_enum(str_value)
    assert result_enum == enum_value, (
        f"{enum_value=} is not {result_enum=} (via {str_value=})"
    )


def test_property_type_invalid_string():
    """Test that an invalid string raises an error."""
    with pytest.raises(error.GremlinError):
        types.PropertyType.to_enum("invalid_string")
