# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import pathlib
import time
import uuid

import pytest

from gremlin import (
    error,
    profile,
    shared_state,
    types,
    user_script,
)
from test.unit.conftest import get_fake_device_guid


@pytest.fixture(scope="module")
def script_path() -> pathlib.Path:
    return pathlib.Path("example.py")


@pytest.fixture(scope="module")
def script_for_test(script_path: pathlib.Path) -> user_script.Script:
    # Mode is retrieved from shared state when loading user plugins.
    shared_state.current_profile = p = profile.Profile()
    p.scripts.add_script(script_path)
    return p.scripts.scripts[0]


class TestScript:
    def test_script_loaded_and_configured(
        self, script_for_test: user_script.Script, script_path: pathlib.Path
    ) -> None:
        assert script_for_test.path.match(script_path)
        assert script_for_test.name == "Instance 1"
        assert script_for_test.is_configured

    def test_script_has_expected_variables(
        self, script_for_test: user_script.Script
    ) -> None:
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

    def test_bool_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
        """Test boolean variable properties."""
        var = script_for_test.get_variable("A bool variable")
        assert isinstance(var, user_script.BoolVariable)
        assert var.value is True
        assert var.is_optional is True
        assert var.description == "Example bool variable"

        with subtests.test("value change"):
            var.value = False
            assert var.value is False

    @pytest.mark.parametrize("value", [True, False])
    def test_bool_variable_xml_transforms(
        self, script_for_test: user_script.Script, value: bool
    ) -> None:
        var = script_for_test.get_variable("A bool variable")
        var.value = value
        xml = var.to_xml()
        var_from_xml = user_script.BoolVariable("", "", False, False)
        var_from_xml.from_xml(xml)
        assert var_from_xml.value is value

    def test_float_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
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

    @pytest.mark.parametrize("value", [1.1, 2.2, 10.0, -4.0, 1])
    def test_float_variable_xml_transforms(
        self, script_for_test: user_script.Script, value: float
    ) -> None:
        var = script_for_test.get_variable("A float variable")
        var.value = value
        xml = var.to_xml()
        var_from_xml = user_script.FloatVariable("", "", 0.0, 0.0, 0.0, False)
        var_from_xml.from_xml(xml)
        assert var_from_xml.value == value

    def test_integer_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
        """Test integer variable properties."""
        var = script_for_test.get_variable("An integer variable")
        assert isinstance(var, user_script.IntegerVariable)
        assert var.value == 2
        assert var.is_optional is True
        assert var.min_value == -20
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

            var.value = -21
            assert var.value == -20  # Limit as defined in script.
            assert var.is_valid()

    @pytest.mark.parametrize("value", [-11, 0, 2, 3, 10])
    def test_integer_variable_xml_transforms(
        self, script_for_test: user_script.Script, value: int
    ) -> None:
        var = script_for_test.get_variable("An integer variable")
        var.value = value
        xml = var.to_xml()
        var_from_xml = user_script.IntegerVariable("", "", 0, 0, 0, False)
        var_from_xml.from_xml(xml)
        assert var_from_xml.value == value

    def test_mode_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
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

    def test_mode_variable_xml_transforms(
        self, script_for_test: user_script.Script
    ) -> None:
        var = script_for_test.get_variable("A mode variable")
        var.value = "Default"
        xml = var.to_xml()
        var_from_xml = user_script.ModeVariable("", "", False)
        var_from_xml.from_xml(xml)
        assert var_from_xml.value == "Default"

    def test_string_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
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

    @pytest.mark.parametrize(
        "value",
        [
            "example string var val",
            "new string var val",
            "long string value",
            "1",
        ],
    )
    def test_string_variable_xml_transforms(
        self, script_for_test: user_script.Script, value: str
    ) -> None:
        var = script_for_test.get_variable("A string variable")
        var.value = value
        xml = var.to_xml()
        var_from_xml = user_script.StringVariable("", "", "", False)
        var_from_xml.from_xml(xml)
        assert var_from_xml.value == value

    def test_selection_variable_with_invalid_default_raises(
        self, subtests: pytest.Subtests
    ) -> None:
        with subtests.test("default too large"), pytest.raises(error.PluginError):
            user_script.SelectionVariable(
                "Var With Default Index Too Large",
                "Selection variable with invalid default index",
                True,
                ["option1", "option2"],
                default_index=5,
            )
        with (
            subtests.test("negative default index not allowed"),
            pytest.raises(error.PluginError),
        ):
            user_script.SelectionVariable(
                "Var With Default Index Negative",
                "Selection variable with invalid default index",
                True,
                ["option1", "option2"],
                default_index=-1,
            )

    def test_selection_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
        """Test selection variable properties."""
        var = script_for_test.get_variable("A selection variable")
        assert isinstance(var, user_script.SelectionVariable)
        assert var.options == ["selection1", "selection2", "selection3"]
        assert var.value == "selection2"  # default_index=1
        assert var.is_optional is True
        assert var.description == "Example selection variable"

        with subtests.test("value change invalid"), pytest.raises(ValueError):
            var.value = "selection4"

        with subtests.test("value change valid"):
            var.value = "selection2"
            assert var.value == "selection2"
            assert var.is_valid()

        with subtests.test("handles reduced options"):
            var.value = "selection3"
            var_xml = var.to_xml()
            assert var_xml is not None
            # Make the selection in XML too large.
            for child in var_xml:
                if child.tag == "property" and child.get("name") == "index":
                    child.text = "4"
            var.from_xml(var_xml)
            # Should still be valid with existing value
            assert var.is_valid()
            assert var.value == "selection3"  # Previous valid value.

    @pytest.mark.parametrize("value", ["selection1", "selection2", "selection3"])
    def test_selection_variable_xml_transforms(
        self, script_for_test: user_script.Script, value: str
    ) -> None:
        var = script_for_test.get_variable("A selection variable")
        var.value = value
        xml = var.to_xml()
        var_from_xml = user_script.SelectionVariable(
            "", "", False, ["selection1", "selection2", "selection3"]
        )
        var_from_xml.from_xml(xml)
        assert var_from_xml.value == value

    def test_virtual_input_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
        """Test virtual input variable properties."""
        with subtests.test("axis"):
            var = script_for_test.get_variable("A virtual axis input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickAxis]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for an axis"

        with subtests.test("axis from xml"):
            var_from_xml = user_script.VirtualInputVariable(
                "", "", True, [types.InputType.JoystickAxis]
            )
            var_from_xml.from_xml(var.to_xml())

        with subtests.test("button"):
            var = script_for_test.get_variable("A virtual button input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickButton]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for a button"

        with subtests.test("button from xml"):
            var_from_xml = user_script.VirtualInputVariable(
                "", "", True, [types.InputType.JoystickButton]
            )
            var_from_xml.from_xml(var.to_xml())

        with subtests.test("hat"):
            var = script_for_test.get_variable("A virtual hat input variable")
            assert isinstance(var, user_script.VirtualInputVariable)
            assert var.valid_types == [types.InputType.JoystickHat]
            assert var.is_optional is True
            assert var.description == "Example virtual input variable for a hat"

        with subtests.test("hat from xml"):
            var_from_xml = user_script.VirtualInputVariable(
                "", "", True, [types.InputType.JoystickHat]
            )
            var_from_xml.from_xml(var.to_xml())

    def test_physical_input_variable(
        self, script_for_test: user_script.Script, subtests: pytest.Subtests
    ) -> None:
        """Test physical input variable properties."""
        with subtests.test("axis"):
            var = script_for_test.get_variable("A physical axis input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickAxis]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for an axis"
            assert not var.is_valid()

        with subtests.test("axis value change"):
            var.value = (
                get_fake_device_guid(is_virtual=False).uuid,
                types.InputType.JoystickAxis,
                1,
            )
            assert var.is_valid()

        with subtests.test("axis from xml"):
            var_from_xml = user_script.PhysicalInputVariable(
                "", "", True, [types.InputType.JoystickAxis]
            )
            var_from_xml.from_xml(var.to_xml())
            assert var_from_xml.is_valid()
            assert var_from_xml.value == var.value

        with subtests.test("button"):
            var = script_for_test.get_variable("A physical button input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickButton]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for a button"
            assert not var.is_valid()

        with subtests.test("button value change"):
            var.value = (
                get_fake_device_guid(is_virtual=False).uuid,
                types.InputType.JoystickButton,
                1,
            )
            assert var.is_valid()

        with subtests.test("button from xml"):
            var_from_xml = user_script.PhysicalInputVariable(
                "", "", True, [types.InputType.JoystickButton]
            )
            var_from_xml.from_xml(var.to_xml())
            assert var_from_xml.is_valid()
            assert var_from_xml.value == var.value

        with subtests.test("hat"):
            var = script_for_test.get_variable("A physical hat input variable")
            assert isinstance(var, user_script.PhysicalInputVariable)
            assert var.valid_types == [types.InputType.JoystickHat]
            assert var.is_optional is True
            assert var.description == "Example physical input variable for a hat"
            assert not var.is_valid()

        with subtests.test("hat value change"):
            var.value = (
                get_fake_device_guid(is_virtual=False).uuid,
                types.InputType.JoystickHat,
                1,
            )
            assert var.is_valid()

        with subtests.test("hat from xml"):
            var_from_xml = user_script.PhysicalInputVariable(
                "", "", True, [types.InputType.JoystickHat]
            )
            var_from_xml.from_xml(var.to_xml())
            assert var_from_xml.is_valid()
            assert var_from_xml.value == var.value

    def test_swap_uuid(self, script_for_test: user_script.Script) -> None:
        var = script_for_test.get_variable("A physical axis input variable")
        existing_device_uuid = get_fake_device_guid(is_virtual=False).uuid
        var.value = (
            existing_device_uuid,
            types.InputType.JoystickAxis,
            1,
        )
        assert var.is_valid()
        assert var.value[0] == existing_device_uuid
        new_device_uuid = uuid.uuid4()
        assert script_for_test.swap_uuid(existing_device_uuid, new_device_uuid)
        assert var.value[0] == new_device_uuid


class TestPeriodicRegistry:
    def test_periodic_decorator_injects_vjoy_plugin(self) -> None:
        received = []

        @user_script.periodic(0.01)
        def print_vjoy(vjoy: object) -> None:
            received.append(vjoy)

        user_script.periodic_registry.start()
        time.sleep(0.1)
        user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        assert all(v is user_script.VJoyPlugin.vjoy for v in received)
        assert 9 <= len(received) <= 11

    def test_periodic_callback_exception_is_logged_and_does_not_stop_other_callbacks(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        working_calls = []

        @user_script.periodic(0.01)
        def raises() -> None:
            raise ValueError("boom")

        @user_script.periodic(0.01)
        def works() -> None:
            working_calls.append(True)

        with caplog.at_level(logging.ERROR, logger="system"):
            user_script.periodic_registry.start()
            time.sleep(0.1)
            user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        assert len(working_calls) > 1
        assert any(
            r.name == "system"
            and r.getMessage() == "Periodic callback raised an exception: boom"
            for r in caplog.records
        )

    def test_periodic_reload_replaces_instead_of_duplicating(
        self, tmp_path: pathlib.Path
    ) -> None:
        script_file = tmp_path / "reload_example.py"
        script_file.write_text(
            "call_log = []\n"
            "\n"
            "from gremlin import user_script\n"
            "\n"
            "\n"
            "@user_script.periodic(0.01)\n"
            "def tick() -> None:\n"
            "    call_log.append(True)\n"
        )

        script = user_script.Script(script_file)
        script.reload()
        script.reload()

        user_script.periodic_registry.start()
        time.sleep(0.1)
        user_script.periodic_registry.stop()
        user_script.periodic_registry.clear()

        # 3 registrations (1 initial load + 2 reloads) firing independently
        # would land around 30 calls in this window; a single, replaced
        # registration lands around 10.
        assert 8 <= len(script.module.call_log) <= 12
