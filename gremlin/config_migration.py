# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import Any

from gremlin import util


def _upgrade_from_16_0_0(data: dict[str, Any]) -> None:
    automation = data.get("profile", {}).get("automation", {})

    remain_active = automation.pop("remain-active-on-focus-loss", None)
    if remain_active is not None:
        is_active = util.parse_bool(remain_active["value"])
        automation["focus-loss-behavior"] = {
            "value": "Remain active" if is_active else "Deactivate",
            "data_type": "selection",
            "properties": {
                "valid_options": ["Deactivate", "Remain active", "Load default"]
            },
            "expose": True,
        }

    entries = automation.get("entries-auto-loading")
    if entries is not None:
        entries["value"] = [
            [*entry, False] if len(entry) == 3 else entry for entry in entries["value"]
        ]


# Sequentially ordered list of version upgrade functions. Each is used to upgrade a
# configuration of that version to the next.
_UPGRADES = [
    ("16.0.0", _upgrade_from_16_0_0),
]


def migrate_config(data: dict[str, Any]) -> None:
    """Upgrades the raw content of a configuration file to the current format.

    Version information is derived from the last-run-version property, but the value
    itself is not modified.

    Args:
        data: raw content of the configuration file to update
    """
    # Attempt to retrieve the version by parsing through the JSON dict, handling
    # non-existence gracefully.
    last_run_version_str = (
        data.get("global", {})
        .get("internal", {})
        .get("last-run-version", {})
        .get("value", None)
    )
    last_version = (
        util.parse_version(last_run_version_str) if last_run_version_str else None
    )
    for version, upgrade in _UPGRADES:
        if last_version is None or last_version <= util.parse_version(version):
            upgrade(data)
