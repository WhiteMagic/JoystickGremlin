# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import contextlib
import types
from collections.abc import Iterator

import pytest
from PySide6 import QtCore

from action_plugins.description import DescriptionData
from action_plugins.root import RootData
from action_plugins.tempo import TempoData
from gremlin.base_classes import AbstractActionData
from gremlin.error import GremlinError
from gremlin.profile import (
    InputItem,
    InputItemBinding,
    Profile,
)
from gremlin.signal import signal
from gremlin.types import InputType
from gremlin.ui.action_model import ActionModel
from gremlin.ui.profile import (
    InputItemBindingModel,
    InputItemModel,
)


@contextlib.contextmanager
def _captured_slot_exceptions() -> Iterator[list[BaseException]]:
    """Collects exceptions PySide6 hands to sys.excepthook instead of re-raising."""
    captured: list[BaseException] = []
    original_excepthook = sys.excepthook

    def _record(
        exception_type: type[BaseException],
        exception_value: BaseException,
        exception_traceback: types.TracebackType | None,
    ) -> None:
        captured.append(exception_value)

    sys.excepthook = _record
    try:
        yield captured
    finally:
        sys.excepthook = original_excepthook


def _make_binding(behavior: InputType) -> InputItemBinding:
    profile = Profile()
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(behavior)
    binding.behavior = behavior
    profile.library.add_action(binding.root_action)

    child_one = DescriptionData(behavior)
    child_two = DescriptionData(behavior)
    profile.library.add_action(child_one)
    profile.library.add_action(child_two)
    binding.root_action.insert_action(child_one, "children")
    binding.root_action.insert_action(child_two, "children")

    return binding


def _make_binding_model(
    behavior: InputType,
) -> tuple[InputItemBindingModel, InputItemModel]:
    """Returns a binding model and the owner that keeps it off the global signal."""
    binding = _make_binding(behavior)
    binding_model = InputItemBindingModel(binding)
    # A real parent keeps _check_user_feedback resolvable when the global signal fires.
    owner = InputItemModel(binding.input_item, 0)
    binding_model.setParent(owner)
    return binding_model, owner


def _make_nested_binding_model() -> tuple[
    InputItemBindingModel, InputItemModel, dict[str, AbstractActionData]
]:
    """Builds a nested tree and returns the model, its owner and its actions.

    The resulting sequence indices are root=0, outer=1, sibling=2, inner=3 and
    leaf=4.
    """
    behavior = InputType.JoystickButton
    profile = Profile()
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(behavior)
    binding.behavior = behavior
    profile.library.add_action(binding.root_action)

    actions = {
        "outer": TempoData(behavior),
        "sibling": DescriptionData(behavior),
        "inner": TempoData(behavior),
        "leaf": DescriptionData(behavior),
    }
    for action in actions.values():
        profile.library.add_action(action)

    binding.root_action.insert_action(actions["outer"], "children")
    binding.root_action.insert_action(actions["sibling"], "children")
    actions["outer"].insert_action(actions["inner"], "short")
    actions["inner"].insert_action(actions["leaf"], "long")

    binding_model = InputItemBindingModel(binding)
    # A real parent keeps _check_user_feedback resolvable when the global signal fires.
    owner = InputItemModel(input_item, 0)
    binding_model.setParent(owner)
    return binding_model, owner, actions


def _make_wide_binding_model() -> tuple[
    InputItemBindingModel, InputItemModel, dict[str, AbstractActionData]
]:
    """Builds a tree with containers wide enough to shift boundaries around.

    Root holds "a", "b", "c", "d" and a tempo in "children"; the tempo holds "p"
    and "q" in "short". Sequence indices follow the level-order walk, so they are
    root=0, a=1, b=2, c=3, d=4, tempo=5, p=6 and q=7.
    """
    behavior = InputType.JoystickButton
    profile = Profile()
    input_item = InputItem(profile.library)
    binding = InputItemBinding(input_item)
    binding.root_action = RootData(behavior)
    binding.behavior = behavior
    profile.library.add_action(binding.root_action)

    actions: dict[str, AbstractActionData] = {
        name: DescriptionData(behavior) for name in ("a", "b", "c", "d", "p", "q")
    }
    actions["tempo"] = TempoData(behavior)
    for action in actions.values():
        profile.library.add_action(action)

    for name in ("a", "b", "c", "d", "tempo"):
        binding.root_action.insert_action(actions[name], "children")
    actions["tempo"].insert_action(actions["p"], "short")
    actions["tempo"].insert_action(actions["q"], "short")

    binding_model = InputItemBindingModel(binding)
    # A real parent keeps _check_user_feedback resolvable when the global signal fires.
    owner = InputItemModel(input_item, 0)
    binding_model.setParent(owner)
    return binding_model, owner, actions


