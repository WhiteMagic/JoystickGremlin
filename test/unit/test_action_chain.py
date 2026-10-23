# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

from unittest import mock

from action_plugins.chain import ChainData, ChainFunctor
from gremlin.base_classes import Value


def test_release_after_timeout_reaches_pressed_sequence() -> None:
    action = ChainData()
    action.chain_sequences = [[], [], []]
    action.timeout = 1.0
    functor = ChainFunctor(action)
    event = mock.MagicMock()

    with mock.patch("action_plugins.chain.time.time", return_value=1.0):
        for is_pressed in [True, False, True]:
            functor(event, Value(is_pressed))
    assert functor.current_index == 1

    # Hold longer than the timeout before releasing.
    with mock.patch("action_plugins.chain.time.time", return_value=2.0):
        functor(event, Value(False))

    assert functor.current_index == 2
