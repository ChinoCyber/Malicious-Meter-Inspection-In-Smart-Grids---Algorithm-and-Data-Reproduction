"""Replicates Fig. 10: dynamic inspection, n = 128.

For each dirty-meter ratio γ (m = γ·n eventual dirty meters), the paper
fixes m and runs the inspection for every number of rounds r from 2 to
m, then averages 20 tests (Sec. VI-B).  To keep the runtime reasonable
the r sweep is subsampled with an even stride when m is large (at most
MAX_R_VALUES values of r per γ), which leaves the average essentially
unchanged; all four algorithms see identical random scenarios.
"""

import random

from _style import finish, new_axes, plot_series, write_csv

from mmi import run_dynamic, DYNAMIC_ALGOS

N = 128
REPEATS = 20
SEED = 202
MAX_R_VALUES = 25
GAMMAS = [round(0.1 * k, 1) for k in range(1, 11)]   # 0.1 .. 1.0


def r_values(m):
    stride = max(1, (m - 1) // MAX_R_VALUES)
    return list(range(2, m + 1, stride))


def main():
    means = {name: [] for name in DYNAMIC_ALGOS}
    for gamma_index, gamma in enumerate(GAMMAS):
        m = round(gamma * N)
        rounds = r_values(m)
        totals = {name: 0 for name in DYNAMIC_ALGOS}
        samples = 0
        for repeat in range(REPEATS):
            for r in rounds:
                scenario_seed = SEED + 100_000 * gamma_index + 1000 * repeat + r
                for name, algo in DYNAMIC_ALGOS.items():
                    rng = random.Random(scenario_seed)
                    totals[name] += run_dynamic(N, m, r, algo, rng)
                samples += 1
        for name in DYNAMIC_ALGOS:
            means[name].append(totals[name] / samples)
        print(f"gamma={gamma:.1f} (m={m}, {len(rounds)} r-values)  " +
              "  ".join(f"{name}={means[name][-1]:.0f}" for name in means))

    write_csv("fig10_dynamic.csv",
              ["gamma"] + list(DYNAMIC_ALGOS),
              [[gamma] + [means[name][i] for name in DYNAMIC_ALGOS]
               for i, gamma in enumerate(GAMMAS)])

    fig, ax = new_axes("γ - the ratio of dirty meters", "N_S - steps",
                       f"Dynamic inspection, n = {N} (paper Fig. 10, "
                       f"avg over r = 2..m, {REPEATS} tests)")
    for name in DYNAMIC_ALGOS:
        plot_series(ax, name, GAMMAS, means[name])
    ax.set_xlim(0, 1.05)
    finish(fig, ax, "fig10_dynamic.png")


if __name__ == "__main__":
    main()
