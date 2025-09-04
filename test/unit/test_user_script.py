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

from gremlin import profile, shared_state, types, user_script
from test.unit.conftest import get_fake_device_guid


@pytest.fixture(scope="module")
def script_path(test_root_dir: pathlib.Path) -> pathlib.Path:
    return test_root_dir / "data" / "testing_script.py"


@pytest.fixture(scope="module")
def script_for_test(script_path: pathlib.Path) -> user_script.Script:
    # Mode is retrieved from shared state when loading user plugins.
    shared_state.current_profile = p = profile.Profile()
    p.scripts.add_script(script_path)
    return p.scripts.scripts[0]


class TestScript:

    def test_script_loaded_and_configured(
        self, script_for_test: user_script.Script, script_path: pathlib.Path
    ):
        assert script_for_test.path == script_path
        assert script_for_test.name == "Instance 1"
        assert script_for_test.is_configured

    def test_script_has_expected_variables(self, script_for_test: user_script.Script):
        assert script_for_test.has_variable("A bool variable")
        assert script_for_test.has_variable("A float variable")
        assert script_for_test.has_variable("An integer variable")
        assert script_for_test.has_variable("A mode variable")
        assert script_for_test.has_variable("A string variable")
        assert script_for_test.has_variable("A selection variable")
        assert script_for_test.has_variable("A virtual axis input variable")
        assert script_for_test.has_variable("A virtual button input variable")
        assert script_for_test.has_variable("A virtual hat input variable")
        assert script_for_test.has_variable("A physical axis input variable")
        assert script_for_test.has_variable("A physical button input variable")
        assert script_for_test.has_variable("A physical hat input variable")

    def test_bool_variable(self, script_for_test: user_script.Script, subtests):
        """Test boolean variable properties."""
        var = script_for_test.get_variable("A bool variable")
        assert isinstance(var, user_script.BoolVariable)
        assert var.value is True
        assert var.is_optional is True
        assert var.description == "Example bool variable"

        with subtests.test("value change"):
            var.value = False
            assert var.value is False

    def test_float_variable(self, script_for_test: user_script.Script, subtests):
        """Test float variable properties."""
        var = script_for_test.get_variable("A float variable")
        assert isinstance(var, user_script.FloatVariable)
        assert var.value == 1.1
        assert var.is_optional is True
        assert var.min_value == -4.0
        assert var.max_value == 10.0
        assert var.description == "Example float variable"

        with subtests.test("value change within bounds"):
            var.value = 2.2
            assert var.value == 2.2
            assert var.is_valid()

        with subtests.test("value change out of bounds"):
            var.value = 11.1
            assert var.value == 10.0
            assert var.is_valid()

            var.value = -5.5
            assert var.value == -4.0
            assert var.is_valid()

    def test_integer_variable(self, script_for_test: user_script.Script, subtests):
        """Test integer variable properties."""
        var = script_for_test.get_variable("An integer variable")
        assert isinstance(var, user_script.IntegerVariable)
        assert var.value == 2
        assert var.is_optional is True
        assert var.min_value == 0
        assert var.max_value == 10
        assert var.description == "Example integer variable"

        with subtests.test("value change within bounds"):
            var.value = 3
            assert var.value == 3
            assert var.is_valid()

        with subtests.test("value change out of bounds"):
            var.value = 11
            assert var.value == 10
            assert var.is_valid()

            var.value = -1
            assert var.value == 0
            assert var.is_valid()

    def test_mode_variable(self, script_for_test: user_script.Script, subtests):
        """Test mode variable properties."""
        var = script_for_test.get_variable("A mode variable")
        assert isinstance(var, user_script.ModeVariable)
        assert var.is_optional is True
        assert var.description == "Example mode variable"
        initial_mode = var.value

        with subtests.test("value change invalid"):
            var.value = "mode1"
            assert var.value == "mode1"
            assert not var.is_valid()

        with subtests.test("value change valid"):
            var.value = initial_mode
            assert var.value == initial_mode
            assert var.is_valid()

    def test_string_variable(self, script_for_test: user_script.Script, subtests):
        """Test string variable properties."""
        var = script_for_test.get_variable("A string variable")
        assert isinstance(var, user_script.StringVariable)
        assert var.value == "example string var"
        assert var.is_optional is True
        assert var.description == "Example string variable"

        with subtests.test("value change invalid"):
            var.value = ""
            assert var.value == ""
            assert not var.is_valid()

        with subtests.test("value change valid"):
            var.value = "new string var val"
            assert var.value == "new string var val"
            assert var.is_valid()

    def test_selection_variable(self, script_for_test: user_script.Script, subtests):
        """Test selection variable properties."""
        var = script_for_test.get_variable("A selection variable")
        assert isinstance(var, user_script.SelectionVariable)
        assert var.options == ["selection1", "selection2", "selection3"]
        assert var.value == "selection2"  # default_index=1
        assert var.is_optional is True
        assert var.description == "Example selection variable"

        with subtests.test("value change invalid"):
            with pytest.raises(ValueError):
                var.value = "selection4"

        with subtests.test("value change valid"):
            var.value = "selection2"
            assert var.value == "selection2"
            assert var.is_valid()

    def test_virtual_input_variable(
        self, script_for_test: user_script.Script, subtests
    ):
        """Test virtual input variable properties."""
        with subtests.test("axis"):
            var = script_for_test.get_variable("A virtual axis input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickAxis]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for an axis"

        with subtests.test("button"):
            var = script_for_test.get_variable("A virtual button input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickButton]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for a button"

        with subtests.test("hat"):
            var = script_for_test.get_variable("A virtual hat input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickHat]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for a hat"

    def test_physical_input_variable(
        self, script_for_test: user_script.Script, subtests
    ):
        """Test physical input variable properties."""
        with subtests.test("axis"):
            var = script_for_test.get_variable("A physical axis input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickAxis]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for an axis"
            assert not var.is_valid()

        with subtests.test("value change"):
            var.value = (
                get_fake_device_guid(is_virtual=False),
                types.InputType.JoystickAxis,
                1,
            )
            assert var.is_valid()

        with subtests.test("button"):
            var = script_for_test.get_variable("A physical button input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickButton]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for a button"
            assert not var.is_valid()

        with subtests.test("hat"):
            var = script_for_test.get_variable("A physical hat input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickHat]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for a hat"
            assert not var.is_valid()
