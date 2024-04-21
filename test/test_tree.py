# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>


import sys
sys.path.append(".")

import pytest

import gremlin.error
from gremlin.tree import TreeNode


def test_constructor():
    n1 = TreeNode(1)
    assert n1.value == 1
    assert n1.children == []
    assert n1.parent == None
    assert n1.depth == 0
    assert n1.depth_first_index == 0
    assert n1.node_count == 1

    n2 = TreeNode(2, None)
    assert n2.value == 2
    assert n2.children == []
    assert n2.parent == None
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


def test_add_child():
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
    assert n2.node_count ==4


def test_add_sibling():
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


def test_set_parent():
    n1 = TreeNode(1)
    n2 = TreeNode(2)
    assert n1.parent == None
    assert n2.parent == None
    assert n1.node_count == 1
    assert n2.node_count == 1

    n2.set_parent(n1)
    assert n1.parent == None
    assert n2.parent == n1
    assert n1.children == [n2]
    assert n2.children == []
    assert n1.node_count == 2

    with pytest.raises(gremlin.error.GremlinError):
        n1.set_parent(n2)
        assert n1.parent == None
        assert n2.parent == n1
        assert n1.children == [n2]
        assert n2.children == []

    n2.detach()
    assert n1.parent == None
    assert n2.parent == None
    assert n1.children == []
    assert n2.children == []
    assert n1.node_count == 1
    assert n2.node_count == 1

    n1.set_parent(n2)
    assert n1.parent == n2
    assert n2.parent == None
    assert n1.children == []
    assert n2.children == [n1]
    assert n1.node_count == 2


def test_remove_child():
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)

    assert n1.parent == None
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
    assert n5.parent == None
    assert n5.children == []

    n1.remove_child(n2)
    assert n1.parent == None
    assert n1.children == [n3]
    assert n2.parent == None
    assert n2.children == [n4]
    assert n5.parent == None
    assert n5.children == []


def test_detach():
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)

    assert n1.parent == None
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
    assert n1.parent == None
    assert n1.children == [n3]
    assert n2.parent == None
    assert n2.children == [n4, n5]
    assert n1.node_count == 2
    assert n2.node_count == 3

    n1.detach()
    assert n1.parent == None
    assert n1.children == [n3]

    n5.detach()
    assert n2.parent == None
    assert n2.children == [n4]
    assert n5.parent == None
    assert n5.children == []


def test_is_descendant():
    n1 = TreeNode(1)
    n2 = TreeNode(2, n1)
    n3 = TreeNode(3, n1)
    n4 = TreeNode(4, n2)
    n5 = TreeNode(5, n2)
    n6 = TreeNode(6)

    assert n1.parent == None
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

    assert n1.is_descendant(n5) == True
    assert n5.is_descendant(n1) == False
    assert n1.is_descendant(n6) == False
    assert n6.is_descendant(n1) == False
    assert n2.is_descendant(n3) == False
    assert n3.is_descendant(n3) == False
    assert n2.is_descendant(n4) == True
    assert n4.is_descendant(n2) == False

    assert n1.depth_first_index == 0
    assert n2.depth_first_index == 1
    assert n3.depth_first_index == 4
    assert n4.depth_first_index == 2
    assert n5.depth_first_index == 3

    assert n1.node_count == 5
    assert n6.node_count == 1


def test_nodes_matching():
    n1 = TreeNode(2)
    n2 = TreeNode(4, n1)
    n3 = TreeNode(6, n1)
    n4 = TreeNode(8, n1)

    assert n1.nodes_matching(lambda x: x.value == 2) == [n1]
    assert n1.nodes_matching(lambda x: x.value % 2 == 0) == [n1, n2, n3, n4]
    assert n1.nodes_matching(lambda x: x.value / 5 == 0) == []
    assert n1.nodes_matching(lambda x: x.value % 3 == 0) == [n3]


def test_sibling_reordering():
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