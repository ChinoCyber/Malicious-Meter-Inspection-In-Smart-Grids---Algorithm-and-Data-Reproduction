"""Replicates Fig. 9: static inspection, n = 512, N_I = 1.

Dirty meters are deployed uniformly at random; every point is the
average of 30 repeats (the paper's setup, Sec. VI-A).  Compares
Scanning, BI_v1, BI_v2 and ATI as the dirty-meter ratio grows.
"""

import random

from _style import finish, new_axes, plot_series, write_csv

from mmi import assign_dirty, build_inspection_tree, STATIC_ALGOS

N = 512
REPEATS = 30
SEED = 42
GAMMAS = [round(0.05 * k, 2) for k in range(1, 21)]   # 0.05 .. 1.0


def main():
    means = {name: [] for name in STATIC_ALGOS}
    for gamma_index, gamma in enumerate(GAMMAS):
        m = round(gamma * N)
        totals = {name: 0 for name in STATIC_ALGOS}
        for repeat in range(REPEATS):
            rng = random.Random(SEED + 1000 * gamma_index + repeat)
            tree = build_inspection_tree(range(N), rng)
            dirty = rng.sample(range(N), m)
            for name, algo in STATIC_ALGOS.items():
                assign_dirty(tree, dirty)   # also resets ATI node state
                _, steps = algo(tree)
                totals[name] += steps
        for name in STATIC_ALGOS:
            means[name].append(totals[name] / REPEATS)
        print(f"gamma={gamma:.2f}  " +
              "  ".join(f"{name}={means[name][-1]:.1f}" for name in means))

    write_csv("fig9_static.csv",
              ["gamma"] + list(STATIC_ALGOS),
              [[gamma] + [means[name][i] for name in STATIC_ALGOS]
               for i, gamma in enumerate(GAMMAS)])

    fig, ax = new_axes("γ - the ratio of dirty meters", "N_S - steps",
                       f"Static inspection, n = {N} (paper Fig. 9, "
                       f"avg of {REPEATS} runs)")
    for name in STATIC_ALGOS:
        plot_series(ax, name, GAMMAS, means[name])
    ax.set_xlim(0, 1.02)
    finish(fig, ax, "fig9_static.png")


if __name__ == "__main__":
    main()
