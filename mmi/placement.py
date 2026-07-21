"""Dirty-meter placement models.

Placements operate in *leaf-position* space (the left-to-right order of
the inspection tree's leaves), because that is what determines how many
subtrees come out clean.  Each model takes the tree, the number of
dirty meters m, and an RNG, and returns the meter ids to mark dirty.

  uniform    every C(n, m) arrangement equally likely (the paper's
             stated setup for Fig. 9)
  clustered  dirty meters fill random contiguous blocks of leaf
             positions -> clean subtrees are common, tree methods win
  spread     dirty meters at (near-)evenly spaced leaf positions ->
             almost every subtree is contaminated, the adversarial
             anti-clustered case (cf. the whole-tree depairing worst
             case of Lemma 3/4)
"""


def uniform_placement(tree, m, rng, **_):
    positions = rng.sample(range(tree.n), m)
    return [tree.leaves[p].meter_id for p in positions]


def clustered_placement(tree, m, rng, block_size=8, **_):
    n = tree.n
    taken = set()
    while len(taken) < m:
        size = min(max(1, block_size), m - len(taken))
        start = rng.randrange(n - size + 1)
        taken |= set(range(start, start + size))
    return [tree.leaves[p].meter_id for p in taken]


def spread_placement(tree, m, rng, **_):
    n = tree.n
    offset = rng.randrange(n)
    # floor(i*n/m) is strictly increasing and < n, so positions are distinct
    positions = {(offset + (i * n) // m) % n for i in range(m)}
    return [tree.leaves[p].meter_id for p in sorted(positions)]


PLACEMENTS = {
    "uniform": uniform_placement,
    "clustered": clustered_placement,
    "spread": spread_placement,
}
