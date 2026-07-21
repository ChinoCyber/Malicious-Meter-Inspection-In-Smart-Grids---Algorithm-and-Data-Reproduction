"""Interactive MMI simulation environment.

Run:  python simulator.py            (opens the GUI)
      python simulator.py --selftest (headless smoke test, no window)

A tkinter front end over the verified mmi package: pick a dirty-meter
placement model (uniform / clustered / spread), the number of trials,
the γ resolution, n, the algorithms to compare, and optionally overlay
the information-theoretic floor log2 C(n, m).  Every run draws the
curves and saves a parameter-stamped PNG + CSV into results/.
"""

import argparse
import csv
import queue
import random
import threading
import time
from pathlib import Path

from mmi import (assign_dirty, build_inspection_tree, make_ati, JUMP_RULES,
                 STATIC_ALGOS)
from mmi.bounds import information_lower_bound
from mmi.placement import PLACEMENTS
from mmi.plotstyle import plot_bound, plot_series, style_axes

RESULTS_DIR = Path(__file__).resolve().parent / "results"
GAMMA_STEPS = (0.01, 0.02, 0.05, 0.10)


# --------------------------------------------------------------------------
# simulation core (GUI-independent)
# --------------------------------------------------------------------------

def sweep(config, progress=None, cancelled=None):
    """Run the static γ sweep described by `config` (a dict).

    Returns (gammas, means, bound) where means maps algorithm name to a
    list of average N_S values.  `progress(fraction)` is called as work
    completes; `cancelled()` returning True aborts and returns None.
    """
    n = config["n"]
    step = config["gamma_step"]
    trials = config["trials"]
    seed = config["seed"]
    jump_rule = config.get("jump_rule", "original")
    jump_threshold = config.get("jump_threshold", None)
    algos = {}
    for name in config["algorithms"]:
        if name == "ATI":
            # honour the configured jump policy; default reproduces Table V
            algos[name] = make_ati(jump_rule, jump_threshold)
        else:
            algos[name] = STATIC_ALGOS[name]
    place = PLACEMENTS[config["placement"]]
    block = config.get("block_size", 8)

    count = int(round(1.0 / step))
    gammas = [round(step * k, 4) for k in range(1, count + 1)]
    means = {name: [] for name in algos}
    total_work = len(gammas) * trials
    done = 0
    for gamma_index, gamma in enumerate(gammas):
        m = max(1, round(gamma * n))
        totals = dict.fromkeys(algos, 0)
        for trial in range(trials):
            if cancelled is not None and cancelled():
                return None
            rng = random.Random(seed + 10_000 * gamma_index + trial)
            tree = build_inspection_tree(range(n), rng)
            dirty = place(tree, m, rng, block_size=block)
            for name, algo in algos.items():
                assign_dirty(tree, dirty)
                _, steps = algo(tree)
                totals[name] += steps
            done += 1
            if progress is not None:
                progress(done / total_work)
        for name in algos:
            means[name].append(totals[name] / trials)
    bound = [information_lower_bound(n, max(1, round(g * n))) for g in gammas]
    return gammas, means, bound


def describe(config):
    placement = config["placement"]
    if placement == "clustered":
        placement += f"(block={config.get('block_size', 8)})"
    text = (f"n={config['n']}, {placement}, trials={config['trials']}, "
            f"γ step={config['gamma_step']}, seed={config['seed']}")
    rule = config.get("jump_rule", "original")
    threshold = config.get("jump_threshold", 0.13)
    if "ATI" in config.get("algorithms", []) and (rule != "original"
                                                  or threshold != 0.13):
        text += f", ATI jump={rule}@R≥{threshold:g}"
    return text


