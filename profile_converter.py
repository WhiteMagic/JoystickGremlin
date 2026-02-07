#!/usr/bin/env python3
"""JoystickGremlin Profile Converter: v9 (R13) -> v14 (Release_14)

A standalone GUI tool that converts JoystickGremlin XML profiles from the
old format (version 9, used by R13 and earlier) to the new format
(version 14, used by Release_14).

Usage:
    python profile_converter.py

Requirements:
    Python 3.7+ with tkinter (included with standard Python on Windows).
    No external dependencies.
"""

import copy
import os
import sys
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Tkinter is optional -- GUI only works when available (standard on Windows)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    HAS_TK = True
except ImportError:
    HAS_TK = False


# ---------------------------------------------------------------------------
# UUID helper
# ---------------------------------------------------------------------------

def new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Data classes for intermediate representation
# ---------------------------------------------------------------------------

@dataclass
class ActionEntry:
    """An action stored in the v14 library."""
    id: str
    action_type: str
    properties: List[Tuple[str, str, str]]  # (type, name, value)
    children: Dict[str, List[str]]  # selector_name -> [action_ids]
    extra_elements: list = field(default_factory=list)  # raw (tag, attribs, children) for special cases


@dataclass
class InputEntry:
    """An input binding in the v14 inputs section."""
    device_id: str
    input_type: str  # "axis", "button", "hat", "key"
    input_id: str
    mode: str
    action_configs: list = field(default_factory=list)  # list of ActionConfigEntry


@dataclass
class ActionConfigEntry:
    root_action_id: str
    behavior: str  # "axis", "button", "hat"
    virtual_button: Optional[dict] = None  # type -> attribs


@dataclass
class DeviceInfo:
    device_id: str
    device_name: str


# ---------------------------------------------------------------------------
# v9 -> v14 Converter
# ---------------------------------------------------------------------------

