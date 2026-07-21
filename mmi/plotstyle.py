"""Shared chart styling for the experiment scripts and the simulator.

Categorical palette validated for CVD separation and lightness/chroma
on a light surface; every series also carries a distinct marker shape
so identity never rides on color alone.  This module only styles Axes
objects, so it works under any matplotlib backend (Agg or TkAgg).
"""

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

BOUND_LABEL = "log2 C(n,m) floor"


def style_axes(ax, xlabel, ylabel, title):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.grid(True, linewidth=0.4, alpha=0.35)
    ax.tick_params(labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def plot_series(ax, name, x, y):
    color, marker, linestyle = SERIES_STYLE[name]
    open_marker = marker in ("o", "s")
    ax.plot(x, y, label=name, color=color, marker=marker,
            linestyle=linestyle, linewidth=2, alpha=0.9,
            markersize=9 if marker == "*" else 6.5,
            markerfacecolor="none" if open_marker else color,
            markeredgecolor=color, markeredgewidth=1.6 if open_marker else 1)


def plot_bound(ax, x, y):
    ax.plot(x, y, label=BOUND_LABEL, color="#565452", linestyle="--",
            linewidth=1.6, alpha=0.85)
