"""Dynamic inspection (Sec. V): malicious meters keep emerging while the
inspection runs, so it proceeds in rounds.  The m eventual dirty meters
are split into r batches; batch i has emerged by the time round i
starts.  Each round inspects the remaining meters with one of the
static schemes (D-Scanning = scanning per round, DBI = tree inspection
per round with the tree rebuilt from the remaining meters, D-ATI
likewise with the adaptive scheme).  Detected meters are removed from
the user set immediately (the paper's assumption), and the free
head-inspector query after a round decides whether another round is
needed.  Total N_S is the sum of the rounds' probing steps, matching
the round accounting of Table IX.
"""

from .static_algos import scanning, bi_v1, bi_v2, ati
from .tree import assign_dirty, build_inspection_tree


def split_into_rounds(m, r, rng):
    """Random composition of m dirty meters into r non-empty batches."""
    r = max(1, min(r, m))
    cuts = sorted(rng.sample(range(1, m), r - 1))
    bounds = [0] + cuts + [m]
    return [bounds[i + 1] - bounds[i] for i in range(r)]


def run_dynamic(n, m, r, algorithm, rng):
    """Simulate one r-round dynamic inspection; return total steps N_S."""
    meters = list(range(n))
    eventual_dirty = rng.sample(meters, m)
    batches = split_into_rounds(m, r, rng)
    remaining = meters
    total_steps = 0
    consumed = 0
    for batch_size in batches:
        batch = set(eventual_dirty[consumed:consumed + batch_size])
        consumed += batch_size
        tree = build_inspection_tree(remaining, rng)
        assign_dirty(tree, batch)
        found, steps = algorithm(tree)
        total_steps += steps
        found_ids = {leaf.meter_id for leaf in found}
        assert found_ids == batch, "inspection missed emerged dirty meters"
        remaining = [meter for meter in remaining if meter not in found_ids]
    return total_steps


DYNAMIC_ALGOS = {
    "Dynamic Scanning": scanning,
    "DBI_v1": bi_v1,
    "DBI_v2": bi_v2,
    "Dynamic ATI": ati,
}
