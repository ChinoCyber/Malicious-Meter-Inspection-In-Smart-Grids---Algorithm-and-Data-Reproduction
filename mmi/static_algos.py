"""Static inspection algorithms (Sec. IV): the malicious set Q does not
change while the inspection runs.  Each algorithm takes an
InspectionTree with dirty statuses already assigned and returns
(Q, N_S): the list of malicious leaf nodes found and the number of
probing steps spent.
"""

import math

from .tree import DIRTY, Prober


def scanning(tree):
    """Brute-force scan (Sec. IV-A): probe every meter once, N_S = n."""
    prober = Prober()
    q = [leaf for leaf in tree.leaves if prober.probe(leaf) == DIRTY]
    return q, prober.steps


def bi_v1(tree):
    """Binary-tree inspection BI_v1 (Table III): probe top-down, descend
    into both children of every dirty internal node, skip clean subtrees."""
    prober = Prober()
    q = []

    def inspect(node):
        if prober.probe(node) == DIRTY:
            if node.is_leaf:
                q.append(node)
            else:
                inspect(node.lchild)
                inspect(node.rchild)

    inspect(tree.root)
    return q, prober.steps


def bi_v2(tree):
    """BI_v2 (Table IV): like BI_v1, but when a dirty node's left child
    probes clean its right child is dirty by inference and costs no probe."""
    prober = Prober()
    q = []

    def expand(node):   # node is known dirty, probed or inferred
        if node.is_leaf:
            q.append(node)
        elif prober.probe(node.lchild) == DIRTY:
            expand(node.lchild)
            if prober.probe(node.rchild) == DIRTY:
                expand(node.rchild)
        else:
            expand(node.rchild)

    if prober.probe(tree.root) == DIRTY:
        expand(tree.root)
    return q, prober.steps


