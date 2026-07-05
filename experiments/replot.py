"""Regenerate the three figures from the CSVs in results/ without
re-running the simulations (useful after style tweaks)."""

import csv

from _style import RESULTS_DIR, finish, new_axes, plot_series

FIGURES = [
    ("fig9_static.csv", "fig9_static.png",
     "γ - the ratio of dirty meters", "N_S - steps",
     "Static inspection, n = 512 (paper Fig. 9, avg of 30 runs)"),
    ("fig10_dynamic.csv", "fig10_dynamic.png",
     "γ - the ratio of dirty meters", "N_S - steps",
     "Dynamic inspection, n = 128 (paper Fig. 10, avg over r = 2..m, 20 tests)"),
    ("fig11_rounds.csv", "fig11_rounds.png",
     "Number of rounds", "N_S - steps",
     "Dynamic inspection, n = 128, m = 24 (paper Fig. 11, avg of 50 runs)"),
]


def main():
    for csv_name, png_name, xlabel, ylabel, title in FIGURES:
        with open(RESULTS_DIR / csv_name, newline="") as handle:
            rows = list(csv.reader(handle))
        header, data = rows[0], rows[1:]
        x = [float(row[0]) for row in data]
        fig, ax = new_axes(xlabel, ylabel, title)
        for column, name in enumerate(header[1:], start=1):
            plot_series(ax, name, x, [float(row[column]) for row in data])
        if xlabel.startswith("γ"):
            ax.set_xlim(0, 1.05)
        finish(fig, ax, png_name)


if __name__ == "__main__":
    main()