def _container_contents(
    action: AbstractActionData, container: str
) -> list[AbstractActionData]:
    return action.get_actions(container)[0]


def _expansion_by_name(
    binding_model: InputItemBindingModel, actions: dict[str, AbstractActionData]
) -> dict[str, bool]:
    """Maps each named action to what its current model reports for `expanded`."""
    models = [
        # One sequence index per action, plus the root action's own.
        binding_model.get_action_model_by_sidx(sidx)
        for sidx in range(len(actions) + 1)
    ]
    return {
        name: next(model.expanded for model in models if model.action_data is action)
        for name, action in actions.items()
    }


def test_parentless_binding_model_ignores_global_signal() -> None:
    binding_model = InputItemBindingModel(_make_binding(InputType.JoystickButton))

    assert binding_model.parent() is None

    try:
        with _captured_slot_exceptions() as captured:
            signal.inputItemChanged.emit(0)
    finally:
        binding_model.dispose()

    assert captured == []


def test_binding_model_ignores_global_signal_for_foreign_parent() -> None:
    binding_model = InputItemBindingModel(_make_binding(InputType.JoystickButton))
    # Qt ownership can reparent a model onto an object without an enumeration index.
    foreign_parent = QtCore.QObject()
    binding_model.setParent(foreign_parent)

    try:
        with _captured_slot_exceptions() as captured:
            signal.inputItemChanged.emit(0)
    finally:
        binding_model.dispose()

    assert captured == []


def test_behavior_switch_clears_children() -> None:
    iibm, _owner = _make_binding_model(InputType.JoystickButton)
    binding = iibm.input_item_binding
    root_id = binding.root_action.id
    child_ids = [child.id for child in binding.root_action.get_actions()[0]]

    assert len(child_ids) == 2
    assert all(binding.library.has_action(cid) for cid in child_ids)

    iibm.behavior = InputType.to_string(InputType.JoystickAxis)

    # Root action identity is preserved, but its contents are wiped.
    assert binding.root_action.id == root_id
    assert binding.root_action.get_actions()[0] == []
    assert binding.behavior == InputType.JoystickAxis
    assert all(not binding.library.has_action(cid) for cid in child_ids)


def test_behavior_switch_noop_keeps_children() -> None:
    iibm, _owner = _make_binding_model(InputType.JoystickButton)
    binding = iibm.input_item_binding
    child_ids = [child.id for child in binding.root_action.get_actions()[0]]

    iibm.behavior = InputType.to_string(InputType.JoystickButton)

    assert [child.id for child in binding.root_action.get_actions()[0]] == child_ids
    assert all(binding.library.has_action(cid) for cid in child_ids)


def test_has_child_actions() -> None:
    iibm, _owner = _make_binding_model(InputType.JoystickButton)
    root_model = iibm.get_action_model_by_sidx(0)

    assert root_model.hasChildren is True

    for child in root_model.getActions("children"):
        assert child.hasChildren is False


def test_drop_action_noop_boundary_keeps_action_models() -> None:
    iibm, _owner = _make_binding_model(InputType.JoystickButton)

    root_model = iibm.get_action_model_by_sidx(0)
    children_before = root_model.getActions("children")
    action_ids_before = [model.action_data.id for model in children_before]
    dropped_model = iibm.get_action_model_by_sidx(1)

    reload_count = 0

    def _count_reload() -> None:
        nonlocal reload_count
        reload_count += 1

    signal.reloadCurrentInputItem.connect(_count_reload)
    try:
        # Boundary 0 is the leading edge of the action already sitting there.
        root_model.dropAction(1, "children", 0)
    finally:
        signal.reloadCurrentInputItem.disconnect(_count_reload)

    assert reload_count == 1

    # The models QML already holds must survive; rebuilding them strands the view.
    assert iibm.get_action_model_by_sidx(0) is root_model
    assert iibm.get_action_model_by_sidx(1) is dropped_model
    children_after = root_model.getActions("children")
    assert len(children_after) == len(children_before)
    assert all(
        after is before
        for after, before in zip(children_after, children_before, strict=True)
    )
    assert [model.action_data.id for model in children_after] == action_ids_before


