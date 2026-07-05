"""Binary inspection tree model for the MMI problem (Sec. III / IV-B.1).

An apartment building's n smart meters are the leaves of a binary
inspection tree.  Probing a node is one inspection step: an inspector
placed at the node compares its own reading against the sum reported by
all meters in its subtree, so a node reads "dirty" iff its subtree
contains at least one malicious meter.  We simulate that check as an
exact oracle via a precomputed per-node dirty count.
"""

import math

DIRTY = "dirty"
CLEAN = "clean"


class Node:
    __slots__ = ("lchild", "rchild", "parent", "level", "meter_id",
                 "dirty", "dirty_count", "n_leaves", "subR", "resolved")

    def __init__(self):
        self.lchild = None
        self.rchild = None
        self.parent = None
        self.level = 0
        self.meter_id = None      # set only on leaves
        self.dirty = False        # leaf status (element of Perm_U)
        self.dirty_count = 0      # dirty leaves in this subtree
        self.n_leaves = 0
        self.subR = 0.0           # subtree dirty ratio, used by ATI
        self.resolved = False     # subtree fully accounted for (ATI)

    @property
    def is_leaf(self):
        return self.lchild is None


class InspectionTree:
    def __init__(self, root):
        self.root = root
        self.postorder = []       # children before parents
        stack, out = [root], []
        while stack:
            node = stack.pop()
            out.append(node)
            if not node.is_leaf:
                stack.append(node.lchild)
                stack.append(node.rchild)
        self.postorder = out[::-1]
        for node in self.postorder:
            node.level = 0        # recomputed below (needs top-down pass)
        for node in reversed(self.postorder):   # parents before children
            if not node.is_leaf:
                node.lchild.level = node.level + 1
                node.rchild.level = node.level + 1
        for node in self.postorder:
            node.n_leaves = 1 if node.is_leaf else (node.lchild.n_leaves +
                                                    node.rchild.n_leaves)
        self.leaves = [n for n in self.postorder if n.is_leaf]
        self.n = len(self.leaves)
        self.leaf_level = max(leaf.level for leaf in self.leaves)


def build_inspection_tree(meter_ids, rng=None):
    """Build the inspection tree of Sec. IV-B.1.

    If n is a power of two the tree is complete; otherwise a complete
    tree with 2^i leaves (2^i < n < 2^(i+1)) is extended one meter at a
    time with the PullDown operation (Fig. 2): an existing leaf becomes
    an internal node whose children are the old meter and the new one.
    Leaf positions are assigned to meters in shuffled order so that the
    tree is built "in a random manner" as the ATI heuristic requires.
    """
    ids = list(meter_ids)
    if rng is not None:
        rng.shuffle(ids)
    n = len(ids)
    if n == 0:
        raise ValueError("need at least one meter")
    base = 2 ** int(math.floor(math.log2(n))) if n > 1 else 1

    def complete(depth):
        node = Node()
        if depth > 0:
            node.lchild = complete(depth - 1)
            node.rchild = complete(depth - 1)
            node.lchild.parent = node
            node.rchild.parent = node
        return node

    root = complete(int(math.log2(base)))

    def leaves_in_order(node):
        if node.is_leaf:
            return [node]
        return leaves_in_order(node.lchild) + leaves_in_order(node.rchild)

    for old_leaf in leaves_in_order(root)[:n - base]:   # PullDown
        for _ in range(2):
            child = Node()
            child.parent = old_leaf
            if old_leaf.lchild is None:
                old_leaf.lchild = child
            else:
                old_leaf.rchild = child

    tree = InspectionTree(root)
    for leaf, meter_id in zip(tree.leaves, ids):
        leaf.meter_id = meter_id
    return tree


def assign_dirty(tree, dirty_ids):
    """Mark the given meters malicious and reset all per-run node state."""
    dirty_ids = set(dirty_ids)
    for node in tree.postorder:
        if node.is_leaf:
            node.dirty = node.meter_id in dirty_ids
            node.dirty_count = 1 if node.dirty else 0
        else:
            node.dirty_count = node.lchild.dirty_count + node.rchild.dirty_count
        node.subR = 0.0
        node.resolved = False
    return tree


class Prober:
    """Counts inspection steps (N_S).  Results are cached: the probing log
    is tamper-evident (Sec. IV-B), so a node's known status is never
    re-purchased with another step within one inspection round."""

    def __init__(self):
        self.steps = 0
        self._cache = {}

    def probe(self, node):
        result = self._cache.get(id(node))
        if result is None:
            self.steps += 1
            result = DIRTY if node.dirty_count > 0 else CLEAN
            self._cache[id(node)] = result
        return result
