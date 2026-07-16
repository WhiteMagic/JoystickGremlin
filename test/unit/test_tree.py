# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import pytest

import gremlin.error
from gremlin.tree import TreeNode


def test_constructor() -> None:
    n1 = TreeNode(1)
    assert n1.value == 1
    assert n1.children == []
    assert n1.parent is None
    assert n1.depth == 0
    assert n1.depth_first_index == 0
    assert n1.node_count == 1

    n2 = TreeNode(2, None)
    assert n2.value == 2
    assert n2.children == []
    assert n2.parent is None
    assert n2.depth == 0
    assert n2.depth_first_index == 0
    assert n2.node_count == 1

    n3 = TreeNode(3, n1)
    assert n3.value == 3
    assert n3.children == []
    assert n3.parent == n1
    assert n1.children == [n3]
    assert n3.depth == 1
    assert n3.depth_first_index == 1
    assert n3.node_count == 2


def test_add_child() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2)
    n3 = TreeNode(3)
    n4 = TreeNode(4)

    n1.add_child(n2)
    assert n1.children == [n2]
    assert n2.parent == n1
    assert n1.depth == 0
    assert n2.depth == 1
    assert n1.node_count == 2

    n1.add_child(n3)
    assert n1.children == [n2, n3]
    assert n3.parent == n1
    assert n3.depth == 1
    assert n3.node_count == 3

    n1.add_child(n4)
    assert n1.children == [n2, n3, n4]
    assert n4.parent == n1
    assert n4.depth == 1
    assert n2.node_count == 4


def test_add_sibling() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2)
    n3 = TreeNode(3)
    n4 = TreeNode(4)

    with pytest.raises(gremlin.error.GremlinError):
        n1.append_sibling(n2)
        assert n1.children == []

    n1.add_child(n2)
    assert n1.children == [n2]
    assert n2.parent == n1
    assert n1.depth == 0
    assert n2.depth == 1
    assert n1.node_count == 2

    n2.append_sibling(n3)
    assert n1.children == [n2, n3]
    assert n2.children == []
    assert n3.parent == n1
    assert n3.depth == 1
    assert n1.node_count == 3

    n2.append_sibling(n4)
    assert n1.children == [n2, n3, n4]
    assert n2.children == []
    assert n4.parent == n1
    assert n1.node_count == 4


def test_set_parent() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2)
    assert n1.parent is None
    assert n2.parent is None
    assert n1.node_count == 1
    assert n2.node_count == 1

    n2.set_parent(n1)
    assert n1.parent is None
    assert n2.parent == n1
    assert n1.children == [n2]
    assert n2.children == []
    assert n1.node_count == 2

    with pytest.raises(gremlin.error.GremlinError):
        n1.set_parent(n2)
        assert n1.parent is None
        assert n2.parent == n1
        assert n1.children == [n2]
        assert n2.children == []

    n2.detach()
    assert n1.parent is None
    assert n2.parent is None
    assert n1.children == []
    assert n2.children == []
    assert n1.node_count == 1
    assert n2.node_count == 1

    n1.set_parent(n2)
    assert n1.parent == n2
    assert n2.parent is None
    assert n1.children == []
    assert n2.children == [n1]
    assert n1.node_count == 2


def test_remove_child() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)

    assert n1.parent is None
    assert n1.children == [n2, n3]
    assert n2.parent == n1
    assert n2.children == [n4, n5]
    assert n3.parent == n1
    assert n3.children == []
    assert n4.parent == n2
    assert n4.children == []
    assert n5.parent == n2
    assert n5.children == []

    n2.remove_child(n5)
    assert n2.parent == n1
    assert n2.children == [n4]
    assert n5.parent is None
    assert n5.children == []

    n1.remove_child(n2)
    assert n1.parent is None
    assert n1.children == [n3]
    assert n2.parent is None
    assert n2.children == [n4]
    assert n5.parent is None
    assert n5.children == []


def test_detach() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)

    assert n1.parent is None
    assert n1.children == [n2, n3]
    assert n2.parent == n1
    assert n2.children == [n4, n5]
    assert n3.parent == n1
    assert n3.children == []
    assert n4.parent == n2
    assert n4.children == []
    assert n5.parent == n2
    assert n5.children == []
    assert n1.node_count == 5

    n2.detach()
    assert n1.parent is None
    assert n1.children == [n3]
    assert n2.parent is None
    assert n2.children == [n4, n5]
    assert n1.node_count == 2
    assert n2.node_count == 3

    n1.detach()
    assert n1.parent is None
    assert n1.children == [n3]

    n5.detach()
    assert n2.parent is None
    assert n2.children == [n4]
    assert n5.parent is None
    assert n5.children == []


def test_is_descendant() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)
    n6 = TreeNode(6)

    assert n1.parent is None
    assert n1.children == [n2, n3]
    assert n2.parent == n1
    assert n2.children == [n4, n5]
    assert n3.parent == n1
    assert n3.children == []
    assert n4.parent == n2
    assert n4.children == []
    assert n5.parent == n2
    assert n5.children == []

    assert n1.depth == 0
    assert n2.depth == 1
    assert n3.depth == 1
    assert n4.depth == 2
    assert n5.depth == 2

    assert n1.is_descendant(n5)
    assert not n5.is_descendant(n1)
    assert not n1.is_descendant(n6)
    assert not n6.is_descendant(n1)
    assert not n2.is_descendant(n3)
    assert not n3.is_descendant(n3)
    assert n2.is_descendant(n4)
    assert not n4.is_descendant(n2)

    assert n1.depth_first_index == 0
    assert n2.depth_first_index == 1
    assert n3.depth_first_index == 4
    assert n4.depth_first_index == 2
    assert n5.depth_first_index == 3

    assert n1.node_count == 5
    assert n6.node_count == 1


def test_nodes_matching() -> None:
    n1 = TreeNode(2)
    n2 = TreeNode(4, n1)
    n3 = TreeNode(6, n1)
    n4 = TreeNode(8, n1)

    assert n1.nodes_matching(lambda x: x.value == 2) == [n1]
    assert n1.nodes_matching(lambda x: x.value % 2 == 0) == [n1, n2, n3, n4]
    assert n1.nodes_matching(lambda x: x.value / 5 == 0) == []
    assert n1.nodes_matching(lambda x: x.value % 3 == 0) == [n3]


def test_sibling_reordering() -> None:
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n1)

    assert n1.children == [n2, n3, n4]

    n4.detach()
    n2.insert_sibling_before(n4)
    assert n1.children == [n4, n2, n3]

    n4.detach()
    n2.insert_sibling_after(n4)
    assert n1.children == [n2, n4, n3]