def test_drop_action_moves_into_target_container() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()
    tempo_model = binding_model.get_action_model_by_sidx(5)

    reload_count = 0

    def _count_reload() -> None:
        nonlocal reload_count
        reload_count += 1

    signal.reloadCurrentInputItem.connect(_count_reload)
    try:
        tempo_model.dropAction(2, "short", 1)
    finally:
        signal.reloadCurrentInputItem.disconnect(_count_reload)

    assert reload_count == 1
    assert _container_contents(binding_model.root_action, "children") == [
        actions["a"],
        actions["c"],
        actions["d"],
        actions["tempo"],
    ]
    assert _container_contents(actions["tempo"], "short") == [
        actions["p"],
        actions["b"],
        actions["q"],
    ]


def test_drop_action_reloads_ui_on_invalid_boundary() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()
    root_model = binding_model.get_action_model_by_sidx(0)

    reload_ui_count = 0
    reload_item_count = 0

    def _count_reload_ui() -> None:
        nonlocal reload_ui_count
        reload_ui_count += 1

    def _count_reload_item() -> None:
        nonlocal reload_item_count
        reload_item_count += 1

    signal.reloadUi.connect(_count_reload_ui)
    signal.reloadCurrentInputItem.connect(_count_reload_item)
    try:
        # QML can only ever propose a boundary in range, so this is a bug report.
        root_model.dropAction(1, "children", 99)
    finally:
        signal.reloadUi.disconnect(_count_reload_ui)
        signal.reloadCurrentInputItem.disconnect(_count_reload_item)

    assert reload_ui_count == 1
    assert reload_item_count == 0
    assert _container_contents(binding_model.root_action, "children") == [
        actions["a"],
        actions["b"],
        actions["c"],
        actions["d"],
        actions["tempo"],
    ]


def test_drop_action_is_registered_as_a_slot() -> None:
    binding_model, _owner, _actions = _make_wide_binding_model()
    root_model = binding_model.get_action_model_by_sidx(0)

    assert hasattr(ActionModel, "dropAction")
    assert (
        type(root_model).staticMetaObject.indexOfSlot("dropAction(int,QString,int)")
        >= 0
    )


def test_is_descendant_of_reports_subtree_membership() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()
    sequence_indices = {
        sidx: binding_model.get_action_model_by_sidx(sidx).sequence_index
        for sidx in range(5)
    }

    # The outer tempo owns the inner tempo and, transitively, the leaf.
    for candidate in (1, 3, 4):
        assert (
            binding_model._is_descendant_of(
                sequence_indices[candidate], sequence_indices[1]
            )
            is True
        )
    for candidate in (0, 2):
        assert (
            binding_model._is_descendant_of(
                sequence_indices[candidate], sequence_indices[1]
            )
            is False
        )

    # A leaf is an ancestor of nothing but itself.
    assert (
        binding_model._is_descendant_of(sequence_indices[2], sequence_indices[2])
        is True
    )
    assert (
        binding_model._is_descendant_of(sequence_indices[1], sequence_indices[2])
        is False
    )
    assert (
        binding_model._is_descendant_of(sequence_indices[4], sequence_indices[2])
        is False
    )

    # Every action is inside the root's subtree.
    for candidate in range(5):
        assert (
            binding_model._is_descendant_of(
                sequence_indices[candidate], sequence_indices[0]
            )
            is True
        )


def test_can_move_action_rejects_direct_child_target() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    # The inner tempo lives in the outer tempo's "short" container.
    assert binding_model.can_move_action(1, 3) is False


def test_can_move_action_rejects_grandchild_target() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    # The leaf sits two levels below the outer tempo.
    assert binding_model.can_move_action(1, 4) is False


def test_can_move_action_rejects_self_target() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    assert binding_model.can_move_action(1, 1) is False


def test_can_move_action_allows_sibling_reorder() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    assert binding_model.can_move_action(1, 2) is True


