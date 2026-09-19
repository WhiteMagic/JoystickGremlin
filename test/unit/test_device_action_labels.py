# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pathlib

from gremlin.profile import Profile
from gremlin.ui.device import _action_labels_from_item


def test_action_labels_dfs_order(xml_dir: pathlib.Path) -> None:
    profile = Profile()
    profile.from_xml(xml_dir / "profile_hierarchy.xml")

    input_items = [item for items in profile.inputs.values() for item in items]
    assert len(input_items) == 1

    # Tempo holds the same Description in both its short and long container.
    assert _action_labels_from_item(input_items[0]) == [
        "Description",
        "Tempo",
        "Description",
        "Description",
        "Description",
    ]