class ProfileConverter:
    """Converts a JoystickGremlin v9 XML profile to v14 format."""

    # Map old curve type names to new ones
    CURVE_TYPE_MAP = {
        "cubic-spline": "CubicSpline",
        "cubic-bezier-spline": "CubicBezierSpline",
    }

    # Hat direction order for 4-way and 8-way
    HAT_DIRS_4 = ["North", "East", "South", "West"]
    HAT_DIRS_8 = [
        "North", "North East", "East", "South East",
        "South", "South West", "West", "North West",
    ]

    def __init__(self):
        self.library: List[ActionEntry] = []
        self.inputs: List[InputEntry] = []
        self.modes: Dict[str, Optional[str]] = {}  # mode_name -> parent_name
        self.devices: Dict[str, DeviceInfo] = {}  # guid -> DeviceInfo
        self.settings_node = None
        self.merge_axes: list = []
        self.plugins: list = []
        self.log_messages: List[str] = []
        self._action_map: Dict[str, ActionEntry] = {}

    def log(self, msg: str):
        self.log_messages.append(msg)

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def convert(self, input_path: str, output_path: str):
        """Convert a v9 profile file to v14 format and write it out."""
        tree = ET.parse(input_path)
        root = tree.getroot()

        version = root.get("version", "0")
        if version not in ("5", "6", "7", "8", "9"):
            self.log(
                f"WARNING: Profile version is {version}. This converter is "
                f"designed for version 9 (R13). Conversion may be incomplete."
            )

        self._parse_old_profile(root)
        new_root = self._build_new_profile()
        self._write_xml(new_root, output_path)
        self.log(f"Conversion complete. Output written to: {output_path}")

    # -------------------------------------------------------------------
    # Parsing the old (v9) profile
    # -------------------------------------------------------------------

    def _parse_old_profile(self, root: ET.Element):
        # Parse devices
        devices_node = root.find("devices")
        if devices_node is not None:
            for device_node in devices_node.findall("device"):
                self._parse_device(device_node)

        # Parse vjoy devices (just record them, usually no actions)
        vjoy_devices_node = root.find("vjoy-devices")
        if vjoy_devices_node is not None:
            for vd in vjoy_devices_node.findall("vjoy-device"):
                self._parse_device(vd, is_vjoy=True)

        # Parse merge-axis elements
        for ma in root.findall("merge-axis"):
            self.merge_axes.append(ma)

        # Parse settings
        self.settings_node = root.find("settings")

        # Parse plugins
        plugins_node = root.find("plugins")
        if plugins_node is not None:
            for plugin in plugins_node.findall("plugin"):
                self.plugins.append(plugin)

    def _parse_device(self, device_node: ET.Element, is_vjoy: bool = False):
        guid = device_node.get("device-guid", "")
        name = device_node.get("name", "Unknown")
        label = device_node.get("label", name)
        dev_type = device_node.get("type", "joystick")

        # Normalize GUID: strip braces if present
        clean_guid = guid.strip("{}")

        # Record device info
        if clean_guid:
            self.devices[clean_guid] = DeviceInfo(
                device_id=clean_guid,
                device_name=label if label else name,
            )

        # Parse modes
        for mode_node in device_node.findall("mode"):
            mode_name = mode_node.get("name", "Default")
            inherit = mode_node.get("inherit")

            # Record mode hierarchy
            if mode_name not in self.modes:
                self.modes[mode_name] = inherit

            # Parse input items
            for input_tag in ("axis", "button", "hat", "keyboard"):
                for input_node in mode_node.findall(input_tag):
                    self._parse_input_item(
                        input_node, input_tag, clean_guid, mode_name,
                        dev_type, is_vjoy
                    )

    def _parse_input_item(
        self, node: ET.Element, input_tag: str, device_guid: str,
        mode_name: str, dev_type: str, is_vjoy: bool
    ):
        input_id = node.get("id", "0")

        # For keyboard inputs, combine scan code and extended flag
        if input_tag == "keyboard":
            extended = node.get("extended", "False").lower() in ("true", "1")
            scan_code = int(input_id)
            input_id = str((1 << 8 | scan_code) if extended else scan_code)
            v14_input_type = "key"
        else:
            v14_input_type = input_tag  # axis, button, hat

        # Parse containers
        containers = node.findall("container")
        if not containers:
            return

        for container_node in containers:
            self._parse_container(
                container_node, device_guid, v14_input_type,
                input_id, mode_name, input_tag
            )

    def _parse_container(
        self, container_node: ET.Element, device_guid: str,
        input_type: str, input_id: str, mode_name: str,
        original_input_tag: str
    ):
        container_type = container_node.get("type", "basic")

        # Parse action sets
        action_sets = container_node.findall("action-set")

        # Parse virtual button (for determining behavior)
        vb_node = container_node.find("virtual-button")
        virtual_button = None
        behavior = input_type

        if vb_node is not None:
            if original_input_tag == "axis":
                virtual_button = {
                    "type": "axis",
                    "lower-limit": vb_node.get("lower-limit", "-1.0"),
                    "upper-limit": vb_node.get("upper-limit", "1.0"),
                    "direction": vb_node.get("direction", "anywhere"),
                }
                # Axis with virtual button behaves as a button
                behavior = "button"
            elif original_input_tag == "hat":
                dirs = []
                for d in ["center", "north", "north-east", "east",
                           "south-east", "south", "south-west",
                           "west", "north-west"]:
                    if vb_node.get(d, "0") == "1":
                        dirs.append(d)
                if dirs:
                    virtual_button = {"type": "hat", "directions": dirs}
                    behavior = "button"

        # Parse activation condition
        ac_node = container_node.find("activation-condition")
        condition_action_id = None
        if ac_node is not None:
            condition_action_id = self._convert_activation_condition(ac_node)

        # Convert based on container type
        if container_type == "basic":
            root_action_id = self._convert_basic_container(
                action_sets, condition_action_id
            )
        elif container_type == "tempo":
            root_action_id = self._convert_tempo_container(
                container_node, action_sets, condition_action_id
            )
        elif container_type == "chain":
            root_action_id = self._convert_chain_container(
                container_node, action_sets, condition_action_id
            )
        elif container_type == "double_tap":
            root_action_id = self._convert_double_tap_container(
                container_node, action_sets, condition_action_id
            )
        elif container_type == "hat_buttons":
            root_action_id = self._convert_hat_buttons_container(
                container_node, action_sets, condition_action_id
            )
        elif container_type == "smart_toggle":
            root_action_id = self._convert_smart_toggle_container(
                container_node, action_sets, condition_action_id
            )
        else:
            self.log(f"WARNING: Unknown container type '{container_type}', skipping")
            return

        if root_action_id is None:
            return

        # Create input entry
        ac = ActionConfigEntry(
            root_action_id=root_action_id,
            behavior=behavior,
            virtual_button=virtual_button,
        )

        input_entry = InputEntry(
            device_id=device_guid,
            input_type=input_type,
            input_id=input_id,
            mode=mode_name,
        )
        input_entry.action_configs.append(ac)
        self.inputs.append(input_entry)

    # -------------------------------------------------------------------
    # Action conversion helpers
    # -------------------------------------------------------------------

    def _add_action(self, action: ActionEntry) -> str:
        self.library.append(action)
        self._action_map[action.id] = action
        return action.id

    def _make_root_action(self, child_ids: List[str]) -> str:
        """Create a 'root' action that references child actions."""
        action = ActionEntry(
            id=new_uuid(),
            action_type="root",
            properties=[
                ("string", "action-label", "Root"),
                ("activation-mode", "activation-mode", "disallowed"),
            ],
            children={"actions": child_ids},
        )
        return self._add_action(action)

    def _convert_action_set_actions(
        self, action_set: ET.Element
    ) -> List[str]:
        """Convert all actions within an <action-set> to v14 library actions."""
        action_ids = []
        for child in action_set:
            aid = self._convert_action(child)
            if aid:
                action_ids.append(aid)
        return action_ids

    def _convert_action(self, node: ET.Element) -> Optional[str]:
        """Convert a single v9 action element to a v14 library action."""
        tag = node.tag

        converters = {
            "remap": self._convert_remap,
            "response-curve": self._convert_response_curve,
            "macro": self._convert_macro,
            "map-to-keyboard": self._convert_map_to_keyboard,
            "map-to-mouse": self._convert_map_to_mouse,
            "switch-mode": self._convert_switch_mode,
            "cycle-modes": self._convert_cycle_modes,
            "previous-mode": self._convert_previous_mode,
            "temporary-mode-switch": self._convert_temporary_mode_switch,
            "split-axis": self._convert_split_axis,
            "play-sound": self._convert_play_sound,
            "description": self._convert_description,
            "text-to-speech": self._convert_text_to_speech,
            "pause": self._convert_pause_action,
            "resume": self._convert_resume_action,
            "toggle-pause": self._convert_toggle_pause_action,
            "noop": self._convert_noop,
        }

        converter = converters.get(tag)
        if converter:
            return converter(node)
        else:
            self.log(f"WARNING: Unknown action type '{tag}', skipping")
            return None

    # -------------------------------------------------------------------
    # Individual action converters
    # -------------------------------------------------------------------

    def _convert_remap(self, node: ET.Element) -> str:
        vjoy_id = node.get("vjoy", "1")
        axis = node.get("axis")
        button = node.get("button")
        hat = node.get("hat")
        axis_type = node.get("axis-type", "absolute")
        axis_scaling = node.get("axis-scaling", "1.0")

        props = [
            ("string", "action-label", "Map to vJoy"),
            ("activation-mode", "activation-mode", "both"),
            ("int", "vjoy-device-id", vjoy_id),
        ]

        if axis is not None:
            props.extend([
                ("int", "vjoy-input-id", axis),
                ("input_type", "vjoy-input-type", "axis"),
                ("axis_mode", "axis-mode", axis_type),
                ("float", "axis-scaling", axis_scaling),
            ])
        elif button is not None:
            props.extend([
                ("int", "vjoy-input-id", button),
                ("input_type", "vjoy-input-type", "button"),
                ("bool", "button-inverted", "False"),
            ])
        elif hat is not None:
            props.extend([
                ("int", "vjoy-input-id", hat),
                ("input_type", "vjoy-input-type", "hat"),
            ])

        action = ActionEntry(
            id=new_uuid(),
            action_type="map-to-vjoy",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_response_curve(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Response Curve"),
            ("activation-mode", "activation-mode", "disallowed"),
        ]

        extra = []

        # Deadzone
        dz_node = node.find("deadzone")
        if dz_node is not None:
            dz_props = [
                ("float", "low", dz_node.get("low", "-1.0")),
                ("float", "center-low", dz_node.get("center-low", "0.0")),
                ("float", "center-high", dz_node.get("center-high", "0.0")),
                ("float", "high", dz_node.get("high", "1.0")),
            ]
            extra.append(("deadzone", dz_props))

        # Mapping / control points
        mapping_node = node.find("mapping")
        if mapping_node is not None:
            curve_type = mapping_node.get("type", "cubic-spline")
            v14_curve = self.CURVE_TYPE_MAP.get(curve_type, "CubicSpline")
            props.append(("string", "curve-type", v14_curve))

            cp_props = []
            for cp in mapping_node.findall("control-point"):
                x = cp.get("x", "0.0")
                y = cp.get("y", "0.0")
                cp_props.append(("point2d", "point", f"({x}, {y})"))
            extra.append(("control-points", cp_props))
        else:
            # Default linear curve
            props.append(("string", "curve-type", "PiecewiseLinear"))
            extra.append(("control-points", [
                ("point2d", "point", "(-1.0, -1.0)"),
                ("point2d", "point", "(1.0, 1.0)"),
            ]))

        action = ActionEntry(
            id=new_uuid(),
            action_type="response-curve",
            properties=props,
            children={},
            extra_elements=extra,
        )
        return self._add_action(action)

    def _convert_macro(self, node: ET.Element) -> str:
        props_node = node.find("properties")
        is_exclusive = False
        repeat_mode = "Single"
        repeat_count = "1"
        repeat_delay = "0.1"

        if props_node is not None:
            if props_node.find("exclusive") is not None:
                is_exclusive = True
            repeat_node = props_node.find("repeat")
            if repeat_node is not None:
                rtype = repeat_node.get("type", "count")
                repeat_mode = rtype.capitalize()
                if repeat_mode not in ("Count", "Toggle", "Hold"):
                    repeat_mode = "Single"
                count_node = repeat_node.find("count")
                if count_node is not None:
                    repeat_count = count_node.text or "1"
                delay_node = repeat_node.find("delay")
                if delay_node is not None:
                    repeat_delay = delay_node.text or "0.1"

        props = [
            ("string", "action-label", "Macro"),
            ("activation-mode", "activation-mode", "press"),
            ("bool", "is-exclusive", str(is_exclusive)),
            ("string", "repeat-mode", repeat_mode),
            ("int", "repeat-count", repeat_count),
            ("float", "repeat-delay", repeat_delay),
        ]

        # Convert macro actions (inline, not library-referenced)
        macro_actions = []
        actions_node = node.find("actions")
        if actions_node is not None:
            for entry in actions_node:
                ma = self._convert_macro_entry(entry)
                if ma:
                    macro_actions.append(ma)

        action = ActionEntry(
            id=new_uuid(),
            action_type="macro",
            properties=props,
            children={},
            extra_elements=[("macro-actions", macro_actions)],
        )
        return self._add_action(action)

    def _convert_macro_entry(self, node: ET.Element) -> Optional[dict]:
        """Convert a single macro step from v9 to v14 format."""
        tag = node.tag

        if tag == "key":
            return {
                "type": "key",
                "properties": [
                    ("int", "scan-code", node.get("scan-code", "0")),
                    ("bool", "is-extended", self._bool_str(node.get("extended", "false"))),
                    ("bool", "is-pressed", self._bool_str(node.get("press", "true"))),
                ],
            }
        elif tag == "pause":
            return {
                "type": "pause",
                "properties": [
                    ("float", "duration", node.get("duration", "0.05")),
                ],
            }
        elif tag == "joystick":
            return {
                "type": "joystick",
                "properties": [
                    ("uuid", "device-guid", self._clean_guid(node.get("device-guid", ""))),
                    ("input_type", "input-type", node.get("input-type", "button")),
                    ("int", "input-id", node.get("input-id", "1")),
                    ("bool", "value", self._bool_str(node.get("value", "true"))),
                ],
            }
        elif tag == "mouse":
            return {
                "type": "mouse-button",
                "properties": [
                    ("string", "button", node.get("button", "Left")),
                    ("bool", "is-pressed", self._bool_str(node.get("press", "true"))),
                ],
            }
        elif tag == "mouse-motion":
            return {
                "type": "mouse-motion",
                "properties": [
                    ("int", "dx", node.get("dx", "0")),
                    ("int", "dy", node.get("dy", "0")),
                ],
            }
        elif tag == "vjoy":
            return {
                "type": "vjoy",
                "properties": [
                    ("int", "vjoy-id", node.get("vjoy-id", "1")),
                    ("input_type", "input-type", node.get("input-type", "button")),
                    ("int", "input-id", node.get("input-id", "1")),
                    ("bool", "value", self._bool_str(node.get("value", "true"))),
                ],
            }
        else:
            self.log(f"WARNING: Unknown macro action type '{tag}', skipping")
            return None

    def _convert_map_to_keyboard(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Map to Keyboard"),
            ("activation-mode", "activation-mode", "both"),
        ]

        keys = []
        for key_node in node.findall("key"):
            keys.append({
                "scan-code": key_node.get("scan-code", "0"),
                "is-extended": self._bool_str(key_node.get("extended", "False")),
            })

        action = ActionEntry(
            id=new_uuid(),
            action_type="map-to-keyboard",
            properties=props,
            children={},
            extra_elements=[("keyboard-keys", keys)],
        )
        return self._add_action(action)

    def _convert_map_to_mouse(self, node: ET.Element) -> str:
        motion_input = node.get("motion-input", "False")
        is_motion = motion_input.lower() in ("true", "1")

        props = [
            ("string", "action-label", "Map to Mouse"),
            ("activation-mode", "activation-mode", "both"),
        ]

        if is_motion:
            props.extend([
                ("string", "mode", "motion"),
                ("int", "direction", node.get("direction", "0")),
                ("int", "min-speed", node.get("min-speed", "5")),
                ("int", "max-speed", node.get("max-speed", "15")),
                ("float", "time-to-max-speed",
                 node.get("time-to-max-speed", "1.0")),
            ])
        else:
            button_id = node.get("button-id", "1")
            props.extend([
                ("string", "mode", "button"),
                ("int", "button", button_id),
            ])

        action = ActionEntry(
            id=new_uuid(),
            action_type="map-to-mouse",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_switch_mode(self, node: ET.Element) -> str:
        mode_name = node.get("name", "Default")
        props = [
            ("string", "action-label", "Change Mode"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "change-type", "Switch"),
        ]
        extra = [("target-modes", [mode_name])]

        action = ActionEntry(
            id=new_uuid(),
            action_type="change-mode",
            properties=props,
            children={},
            extra_elements=extra,
        )
        return self._add_action(action)

    def _convert_cycle_modes(self, node: ET.Element) -> str:
        modes = [m.get("name", "") for m in node.findall("mode") if m.get("name")]
        props = [
            ("string", "action-label", "Change Mode"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "change-type", "Cycle"),
        ]
        extra = [("target-modes", modes)]

        action = ActionEntry(
            id=new_uuid(),
            action_type="change-mode",
            properties=props,
            children={},
            extra_elements=extra,
        )
        return self._add_action(action)

    def _convert_previous_mode(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Change Mode"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "change-type", "Previous"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="change-mode",
            properties=props,
            children={},
            extra_elements=[("target-modes", [])],
        )
        return self._add_action(action)

    def _convert_temporary_mode_switch(self, node: ET.Element) -> str:
        mode_name = node.get("name", "Default")
        props = [
            ("string", "action-label", "Change Mode"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "change-type", "Temporary"),
        ]
        extra = [("target-modes", [mode_name])]

        action = ActionEntry(
            id=new_uuid(),
            action_type="change-mode",
            properties=props,
            children={},
            extra_elements=extra,
        )
        return self._add_action(action)

    def _convert_split_axis(self, node: ET.Element) -> str:
        center = node.get("center-point", "0.0")
        low_vjoy = node.get("device-low-vjoy-id", "1")
        low_axis = node.get("device-low-axis", "1")
        high_vjoy = node.get("device-high-vjoy-id", "1")
        high_axis = node.get("device-high-axis", "1")

        # Create remap actions for lower and upper
        lower_remap = ActionEntry(
            id=new_uuid(),
            action_type="map-to-vjoy",
            properties=[
                ("string", "action-label", "Map to vJoy"),
                ("activation-mode", "activation-mode", "both"),
                ("int", "vjoy-device-id", low_vjoy),
                ("int", "vjoy-input-id", low_axis),
                ("input_type", "vjoy-input-type", "axis"),
                ("axis_mode", "axis-mode", "absolute"),
                ("float", "axis-scaling", "1.0"),
            ],
            children={},
        )
        self._add_action(lower_remap)

        upper_remap = ActionEntry(
            id=new_uuid(),
            action_type="map-to-vjoy",
            properties=[
                ("string", "action-label", "Map to vJoy"),
                ("activation-mode", "activation-mode", "both"),
                ("int", "vjoy-device-id", high_vjoy),
                ("int", "vjoy-input-id", high_axis),
                ("input_type", "vjoy-input-type", "axis"),
                ("axis_mode", "axis-mode", "absolute"),
                ("float", "axis-scaling", "1.0"),
            ],
            children={},
        )
        self._add_action(upper_remap)

        # Create lower and upper root actions
        lower_root_id = self._make_root_action([lower_remap.id])
        upper_root_id = self._make_root_action([upper_remap.id])

        props = [
            ("string", "action-label", "Split Axis"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("float", "split-value", center),
        ]

        action = ActionEntry(
            id=new_uuid(),
            action_type="split-axis",
            properties=props,
            children={
                "lower-actions": [lower_root_id],
                "upper-actions": [upper_root_id],
            },
        )
        return self._add_action(action)

    def _convert_play_sound(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Play Sound"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "filename", node.get("file", "")),
            ("int", "volume", node.get("volume", "50")),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="play-sound",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_description(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Description"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("string", "description", node.get("description", "")),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="description",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_text_to_speech(self, node: ET.Element) -> str:
        # No direct equivalent in v14 - convert to description with note
        text = node.get("text", "")
        self.log(
            f"NOTE: text-to-speech action converted to description "
            f"(not supported in v14): '{text}'"
        )
        props = [
            ("string", "action-label", "Description"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("string", "description",
             f"[Converted from text-to-speech] {text}"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="description",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_pause_action(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Pause Resume"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "operation", "Pause"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="pause-resume",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_resume_action(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Pause Resume"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "operation", "Resume"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="pause-resume",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_toggle_pause_action(self, node: ET.Element) -> str:
        props = [
            ("string", "action-label", "Pause Resume"),
            ("activation-mode", "activation-mode", "press"),
            ("string", "operation", "Toggle"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="pause-resume",
            properties=props,
            children={},
        )
        return self._add_action(action)

    def _convert_noop(self, node: ET.Element) -> str:
        # Convert to description since v14 has no noop
        self.log("NOTE: noop action converted to description (not supported in v14)")
        props = [
            ("string", "action-label", "Description"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("string", "description", "[Converted from noop]"),
        ]
        action = ActionEntry(
            id=new_uuid(),
            action_type="description",
            properties=props,
            children={},
        )
        return self._add_action(action)

    # -------------------------------------------------------------------
    # Container converters
    # -------------------------------------------------------------------

    def _convert_basic_container(
        self, action_sets: list, condition_action_id: Optional[str]
    ) -> Optional[str]:
        if not action_sets:
            return None

        # Basic container has one action set with possibly multiple actions
        child_ids = []
        for action_set in action_sets:
            child_ids.extend(self._convert_action_set_actions(action_set))

        if not child_ids:
            return None

        # Wrap with condition if needed
        if condition_action_id:
            child_ids = self._wrap_with_condition(
                child_ids, condition_action_id
            )

        return self._make_root_action(child_ids)

    def _convert_tempo_container(
        self, container_node: ET.Element, action_sets: list,
        condition_action_id: Optional[str]
    ) -> Optional[str]:
        delay = container_node.get("delay", "0.5")
        activate_on = container_node.get("activate-on", "release")

        short_ids = []
        long_ids = []

        if len(action_sets) >= 1:
            short_ids = self._convert_action_set_actions(action_sets[0])
        if len(action_sets) >= 2:
            long_ids = self._convert_action_set_actions(action_sets[1])

        # Create root actions for short and long branches
        short_root = self._make_root_action(short_ids) if short_ids else self._make_root_action([])
        long_root = self._make_root_action(long_ids) if long_ids else self._make_root_action([])

        props = [
            ("string", "action-label", "Tempo"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("float", "threshold", delay),
            ("string", "activate-on", activate_on),
        ]

        tempo_action = ActionEntry(
            id=new_uuid(),
            action_type="tempo",
            properties=props,
            children={
                "short-actions": [short_root],
                "long-actions": [long_root],
            },
        )
        tempo_id = self._add_action(tempo_action)

        child_ids = [tempo_id]
        if condition_action_id:
            child_ids = self._wrap_with_condition(child_ids, condition_action_id)

        return self._make_root_action(child_ids)

    def _convert_chain_container(
        self, container_node: ET.Element, action_sets: list,
        condition_action_id: Optional[str]
    ) -> Optional[str]:
        timeout = container_node.get("timeout", "0.0")

        props = [
            ("string", "action-label", "Chain"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("float", "timeout", timeout),
        ]

        children = {}
        for i, action_set in enumerate(action_sets):
            step_ids = self._convert_action_set_actions(action_set)
            step_root = self._make_root_action(step_ids)
            children[f"chain-{i}"] = [step_root]

        chain_action = ActionEntry(
            id=new_uuid(),
            action_type="chain",
            properties=props,
            children=children,
        )
        chain_id = self._add_action(chain_action)

        child_ids = [chain_id]
        if condition_action_id:
            child_ids = self._wrap_with_condition(child_ids, condition_action_id)

        return self._make_root_action(child_ids)

    def _convert_double_tap_container(
        self, container_node: ET.Element, action_sets: list,
        condition_action_id: Optional[str]
    ) -> Optional[str]:
        delay = container_node.get("delay", "0.5")
        activate_on = container_node.get("activate-on", "combined")

        # Map old activate-on values
        if activate_on == "combined":
            activate_on = "combined"
        elif activate_on == "exclusive":
            activate_on = "exclusive"

        single_ids = []
        double_ids = []

        if len(action_sets) >= 1:
            single_ids = self._convert_action_set_actions(action_sets[0])
        if len(action_sets) >= 2:
            double_ids = self._convert_action_set_actions(action_sets[1])

        single_root = self._make_root_action(single_ids)
        double_root = self._make_root_action(double_ids)

        props = [
            ("string", "action-label", "Double Tap"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("float", "threshold", delay),
            ("string", "activate-on", activate_on),
        ]

        dt_action = ActionEntry(
            id=new_uuid(),
            action_type="double-tap",
            properties=props,
            children={
                "single-actions": [single_root],
                "double-actions": [double_root],
            },
        )
        dt_id = self._add_action(dt_action)

        child_ids = [dt_id]
        if condition_action_id:
            child_ids = self._wrap_with_condition(child_ids, condition_action_id)

        return self._make_root_action(child_ids)

    def _convert_hat_buttons_container(
        self, container_node: ET.Element, action_sets: list,
        condition_action_id: Optional[str]
    ) -> Optional[str]:
        button_count = int(container_node.get("button-count", "4"))
        dirs = self.HAT_DIRS_4 if button_count == 4 else self.HAT_DIRS_8

        props = [
            ("string", "action-label", "Hat as Buttons"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("int", "button-count", str(button_count)),
        ]

        children = {}
        for i, direction in enumerate(dirs):
            if i < len(action_sets):
                step_ids = self._convert_action_set_actions(action_sets[i])
            else:
                step_ids = []
            children[direction] = step_ids

        hb_action = ActionEntry(
            id=new_uuid(),
            action_type="hat-buttons",
            properties=props,
            children=children,
        )
        hb_id = self._add_action(hb_action)

        child_ids = [hb_id]
        if condition_action_id:
            child_ids = self._wrap_with_condition(child_ids, condition_action_id)

        return self._make_root_action(child_ids)

    def _convert_smart_toggle_container(
        self, container_node: ET.Element, action_sets: list,
        condition_action_id: Optional[str]
    ) -> Optional[str]:
        delay = container_node.get("delay", "0.5")

        all_ids = []
        for action_set in action_sets:
            all_ids.extend(self._convert_action_set_actions(action_set))

        props = [
            ("string", "action-label", "Smart Toggle"),
            ("activation-mode", "activation-mode", "disallowed"),
            ("float", "delay", delay),
        ]

        st_action = ActionEntry(
            id=new_uuid(),
            action_type="smart-toggle",
            properties=props,
            children={"actions": all_ids},
        )
        st_id = self._add_action(st_action)

        child_ids = [st_id]
        if condition_action_id:
            child_ids = self._wrap_with_condition(child_ids, condition_action_id)

        return self._make_root_action(child_ids)

    # -------------------------------------------------------------------
    # Activation condition converter
    # -------------------------------------------------------------------

    def _convert_activation_condition(self, ac_node: ET.Element) -> str:
        rule = ac_node.get("rule", "all")

        props = [
            ("string", "action-label", "Condition"),
            ("activation-mode", "activation-mode", "both"),
            ("string", "logical-operator", rule),
        ]

        conditions = []
        for cond in ac_node.findall("condition"):
            conditions.append(self._convert_condition_entry(cond))

        action = ActionEntry(
            id=new_uuid(),
            action_type="condition",
            properties=props,
            children={
                "true-actions": [],  # Will be filled by caller
                "false-actions": [],
            },
            extra_elements=[("conditions", conditions)],
        )
        return self._add_action(action)

    def _convert_condition_entry(self, cond: ET.Element) -> dict:
        """Convert a single condition element to v14 format."""
        cond_type = cond.get("condition-type", "keyboard")
        input_type = cond.get("input", "keyboard")
        comparison = cond.get("comparison", "pressed")

        result = {
            "condition-type": cond_type,
            "input": input_type,
            "comparison": comparison,
        }

        if cond_type == "keyboard":
            result["scan-code"] = cond.get("scan-code", "0")
            result["extended"] = cond.get("extended", "false")
        elif cond_type in ("joystick", "vjoy"):
            result["device-guid"] = self._clean_guid(
                cond.get("device-guid", cond.get("vjoy-id", ""))
            )
            if cond_type == "vjoy":
                result["vjoy-id"] = cond.get("vjoy-id", "1")
            result["id"] = cond.get("id", "1")
            if input_type == "axis":
                result["range-low"] = cond.get("range-low", "-1.0")
                result["range-high"] = cond.get("range-high", "1.0")

        return result

    def _wrap_with_condition(
        self, action_ids: List[str], condition_action_id: str
    ) -> List[str]:
        """Wrap actions inside a condition action's true branch."""
        cond_action = self._action_map.get(condition_action_id)
        if cond_action:
            # Create a root for the true actions
            true_root = self._make_root_action(action_ids)
            cond_action.children["true-actions"] = [true_root]
            return [condition_action_id]
        return action_ids

    # -------------------------------------------------------------------
    # Build new v14 profile XML
    # -------------------------------------------------------------------

    def _build_new_profile(self) -> ET.Element:
        root = ET.Element("profile")
        root.set("version", "14")

        # 1. Inputs
        inputs_elem = ET.SubElement(root, "inputs")
        for inp in self.inputs:
            self._build_input_element(inputs_elem, inp)

        # 2. Settings
        self._build_settings(root)

        # 3. Logical device (empty for converted profiles)
        ET.SubElement(root, "logical-device")

        # 4. Library
        library_elem = ET.SubElement(root, "library")
        for action in self.library:
            self._build_action_element(library_elem, action)

        # 5. Modes
        modes_elem = ET.SubElement(root, "modes")
        if not self.modes:
            mode_elem = ET.SubElement(modes_elem, "mode")
            mode_elem.text = "Default"
        else:
            for mode_name, parent in self.modes.items():
                mode_elem = ET.SubElement(modes_elem, "mode")
                mode_elem.text = mode_name
                if parent:
                    mode_elem.set("parent", parent)

        # 6. Scripts
        scripts_elem = ET.SubElement(root, "scripts")
        self._build_scripts(scripts_elem)

        # 7. Devices
        devices_elem = ET.SubElement(root, "devices")
        for guid, info in self.devices.items():
            dev = ET.SubElement(devices_elem, "device")
            did = ET.SubElement(dev, "device-id")
            did.text = info.device_id
            dn = ET.SubElement(dev, "device-name")
            dn.text = info.device_name

        # 8. Convert merge axes to actions/inputs
        self._convert_merge_axes(inputs_elem, library_elem)

        return root

    def _build_input_element(self, parent: ET.Element, inp: InputEntry):
        input_elem = ET.SubElement(parent, "input")

        did = ET.SubElement(input_elem, "device-id")
        did.text = inp.device_id

        it = ET.SubElement(input_elem, "input-type")
        it.text = inp.input_type

        iid = ET.SubElement(input_elem, "input-id")
        iid.text = str(inp.input_id)

        mode = ET.SubElement(input_elem, "mode")
        mode.text = inp.mode

        for ac in inp.action_configs:
            ac_elem = ET.SubElement(input_elem, "action-configuration")

            ra = ET.SubElement(ac_elem, "root-action")
            ra.text = ac.root_action_id

            beh = ET.SubElement(ac_elem, "behavior")
            beh.text = ac.behavior

            if ac.virtual_button:
                vb_elem = ET.SubElement(ac_elem, "virtual-button")
                if ac.virtual_button["type"] == "axis":
                    ll = ET.SubElement(vb_elem, "lower-limit")
                    ll.text = ac.virtual_button["lower-limit"]
                    ul = ET.SubElement(vb_elem, "upper-limit")
                    ul.text = ac.virtual_button["upper-limit"]
                    abd = ET.SubElement(vb_elem, "axis-button-direction")
                    abd.text = ac.virtual_button["direction"]
                elif ac.virtual_button["type"] == "hat":
                    for d in ac.virtual_button["directions"]:
                        hd = ET.SubElement(vb_elem, "hat-direction")
                        hd.text = d

    def _build_action_element(self, parent: ET.Element, action: ActionEntry):
        action_elem = ET.SubElement(parent, "action")
        action_elem.set("id", action.id)
        action_elem.set("type", action.action_type)

        # Add properties
        for ptype, pname, pvalue in action.properties:
            self._build_property(action_elem, ptype, pname, pvalue)

        # Add child action references
        for selector_name, action_ids in action.children.items():
            sel_elem = ET.SubElement(action_elem, selector_name)
            for aid in action_ids:
                aid_elem = ET.SubElement(sel_elem, "action-id")
                aid_elem.text = aid

        # Handle extra elements
        for extra_type, extra_data in action.extra_elements:
            if extra_type == "deadzone":
                dz_elem = ET.SubElement(action_elem, "deadzone")
                for ptype, pname, pvalue in extra_data:
                    self._build_property(dz_elem, ptype, pname, pvalue)
            elif extra_type == "control-points":
                cp_elem = ET.SubElement(action_elem, "control-points")
                for ptype, pname, pvalue in extra_data:
                    self._build_property(cp_elem, ptype, pname, pvalue)
            elif extra_type == "macro-actions":
                for ma in extra_data:
                    ma_elem = ET.SubElement(action_elem, "macro-action")
                    ma_elem.set("type", ma["type"])
                    for ptype, pname, pvalue in ma["properties"]:
                        self._build_property(ma_elem, ptype, pname, pvalue)
            elif extra_type == "keyboard-keys":
                for key_info in extra_data:
                    inp_elem = ET.SubElement(action_elem, "input")
                    self._build_property(
                        inp_elem, "int", "scan-code",
                        key_info["scan-code"]
                    )
                    self._build_property(
                        inp_elem, "bool", "is-extended",
                        key_info["is-extended"]
                    )
            elif extra_type == "target-modes":
                for mode_name in extra_data:
                    tm = ET.SubElement(action_elem, "target-mode")
                    self._build_property(tm, "string", "name", mode_name)
            elif extra_type == "conditions":
                for cond_data in extra_data:
                    cond_elem = ET.SubElement(action_elem, "condition")
                    self._build_property(
                        cond_elem, "string", "condition-type",
                        cond_data["condition-type"]
                    )
                    for k, v in cond_data.items():
                        if k != "condition-type":
                            # Determine property type
                            if k in ("scan-code", "id", "vjoy-id"):
                                pt = "int"
                            elif k in ("range-low", "range-high"):
                                pt = "float"
                            elif k in ("extended",):
                                pt = "bool"
                            elif k == "device-guid":
                                pt = "uuid"
                            else:
                                pt = "string"
                            self._build_property(cond_elem, pt, k, v)

    def _build_property(
        self, parent: ET.Element, ptype: str, name: str, value: str
    ):
        prop = ET.SubElement(parent, "property")
        prop.set("type", ptype)
        n = ET.SubElement(prop, "name")
        n.text = name
        v = ET.SubElement(prop, "value")
        v.text = str(value)

    def _build_settings(self, root: ET.Element):
        settings_elem = ET.SubElement(root, "settings")

        if self.settings_node is not None:
            # Startup mode
            sm = self.settings_node.find("startup-mode")
            sm_elem = ET.SubElement(settings_elem, "startup-mode")
            sm_elem.text = sm.text if sm is not None and sm.text else "Default"

            # Macro default delay
            dd = self.settings_node.find("default-delay")
            mdd_elem = ET.SubElement(settings_elem, "macro-default-delay")
            mdd_elem.text = dd.text if dd is not None and dd.text else "0.05"

            # vJoy input IDs
            for vi in self.settings_node.findall("vjoy-input"):
                vid_elem = ET.SubElement(settings_elem, "vjoy-input-id")
                vid_elem.text = vi.get("id", "1")

            # vJoy initial values
            for vjoy_node in self.settings_node.findall("vjoy"):
                vjoy_id = vjoy_node.get("id", "1")
                for axis_node in vjoy_node.findall("axis"):
                    viv = ET.SubElement(settings_elem, "vjoy-initial-value")
                    vid = ET.SubElement(viv, "vjoy-id")
                    vid.text = vjoy_id
                    aid = ET.SubElement(viv, "axis-id")
                    aid.text = axis_node.get("id", "1")
                    val = ET.SubElement(viv, "value")
                    val.text = axis_node.get("value", "0.0")
        else:
            sm_elem = ET.SubElement(settings_elem, "startup-mode")
            sm_elem.text = "Default"
            mdd_elem = ET.SubElement(settings_elem, "macro-default-delay")
            mdd_elem.text = "0.05"

    def _build_scripts(self, scripts_elem: ET.Element):
        """Convert v9 plugins to v14 scripts section."""
        for plugin in self.plugins:
            file_name = plugin.get("file-name", "")
            if not file_name:
                continue

            script_elem = ET.SubElement(scripts_elem, "script")
            script_elem.set("id", new_uuid())

            self._build_property(script_elem, "path", "path", file_name)

            # Convert instances and variables
            for instance in plugin.findall("instance"):
                inst_name = instance.get("name", "Default")
                self._build_property(
                    script_elem, "string", "name", inst_name
                )

                for var_node in instance.findall("variable"):
                    var_elem = ET.SubElement(script_elem, "variable")
                    var_type = var_node.get("type", "String")
                    var_elem.set("type", var_type.lower())

                    self._build_property(
                        var_elem, "string", "name",
                        var_node.get("name", "")
                    )
                    self._build_property(
                        var_elem, "string", "value",
                        var_node.get("value", "")
                    )

    def _convert_merge_axes(
        self, inputs_elem: ET.Element, library_elem: ET.Element
    ):
        """Convert top-level <merge-axis> elements to v14 actions."""
        for ma_node in self.merge_axes:
            mode = ma_node.get("mode", "Default")
            operation = ma_node.get("operation", "average")

            vjoy_node = ma_node.find("vjoy")
            lower_node = ma_node.find("lower")
            upper_node = ma_node.find("upper")

            if vjoy_node is None or lower_node is None or upper_node is None:
                self.log("WARNING: Incomplete merge-axis element, skipping")
                continue

            vjoy_id = vjoy_node.get("vjoy-id", "1")
            vjoy_axis = vjoy_node.get("axis-id", "1")
            lower_guid = self._clean_guid(
                lower_node.get("device-guid", "")
            )
            lower_axis = lower_node.get("axis-id", "1")
            upper_guid = self._clean_guid(
                upper_node.get("device-guid", "")
            )
            upper_axis = upper_node.get("axis-id", "1")

            # Create the output remap action
            remap_action = ActionEntry(
                id=new_uuid(),
                action_type="map-to-vjoy",
                properties=[
                    ("string", "action-label", "Map to vJoy"),
                    ("activation-mode", "activation-mode", "both"),
                    ("int", "vjoy-device-id", vjoy_id),
                    ("int", "vjoy-input-id", vjoy_axis),
                    ("input_type", "vjoy-input-type", "axis"),
                    ("axis_mode", "axis-mode", "absolute"),
                    ("float", "axis-scaling", "1.0"),
                ],
                children={},
            )
            remap_id = self._add_action(remap_action)
            self._build_action_element(library_elem, remap_action)

            # Create the merge-axis action
            merge_action = ActionEntry(
                id=new_uuid(),
                action_type="merge-axis",
                properties=[
                    ("string", "action-label", "Merge Axis"),
                    ("activation-mode", "activation-mode", "disallowed"),
                    ("string", "label", "Merged Axis"),
                    ("uuid", "axis1-guid", lower_guid),
                    ("int", "axis1-axis", lower_axis),
                    ("uuid", "axis2-guid", upper_guid),
                    ("int", "axis2-axis", upper_axis),
                    ("string", "operation", operation),
                ],
                children={"actions": [remap_id]},
            )
            merge_id = self._add_action(merge_action)
            self._build_action_element(library_elem, merge_action)

            # Create root and input for the merge
            root_id = self._make_root_action([merge_id])
            root_action = self._action_map[root_id]
            self._build_action_element(library_elem, root_action)

            # Create input entry for lower axis
            input_entry = InputEntry(
                device_id=lower_guid,
                input_type="axis",
                input_id=lower_axis,
                mode=mode,
            )
            ac = ActionConfigEntry(
                root_action_id=root_id,
                behavior="axis",
            )
            input_entry.action_configs.append(ac)
            self._build_input_element(inputs_elem, input_entry)

            self.log(
                f"Converted merge-axis: {lower_guid}:{lower_axis} + "
                f"{upper_guid}:{upper_axis} -> vJoy {vjoy_id}:{vjoy_axis} "
                f"(operation: {operation})"
            )

    # -------------------------------------------------------------------
    # XML output
    # -------------------------------------------------------------------

    def _write_xml(self, root: ET.Element, output_path: str):
        rough = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough)
        pretty = parsed.toprettyxml(indent="    ", encoding="utf-8")

        # Write with UTF-8 BOM
        with open(output_path, "wb") as f:
            f.write(b"\xef\xbb\xbf")
            # Skip the XML declaration from minidom (it writes its own)
            lines = pretty.split(b"\n")
            # Find where actual content starts (skip <?xml...?>)
            start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(b"<?xml"):
                    start = i + 1
                    break
            # Write XML declaration
            f.write(b'<?xml version="1.0" ?>\n')
            f.write(b"\n".join(lines[start:]))

    # -------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------

    @staticmethod
    def _clean_guid(guid: str) -> str:
        return guid.strip("{}")

    @staticmethod
    def _bool_str(val: str) -> str:
        return "True" if val.lower() in ("true", "1") else "False"


# ---------------------------------------------------------------------------
# GUI Application (only usable when tkinter is available)
# ---------------------------------------------------------------------------

class ConverterApp:
    """Tkinter GUI for the profile converter."""

    def __init__(self, master):
        self.master = master
        master.title("JoystickGremlin Profile Converter (v9 → v14)")
        master.geometry("750x600")
        master.minsize(600, 450)

        self._build_ui()

    def _build_ui(self):
        # Style
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Main frame
        main = ttk.Frame(self.master, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(
            main,
            text="JoystickGremlin Profile Converter",
            font=("Helvetica", 16, "bold"),
        )
        title.pack(pady=(0, 5))

        subtitle = ttk.Label(
            main,
            text="Convert profiles from v9 (R13 and earlier) to v14 (Release 14)",
            font=("Helvetica", 10),
        )
        subtitle.pack(pady=(0, 15))

        # Input file
        input_frame = ttk.LabelFrame(main, text="Input Profile (v9)", padding=10)
        input_frame.pack(fill=tk.X, pady=5)

        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_var)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_in = ttk.Button(
            input_frame, text="Browse...", command=self._browse_input
        )
        browse_in.pack(side=tk.RIGHT)

        # Output file
        output_frame = ttk.LabelFrame(main, text="Output Profile (v14)", padding=10)
        output_frame.pack(fill=tk.X, pady=5)

        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_out = ttk.Button(
            output_frame, text="Browse...", command=self._browse_output
        )
        browse_out.pack(side=tk.RIGHT)

        # Convert button
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=15)

        self.convert_btn = ttk.Button(
            btn_frame,
            text="Convert Profile",
            command=self._do_convert,
        )
        self.convert_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(btn_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=15)

        # Log output
        log_frame = ttk.LabelFrame(main, text="Conversion Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=12, font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Info bar
        info = ttk.Label(
            main,
            text=(
                "Note: Some v9 features (text-to-speech, noop) have no v14 "
                "equivalent and will be converted to descriptions."
            ),
            font=("Helvetica", 8),
            foreground="gray",
        )
        info.pack(pady=(5, 0))

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Select v9 Profile",
            filetypes=[
                ("XML Profiles", "*.xml"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.input_var.set(path)
            # Auto-suggest output name
            base, ext = os.path.splitext(path)
            self.output_var.set(f"{base}_v14{ext}")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save v14 Profile As",
            defaultextension=".xml",
            filetypes=[
                ("XML Profiles", "*.xml"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.output_var.set(path)

    def _do_convert(self):
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()

        if not input_path:
            messagebox.showerror("Error", "Please select an input profile file.")
            return
        if not output_path:
            messagebox.showerror("Error", "Please select an output file location.")
            return
        if not os.path.isfile(input_path):
            messagebox.showerror("Error", f"Input file not found:\n{input_path}")
            return

        self.log_text.delete("1.0", tk.END)
        self.status_label.config(text="Converting...")
        self.master.update_idletasks()

        converter = ProfileConverter()

        try:
            converter.convert(input_path, output_path)
            status = "Conversion successful!"
            self.status_label.config(text=status, foreground="green")
        except Exception as e:
            status = f"Conversion failed: {e}"
            converter.log(f"ERROR: {e}")
            self.status_label.config(text="Conversion failed!", foreground="red")
            messagebox.showerror("Conversion Error", str(e))

        # Show log
        for msg in converter.log_messages:
            self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

        # Summary
        self.log_text.insert(tk.END, "\n--- Summary ---\n")
        self.log_text.insert(
            tk.END, f"Actions in library: {len(converter.library)}\n"
        )
        self.log_text.insert(
            tk.END, f"Input bindings: {len(converter.inputs)}\n"
        )
        self.log_text.insert(
            tk.END, f"Modes: {len(converter.modes)}\n"
        )
        self.log_text.insert(
            tk.END, f"Devices: {len(converter.devices)}\n"
        )
        self.log_text.insert(
            tk.END, f"Merge axes converted: {len(converter.merge_axes)}\n"
        )
        self.log_text.insert(
            tk.END, f"Plugins/scripts converted: {len(converter.plugins)}\n"
        )
        self.log_text.see(tk.END)


# ---------------------------------------------------------------------------
# CLI fallback (no GUI)
# ---------------------------------------------------------------------------

def cli_convert(input_path: str, output_path: str):
    """Command-line conversion when tkinter is not available."""
    converter = ProfileConverter()
    converter.convert(input_path, output_path)
    for msg in converter.log_messages:
        print(msg)
    print(f"\nActions: {len(converter.library)}")
    print(f"Inputs: {len(converter.inputs)}")
    print(f"Modes: {len(converter.modes)}")
    print(f"Devices: {len(converter.devices)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) >= 3:
        # CLI mode: profile_converter.py input.xml output.xml
        cli_convert(sys.argv[1], sys.argv[2])
    elif not HAS_TK:
        print("Tkinter is not available. Use CLI mode:")
        print(f"  python {sys.argv[0]} <input.xml> <output.xml>")
        sys.exit(1)
    else:
        # GUI mode
        try:
            root = tk.Tk()
            ConverterApp(root)
            root.mainloop()
        except tk.TclError as e:
            print(f"Cannot start GUI: {e}")
            print(f"Use CLI mode: python {sys.argv[0]} <input.xml> <output.xml>")
            sys.exit(1)


if __name__ == "__main__":
    main()