def test_can_move_action_allows_unrelated_container() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    assert binding_model.can_move_action(2, 3) is True


def test_can_move_action_returns_false_for_unknown_indices() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()

    # QML has no way to act on an exception, so an unknown index is just invalid.
    assert binding_model.can_move_action(99, 1) is False
    assert binding_model.can_move_action(1, 99) is False


def test_can_move_action_is_side_effect_free() -> None:
    binding_model, _owner, actions = _make_nested_binding_model()
    root_action = binding_model.root_action
    models_before = [binding_model.get_action_model_by_sidx(sidx) for sidx in range(5)]

    binding_model.can_move_action(1, 3)
    binding_model.can_move_action(1, 2)
    binding_model.can_move_action(99, 1)

    assert [binding_model.get_action_model_by_sidx(sidx) for sidx in range(5)] == (
        models_before
    )
    assert _container_contents(root_action, "children") == [
        actions["outer"],
        actions["sibling"],
    ]
    assert _container_contents(actions["outer"], "short") == [actions["inner"]]
    assert _container_contents(actions["inner"], "long") == [actions["leaf"]]


def test_can_accept_drop_rejects_own_ancestor() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()
    inner_model = binding_model.get_action_model_by_sidx(3)

    # The inner tempo cannot swallow the outer tempo it lives inside.
    assert inner_model.canAcceptDrop(1) is False


def test_can_accept_drop_allows_legal_source() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()
    sibling_model = binding_model.get_action_model_by_sidx(2)

    assert sibling_model.canAcceptDrop(1) is True


def test_can_accept_drop_is_registered_as_a_slot() -> None:
    binding_model, _owner, _actions = _make_nested_binding_model()
    inner_model = binding_model.get_action_model_by_sidx(3)

    assert hasattr(ActionModel, "canAcceptDrop")
    assert type(inner_model).staticMetaObject.indexOfSlot("canAcceptDrop(int)") >= 0


def test_wide_binding_model_sequence_indices() -> None:
    """Pins the level-order numbering every boundary test below is written against."""
    binding_model, _owner, actions = _make_wide_binding_model()

    expected = ["a", "b", "c", "d", "tempo", "p", "q"]
    for sidx, name in enumerate(expected, start=1):
        model = binding_model.get_action_model_by_sidx(sidx)
        assert model.action_data is actions[name], f"sidx {sidx} is not {name}"


def test_move_action_moves_sibling_backward() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    binding_model.move_action(3, 0, "children", 0)

    assert _container_contents(binding_model.root_action, "children") == [
        actions["c"],
        actions["a"],
        actions["b"],
        actions["d"],
        actions["tempo"],
    ]


def test_move_action_moves_sibling_forward() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    # Boundary 3 is read against the pre-move container, so removing "a" first has to
    # pull it down to 2.
    binding_model.move_action(1, 0, "children", 3)

    assert _container_contents(binding_model.root_action, "children") == [
        actions["b"],
        actions["c"],
        actions["a"],
        actions["d"],
        actions["tempo"],
    ]


def test_move_action_appends_at_trailing_boundary() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    binding_model.move_action(1, 0, "children", 5)

    assert _container_contents(binding_model.root_action, "children") == [
        actions["b"],
        actions["c"],
        actions["d"],
        actions["tempo"],
        actions["a"],
    ]


def test_move_action_noop_boundaries_change_nothing() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()
    models_before = [binding_model.get_action_model_by_sidx(sidx) for sidx in range(8)]
    order_before = [actions[name] for name in ("a", "b", "c", "d", "tempo")]

    # The two boundaries either side of "b" are where it already sits.
    binding_model.move_action(2, 0, "children", 1)
    binding_model.move_action(2, 0, "children", 2)

    assert _container_contents(binding_model.root_action, "children") == order_before
    # A no-op must not rebuild -- that would strand every model QML is holding.
    assert [
        binding_model.get_action_model_by_sidx(sidx) for sidx in range(8)
    ] == models_before


def test_move_action_into_unrelated_container() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    binding_model.move_action(2, 5, "short", 1)

    assert _container_contents(binding_model.root_action, "children") == [
        actions["a"],
        actions["c"],
        actions["d"],
        actions["tempo"],
    ]
    assert _container_contents(actions["tempo"], "short") == [
        actions["p"],
        actions["b"],
        actions["q"],
    ]


