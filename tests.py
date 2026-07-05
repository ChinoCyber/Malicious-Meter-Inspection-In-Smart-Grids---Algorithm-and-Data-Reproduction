"""Sanity checks for the MMI replication (run: python tests.py)."""

import math
import random

from mmi import (assign_dirty, build_inspection_tree, run_dynamic,
                 split_into_rounds, STATIC_ALGOS, DYNAMIC_ALGOS,
                 scanning, bi_v1, bi_v2)


def check_tree_structure():
    rng = random.Random(0)
    for n in (1, 2, 7, 8, 33, 100, 512):
        tree = build_inspection_tree(range(n), rng)
        assert tree.n == n
        assert len(tree.postorder) == 2 * n - 1, f"tree size != 2n-1 for n={n}"
        assert sorted(leaf.meter_id for leaf in tree.leaves) == list(range(n))
    print("tree structure ok (size 2n-1, n leaves, all meters placed)")


def check_all_algorithms_exact():
    rng = random.Random(1)
    for n in (8, 33, 100, 512):
        for trial in range(10):
            m = rng.randint(0, n)
            tree = build_inspection_tree(range(n), rng)
            dirty = set(rng.sample(range(n), m))
            for name, algo in STATIC_ALGOS.items():
                assign_dirty(tree, dirty)
                q, _ = algo(tree)
                found = {leaf.meter_id for leaf in q}
                assert found == dirty, f"{name} wrong on n={n}, m={m}"
    print("all static algorithms recover the exact planted dirty set")


def check_scanning_steps():
    rng = random.Random(2)
    for n in (8, 100, 512):
        tree = build_inspection_tree(range(n), rng)
        assign_dirty(tree, rng.sample(range(n), n // 3))
        _, steps = scanning(tree)
        assert steps == n, f"scanning N_S != n for n={n}"
    print("scanning uses exactly n steps")


def check_bi_bounds():
    rng = random.Random(3)
    # Theory 1: m = 1 on a complete tree
    for n in (32, 64, 512):
        height = math.ceil(math.log2(n))
        for trial in range(30):
            tree = build_inspection_tree(range(n), rng)
            assign_dirty(tree, [rng.randrange(n)])
            _, steps = bi_v1(tree)
            assert height + 1 <= steps <= 2 * height + 1, \
                f"BI_v1 m=1 bound violated: n={n}, N_S={steps}"
    # Lemma 1: N_S <= 2n - 1 always, and BI_v2 never worse than BI_v1
    for trial in range(30):
        n = rng.randint(4, 300)
        m = rng.randint(1, n)
        tree = build_inspection_tree(range(n), rng)
        dirty = rng.sample(range(n), m)
        assign_dirty(tree, dirty)
        _, steps_v1 = bi_v1(tree)
        assign_dirty(tree, dirty)
        _, steps_v2 = bi_v2(tree)
        assert steps_v1 <= 2 * n - 1
        assert steps_v2 <= steps_v1, "BI_v2 worse than BI_v1"
    print("BI_v1 bounds hold (Theory 1, Lemma 1); BI_v2 <= BI_v1")


def check_dynamic():
    rng = random.Random(4)
    assert sum(split_into_rounds(24, 6, rng)) == 24
    assert all(x >= 1 for x in split_into_rounds(24, 24, rng))
    for algo in DYNAMIC_ALGOS.values():
        # run_dynamic asserts internally that every batch is fully found
        steps = run_dynamic(128, 24, 6, algo, random.Random(5))
        assert steps > 0
    # D-Scanning with x_i = 1 per round matches Table IX exactly:
    # N_S = r*n - sum_{l=1}^{r-1} x_l*(r-l)
    n, m = 64, 5
    steps = run_dynamic(n, m, m, scanning, random.Random(6))
    expected = m * n - sum(1 * (m - l) for l in range(1, m))
    assert steps == expected, f"D-Scanning {steps} != Table IX {expected}"
    print("dynamic driver ok (batches found each round, Table IX accounting)")


if __name__ == "__main__":
    check_tree_structure()
    check_all_algorithms_exact()
    check_scanning_steps()
    check_bi_bounds()
    check_dynamic()
    print("ALL CHECKS PASSED")