def save_run(config, gammas, means, bound):
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    placement = config["placement"]
    if placement == "clustered":
        placement += f"-b{config.get('block_size', 8)}"
    base = f"sim_{placement}_n{config['n']}_t{config['trials']}_{stamp}"
    names = list(means)
    csv_path = RESULTS_DIR / f"{base}.csv"
    with open(csv_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gamma"] + names + ["lower_bound"])
        for i, gamma in enumerate(gammas):
            writer.writerow([gamma] + [means[name][i] for name in names]
                            + [round(bound[i], 1)])
    return base, csv_path


def draw(ax, config, gammas, means, bound):
    ax.clear()
    style_axes(ax, "γ - the ratio of dirty meters", "N_S - steps",
               f"Static MMI inspection — {describe(config)}")
    for name in means:
        plot_series(ax, name, gammas, means[name])
    if config.get("show_bound"):
        plot_bound(ax, gammas, bound)
    ax.set_xlim(0, 1.05)
    ax.legend(fontsize=9, framealpha=0.9)


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

def launch_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    root = tk.Tk()
    root.title("MMI Simulation Lab — Xiao, Xiao & Du (IEEE TSG 2013)")
    root.geometry("1120x640")

    panel = ttk.Frame(root, padding=10)
    panel.pack(side=tk.LEFT, fill=tk.Y)
    plot_frame = ttk.Frame(root)
    plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    figure = Figure(figsize=(7.2, 5.0), dpi=110)
    ax = figure.add_subplot(111)
    style_axes(ax, "γ - the ratio of dirty meters", "N_S - steps",
               "Configure a scenario and press Run")
    canvas = FigureCanvasTkAgg(figure, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    row = 0

    def label(text):
        nonlocal row
        ttk.Label(panel, text=text, font=("Segoe UI", 9, "bold")).grid(
            column=0, row=row, columnspan=2, sticky="w", pady=(10, 2))
        row += 1

    label("Meters (n)")
    n_var = tk.StringVar(value="512")
    ttk.Combobox(panel, textvariable=n_var, width=10,
                 values=("64", "128", "256", "512", "1024")).grid(
        column=0, row=row, columnspan=2, sticky="w")
    row += 1

    label("Dirty-meter placement")
    placement_var = tk.StringVar(value="uniform")
    for value, text in (("uniform", "Uniform random"),
                        ("clustered", "Clustered (contiguous blocks)"),
                        ("spread", "Spread / anti-clustered")):
        ttk.Radiobutton(panel, text=text, value=value,
                        variable=placement_var).grid(
            column=0, row=row, columnspan=2, sticky="w")
        row += 1

    ttk.Label(panel, text="Cluster block size").grid(
        column=0, row=row, sticky="w")
    block_var = tk.StringVar(value="8")
    block_spin = ttk.Spinbox(panel, from_=2, to=512, width=8,
                             textvariable=block_var)
    block_spin.grid(column=1, row=row, sticky="w")
    row += 1

    label("Trials per γ point")
    trials_var = tk.StringVar(value="30")
    ttk.Spinbox(panel, from_=1, to=500, width=8,
                textvariable=trials_var).grid(column=0, row=row, sticky="w")
    row += 1

    label("γ resolution (step)")
    step_var = tk.StringVar(value="0.05")
    ttk.Combobox(panel, textvariable=step_var, width=10,
                 values=tuple(str(s) for s in GAMMA_STEPS)).grid(
        column=0, row=row, columnspan=2, sticky="w")
    row += 1

    label("Algorithms")
    algo_vars = {}
    for name in STATIC_ALGOS:
        var = tk.BooleanVar(value=True)
        algo_vars[name] = var
        ttk.Checkbutton(panel, text=name, variable=var).grid(
            column=0, row=row, columnspan=2, sticky="w")
        row += 1

    label("ATI jump rule")
    jump_rule_var = tk.StringVar(value="original")
    ttk.Combobox(panel, textvariable=jump_rule_var, width=14,
                 state="readonly", values=JUMP_RULES).grid(
        column=0, row=row, columnspan=2, sticky="w")
    row += 1
    ttk.Label(panel, text="(dirtiness/aggressive push the\n"
                          "below-scanning range past γ≈0.5)",
              font=("Segoe UI", 8), foreground="#555").grid(
        column=0, row=row, columnspan=2, sticky="w")
    row += 1

    ttk.Label(panel, text="ATI jump threshold (R)").grid(
        column=0, row=row, sticky="w")
    threshold_var = tk.StringVar(value="0.13")
    ttk.Entry(panel, textvariable=threshold_var, width=8).grid(
        column=1, row=row, sticky="w")
    row += 1

    bound_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(panel, text="Overlay log2 C(n,m) floor",
                    variable=bound_var).grid(
        column=0, row=row, columnspan=2, sticky="w", pady=(10, 0))
    row += 1

    ttk.Label(panel, text="Seed").grid(column=0, row=row, sticky="w",
                                       pady=(10, 0))
    seed_var = tk.StringVar(value="42")
    ttk.Entry(panel, textvariable=seed_var, width=8).grid(
        column=1, row=row, sticky="w", pady=(10, 0))
    row += 1

    run_button = ttk.Button(panel, text="Run simulation")
    run_button.grid(column=0, row=row, columnspan=2, sticky="we",
                    pady=(14, 4))
    row += 1
    progress = ttk.Progressbar(panel, maximum=1.0)
    progress.grid(column=0, row=row, columnspan=2, sticky="we")
    row += 1
    status_var = tk.StringVar(value="Ready.")
    ttk.Label(panel, textvariable=status_var, wraplength=220).grid(
        column=0, row=row, columnspan=2, sticky="w", pady=(4, 0))

    events = queue.Queue()
    state = {"running": False}

    def read_config():
        try:
            config = {
                "n": int(n_var.get()),
                "placement": placement_var.get(),
                "block_size": int(block_var.get()),
                "trials": int(trials_var.get()),
                "gamma_step": float(step_var.get()),
                "seed": int(seed_var.get()),
                "show_bound": bound_var.get(),
                "jump_rule": jump_rule_var.get(),
                "jump_threshold": float(threshold_var.get()),
                "algorithms": [name for name, var in algo_vars.items()
                               if var.get()],
            }
        except ValueError as exc:
            raise ValueError(f"Bad input: {exc}") from exc
        if config["n"] < 2:
            raise ValueError("n must be at least 2")
        if not 0 < config["gamma_step"] <= 0.5:
            raise ValueError("γ step must be in (0, 0.5]")
        if not 0.0 <= config["jump_threshold"] <= 1.0:
            raise ValueError("ATI jump threshold must be in [0, 1]")
        if not config["algorithms"]:
            raise ValueError("select at least one algorithm")
        return config

    def worker(config):
        try:
            result = sweep(config,
                           progress=lambda f: events.put(("progress", f)))
            events.put(("done", (config, result)))
        except Exception as exc:                    # surface, don't hang
            events.put(("error", str(exc)))

    def on_run():
        if state["running"]:
            return
        try:
            config = read_config()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        state["running"] = True
        run_button.state(["disabled"])
        progress["value"] = 0
        status_var.set("Running: " + describe(config))
        threading.Thread(target=worker, args=(config,), daemon=True).start()

    def poll():
        try:
            while True:
                kind, payload = events.get_nowait()
                if kind == "progress":
                    progress["value"] = payload
                elif kind == "error":
                    state["running"] = False
                    run_button.state(["!disabled"])
                    status_var.set("Failed: " + payload)
                elif kind == "done":
                    config, result = payload
                    gammas, means, bound = result
                    draw(ax, config, gammas, means, bound)
                    canvas.draw()
                    base, _ = save_run(config, gammas, means, bound)
                    figure.savefig(RESULTS_DIR / f"{base}.png", dpi=150,
                                   bbox_inches="tight")
                    state["running"] = False
                    run_button.state(["!disabled"])
                    progress["value"] = 1.0
                    status_var.set(f"Done. Saved results/{base}.png/.csv")
        except queue.Empty:
            pass
        root.after(100, poll)

    run_button.configure(command=on_run)
    poll()
    root.mainloop()


# --------------------------------------------------------------------------

def selftest():
    """Headless smoke test of the simulation core and file outputs."""
    config = {"n": 64, "placement": "clustered", "block_size": 4,
              "trials": 3, "gamma_step": 0.25, "seed": 1,
              "show_bound": True, "algorithms": list(STATIC_ALGOS)}
    result = sweep(config)
    assert result is not None
    gammas, means, bound = result
    assert len(gammas) == 4 and all(len(v) == 4 for v in means.values())
    assert all(b >= 0 for b in bound)
    for placement in PLACEMENTS:
        config2 = dict(config, placement=placement, gamma_step=0.5, trials=2)
        assert sweep(config2) is not None

    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    figure = Figure(figsize=(7.2, 5.0))
    ax = figure.add_subplot(111)
    draw(ax, config, gammas, means, bound)
    base, csv_path = save_run(config, gammas, means, bound)
    figure.savefig(RESULTS_DIR / f"{base}.png", dpi=150, bbox_inches="tight")
    assert csv_path.exists()
    print(f"selftest ok — wrote results/{base}.png/.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true",
                        help="run a headless smoke test and exit")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        launch_gui()