def test_move_action_lifts_action_out_of_container() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    binding_model.move_action(7, 0, "children", 2)

    assert _container_contents(binding_model.root_action, "children") == [
        actions["a"],
        actions["b"],
        actions["q"],
        actions["c"],
        actions["d"],
        actions["tempo"],
    ]
    assert _container_contents(actions["tempo"], "short") == [actions["p"]]


def test_move_action_into_own_subtree_rejected() -> None:
    binding_model, _owner, actions = _make_nested_binding_model()
    root_action = binding_model.root_action
    models_before = [binding_model.get_action_model_by_sidx(sidx) for sidx in range(5)]

    # A container of the outer tempo's own child, and of its grandchild.
    binding_model.move_action(1, 3, "long", 0)
    binding_model.move_action(1, 4, "children", 0)

    assert _container_contents(root_action, "children") == [
        actions["outer"],
        actions["sibling"],
    ]
    assert _container_contents(actions["outer"], "short") == [actions["inner"]]
    assert _container_contents(actions["inner"], "long") == [actions["leaf"]]
    assert [binding_model.get_action_model_by_sidx(sidx) for sidx in range(5)] == (
        models_before
    )


def test_move_action_into_itself_rejected() -> None:
    binding_model, _owner, actions = _make_nested_binding_model()
    root_action = binding_model.root_action

    binding_model.move_action(1, 1, "short", 0)

    assert _container_contents(root_action, "children") == [
        actions["outer"],
        actions["sibling"],
    ]
    assert _container_contents(actions["outer"], "short") == [actions["inner"]]


def test_move_action_rejects_out_of_range_boundary() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    for position in (-1, 6):
        with pytest.raises(GremlinError):
            binding_model.move_action(1, 0, "children", position)

    assert _container_contents(binding_model.root_action, "children") == [
        actions[name] for name in ("a", "b", "c", "d", "tempo")
    ]


def test_move_action_rejects_unknown_container() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    with pytest.raises(GremlinError):
        binding_model.move_action(1, 0, "nonexistent", 0)

    # A rejection that removed the source first would leave the action nowhere.
    assert _container_contents(binding_model.root_action, "children") == [
        actions[name] for name in ("a", "b", "c", "d", "tempo")
    ]


def test_expansion_state_survives_a_move() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    binding_model.get_action_model_by_sidx(3).expanded = False
    binding_model.get_action_model_by_sidx(7).expanded = False
    assert _expansion_by_name(binding_model, actions) == {
        "a": True,
        "b": True,
        "c": False,
        "d": True,
        "p": True,
        "q": False,
        "tempo": True,
    }

    # Moving "a" to the end of "children" renumbers every action behind it.
    binding_model.move_action(1, 0, "children", 5)

    assert _expansion_by_name(binding_model, actions) == {
        "a": True,
        "b": True,
        "c": False,
        "d": True,
        "p": True,
        "q": False,
        "tempo": True,
    }


def test_expansion_syncs_across_shared_placements() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()
    # Inserting an existing library action puts one instance at two places in the tree,
    # which is what the Reference action's "use existing" path does.
    binding_model.root_action.insert_action(actions["p"], "children")
    binding_model.sync_data()

    first = binding_model.get_action_model_by_sidx(6)
    second = binding_model.get_action_model_by_sidx(7)
    assert first.action_data is actions["p"]
    assert second.action_data is actions["p"]

    change_count = 0

    def _count_change() -> None:
        nonlocal change_count
        change_count += 1

    second.actionChanged.connect(_count_change)
    try:
        first.expanded = False
    finally:
        second.actionChanged.disconnect(_count_change)

    # Both placements have to fold in the same event, or the second one paints stale.
    assert second.expanded is False
    assert change_count == 1


def test_move_action_rejects_unknown_sequence_index() -> None:
    binding_model, _owner, actions = _make_wide_binding_model()

    with pytest.raises(GremlinError):
        binding_model.move_action(99, 0, "children", 0)
    with pytest.raises(GremlinError):
        binding_model.move_action(1, 99, "children", 0)

    assert _container_contents(binding_model.root_action, "children") == [
        actions[name] for name in ("a", "b", "c", "d", "tempo")
    ]
