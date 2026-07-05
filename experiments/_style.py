"""Shared plotting style and helpers for the replication figures.

Categorical palette validated for CVD separation and lightness/chroma
(dataviz six-checks, light surface); every series also carries a
distinct marker shape so identity never rides on color alone.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "results"

# series -> (color, marker, linestyle); fixed assignment, never cycled
SERIES_STYLE = {
    "Scanning":         ("#0072B2", ".", ":"),
    "BI_v1":            ("#009E73", "o", "-"),
    "BI_v2":            ("#D55E00", "*", "-"),
    "ATI":              ("#CC79A7", "s", "-"),
    "Dynamic Scanning": ("#0072B2", "+", "-"),
    "DBI_v1":           ("#009E73", "o", "-"),
    "DBI_v2":           ("#D55E00", "*", "-"),
    "Dynamic ATI":      ("#CC79A7", "s", "-"),
}


def new_axes(xlabel, ylabel, title):
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=150)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.tick_params(labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    return fig, ax


def plot_series(ax, name, x, y):
    color, marker, linestyle = SERIES_STYLE[name]
    open_marker = marker in ("o", "s")
    ax.plot(x, y, label=name, color=color, marker=marker,
            linestyle=linestyle, linewidth=2, alpha=0.9,
            markersize=9 if marker == "*" else 6.5,
            markerfacecolor="none" if open_marker else color,
            markeredgecolor=color, markeredgewidth=1.6 if open_marker else 1)


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