class _AdaptiveInspection:
    """Adaptive Tree Inspection, ATI (Table V / Sec. IV-D).

    A DFS over the tree that may "jump": skip D levels below a dirty
    internal node and probe its 2^D descendants at that depth directly,
    blending binary inspection with scanning.  The jump decision uses
    two on-line statistics:

      R    running dirty-meter ratio over the meters accounted for so far
      S_l  similarity of level l: the standard deviation, around R, of
           the subtree dirty ratios (subR) known at level l

    following the paper's rules: never jump from a leaf's parent, never
    jump while R < 0.13 (the BI-beats-scanning threshold from Lemma 4),
    never jump while S_l/R >= 1, otherwise jump
    D = ceil((1 - S_l/R) * distance-to-leaves), so S_l = 0 sends the
    inspection straight to the leaves.

    Interpretation note: Table V descends dirty nodes like BI_v1, but the
    paper's Figs. 9-11 show ATI at or below BI_v2 everywhere, which is
    impossible without BI_v2's inference (with R < 0.13 no jump ever
    fires, so a literal Table V collapses onto BI_v1).  We therefore use
    the BI_v2 skip in the non-jump descent: a dirty node whose left
    child probes clean has a dirty right child that costs no probe.
    """

    JUMP_THRESHOLD = 0.13

    def __init__(self, tree, jump_rule="original", jump_threshold=None):
        self.tree = tree
        self.prober = Prober()
        self.q = []
        self.num_meter = 0
        self.num_dirty = 0
        # per-level aggregates of known subRs: [count, sum, sum of squares]
        self.level_stats = {}
        # jump policy (see _decide_jump): the defaults reproduce Table V,
        # the simulator exposes the others to probe how far ATI can be
        # pushed below scanning at high dirty ratios.
        self.jump_rule = jump_rule
        self.jump_threshold = (self.JUMP_THRESHOLD if jump_threshold is None
                               else jump_threshold)

    def run(self):
        self._visit(self.tree.root)
        return self.q, self.prober.steps

    # -- statistics ----------------------------------------------------
    def _record(self, level, sub_r, count=1):
        stats = self.level_stats.setdefault(level, [0, 0.0, 0.0])
        stats[0] += count
        stats[1] += sub_r * count
        stats[2] += sub_r * sub_r * count

    def _ratio(self):
        return self.num_dirty / self.num_meter if self.num_meter else 0.0

    def _similarity(self, level):
        stats = self.level_stats.get(level)
        if stats is None or stats[0] < 2:
            return math.inf          # paper initializes S_l to +infinity
        count, total, sq_total = stats
        ratio = self._ratio()
        variance = (sq_total - 2 * ratio * total + count * ratio * ratio)
        return math.sqrt(max(variance, 0.0) / (count - 1))

    # -- subR bookkeeping (updateAncestor / updateDecendent) ------------
    def _resolve(self, node, sub_r):
        node.subR = sub_r
        node.resolved = True
        self._record(node.level, sub_r)
        parent = node.parent
        while (parent is not None and not parent.resolved
               and parent.lchild.resolved and parent.rchild.resolved):
            left, right = parent.lchild, parent.rchild
            parent.subR = (left.subR * left.n_leaves +
                           right.subR * right.n_leaves) / parent.n_leaves
            parent.resolved = True
            self._record(parent.level, parent.subR)
            parent = parent.parent

    def _resolve_clean_internal(self, node):
        # one clean probe accounts for the whole subtree; its unprobed
        # descendants enter the level statistics with subR = 0
        self.num_meter += node.n_leaves
        level, count = node.level + 1, 2
        while level < self.tree.leaf_level:
            self._record(level, 0.0, count)
            count *= 2
            level += 1
        self._resolve(node, 0.0)

    # -- jump decision ---------------------------------------------------
    def _decide_jump(self, node):
        distance = self.tree.leaf_level - node.level
        if distance <= 1:
            return 0
        ratio = self._ratio()
        if ratio <= 0.0 or ratio < self.jump_threshold:
            return 0
        similarity = self._similarity(node.level)
        rule = self.jump_rule
        if rule == "original":
            # Table V: jump only when the level looks uniform (S_l < R),
            # deeper the more uniform it is.  S_l stays high under
            # clustering, so jumps are suppressed exactly where high-gamma
            # scenarios need them -> ATI stops beating scanning near g~0.4.
            if not math.isfinite(similarity) or similarity / ratio >= 1.0:
                return 0
            depth = math.ceil(distance * (1.0 - similarity / ratio))
        elif rule == "dirtiness":
            # dive toward the leaves in proportion to how dirty we are,
            # ignoring S_l -> keeps jumping in dense (clustered) regions
            # and pushes the below-scanning crossover out to g~0.55.
            depth = math.ceil(distance * ratio)
        elif rule == "aggressive":
            # take whichever of the two rules jumps deeper
            damp = (0.0 if not math.isfinite(similarity)
                    else max(0.0, 1.0 - similarity / ratio))
            depth = math.ceil(distance * max(damp, ratio))
        else:
            raise ValueError(f"unknown jump_rule {rule!r}")
        return max(1, min(depth, distance))

    def _descendants_at(self, node, depth):
        target = node.level + depth
        found = []

        def collect(current):
            if current.level == target or current.is_leaf:
                found.append(current)
            else:
                collect(current.lchild)
                collect(current.rchild)

        collect(node.lchild)
        collect(node.rchild)
        return found

    # -- traversal ---------------------------------------------------------
    def _handle_clean(self, node):
        if node.is_leaf:
            self.num_meter += 1
            self._resolve(node, 0.0)
        else:
            self._resolve_clean_internal(node)

    def _visit(self, node):
        if self.prober.probe(node) == DIRTY:
            self._expand_dirty(node)
        else:
            self._handle_clean(node)

    def _expand_dirty(self, node):
        """node is known dirty, whether probed or inferred."""
        if node.is_leaf:
            self.num_meter += 1
            self.num_dirty += 1
            self.q.append(node)
            self._resolve(node, 1.0)
            return
        depth = self._decide_jump(node)
        if depth >= 1:
            for descendant in self._descendants_at(node, depth):
                self._visit(descendant)
        elif self.prober.probe(node.lchild) == DIRTY:
            self._expand_dirty(node.lchild)
            if self.prober.probe(node.rchild) == DIRTY:
                self._expand_dirty(node.rchild)
            else:
                self._handle_clean(node.rchild)
        else:
            self._handle_clean(node.lchild)
            self._expand_dirty(node.rchild)   # inferred dirty: no probe spent


def ati(tree):
    """Adaptive Tree Inspection (Table V), paper-faithful defaults."""
    return _AdaptiveInspection(tree).run()


JUMP_RULES = ("original", "dirtiness", "aggressive")


def make_ati(jump_rule="original", jump_threshold=None):
    """Build an ATI algorithm callable with a chosen jump policy.

    `jump_rule` selects how the jump depth D is computed (see
    `_AdaptiveInspection._decide_jump`); `jump_threshold` overrides the
    minimum running dirty ratio R below which no jump fires (default
    0.13, the Lemma-4 value).  `make_ati()` with no arguments is exactly
    `ati`.  The interactive simulator uses this to explore how far ATI's
    below-scanning range can be pushed under clustered placements.
    """
    def algo(tree):
        return _AdaptiveInspection(tree, jump_rule, jump_threshold).run()
    return algo


STATIC_ALGOS = {
    "Scanning": scanning,
    "BI_v1": bi_v1,
    "BI_v2": bi_v2,
    "ATI": ati,
}
