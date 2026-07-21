"""Plotting helpers for the batch experiment scripts (headless Agg
backend).  Visual styling lives in mmi.plotstyle so the interactive
simulator shares it."""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from mmi.plotstyle import SERIES_STYLE, plot_series, style_axes  # noqa: E402,F401

RESULTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "results"


def new_axes(xlabel, ylabel, title):
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=150)
    style_axes(ax, xlabel, ylabel, title)
    return fig, ax


def finish(fig, ax, png_name):
    ax.legend(fontsize=9, framealpha=0.9)
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / png_name
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"saved {out}")


def write_csv(csv_name, header, rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / csv_name
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"saved {out}")
