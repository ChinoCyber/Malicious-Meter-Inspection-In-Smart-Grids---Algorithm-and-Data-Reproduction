"""Replicates Fig. 11: dynamic inspection with n = 128 and m = 24 fixed,
examining how the number of rounds r (2..m) affects total steps N_S.
All four algorithms see identical random scenarios at every point.
"""

import random

from _style import finish, new_axes, plot_series, write_csv

from mmi import run_dynamic, DYNAMIC_ALGOS

N = 128
M = 24
REPEATS = 50
SEED = 303
ROUNDS = list(range(2, M + 1))


def main():
    means = {name: [] for name in DYNAMIC_ALGOS}
    for r in ROUNDS:
        totals = {name: 0 for name in DYNAMIC_ALGOS}
        for repeat in range(REPEATS):
            scenario_seed = SEED + 1000 * repeat + r
            for name, algo in DYNAMIC_ALGOS.items():
                rng = random.Random(scenario_seed)
                totals[name] += run_dynamic(N, M, r, algo, rng)
        for name in DYNAMIC_ALGOS:
            means[name].append(totals[name] / REPEATS)
        print(f"r={r:2d}  " +
              "  ".join(f"{name}={means[name][-1]:.0f}" for name in means))

    write_csv("fig11_rounds.csv",
              ["rounds"] + list(DYNAMIC_ALGOS),
              [[r] + [means[name][i] for name in DYNAMIC_ALGOS]
               for i, r in enumerate(ROUNDS)])

    fig, ax = new_axes("Number of rounds", "N_S - steps",
                       f"Dynamic inspection, n = {N}, m = {M} "
                       f"(paper Fig. 11, avg of {REPEATS} runs)")
    for name in DYNAMIC_ALGOS:
        plot_series(ax, name, ROUNDS, means[name])
    finish(fig, ax, "fig11_rounds.png")


if __name__ == "__main__":
    main()
