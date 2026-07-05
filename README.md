# MMI Algorithms — Replication

Replication of the simulation results of:

> Z. Xiao, Y. Xiao, and D. H.-C. Du, "Exploring Malicious Meter Inspection in
> Neighborhood Area Smart Grids," *IEEE Transactions on Smart Grid*, vol. 4,
> no. 1, pp. 214–226, March 2013.

The paper models an apartment building's `n` smart meters as the leaves of a
binary **inspection tree**. Probing a node costs one step: an inspector
compares its own reading with the sum reported by the meters in its subtree,
so a node reads *dirty* iff its subtree contains at least one malicious meter.
Algorithms are compared by `N_S`, the number of probing steps needed to
identify every malicious meter.

## Layout

```
mmi/
  tree.py          inspection-tree model, PullDown build, probe oracle
  static_algos.py  Scanning, BI_v1 (Table III), BI_v2 (Table IV), ATI (Table V)
  dynamic_algos.py r-round dynamic driver (Sec. V): D-Scanning, DBI_v1/v2, D-ATI
experiments/
  fig9_static.py   paper Fig. 9  — static, n = 512, 30 repeats
  fig10_dynamic.py paper Fig. 10 — dynamic, n = 128, avg over r = 2..m, 20 tests
  fig11_rounds.py  paper Fig. 11 — dynamic, n = 128, m = 24, r = 2..24
results/           generated PNGs and CSVs
tests.py           sanity checks against the paper's theorems
```

## Run

```
pip install -r requirements.txt
python tests.py
python experiments/fig9_static.py
python experiments/fig10_dynamic.py
python experiments/fig11_rounds.py
```

Figures and raw data land in `results/`. All experiments are seeded and
reproducible; in the dynamic experiments all four algorithms are run on
identical random scenarios.

## Interpretation choices

The paper's pseudocode leaves a few details open; this replication resolves
them as follows (all documented in the docstrings):

1. **Probe oracle.** The reading-vs-threshold comparison of Table II is
   simulated as an exact test (`dirty iff the subtree holds >= 1 dirty
   meter`); probe results are cached within a round, so a node's status is
   never bought twice.
2. **ATI descent uses BI_v2's inference.** Table V descends dirty nodes like
   BI_v1, but the paper's results show ATI at or below BI_v2 everywhere —
   impossible with a literal Table V, which collapses onto BI_v1 whenever
   R < 0.13 forbids jumping. The non-jump descent therefore uses BI_v2's
   skip (a dirty node with a clean left child has a dirty right child that
   costs no probe).
3. **ATI similarity statistic.** `S_l` is the standard deviation, around the
   running ratio R, of the subtree dirty ratios known at level `l` (the
   paper's formula), tracked with per-level aggregates; a clean internal
   probe also enters its unprobed descendants as zeros (updateDecendent).
   Jump range: `D = ceil((1 - S_l/R) * dist)`, clamped to `[1, dist]`.
4. **Dynamic rounds.** The `m` eventual dirty meters are split into `r`
   non-empty random batches; batch *i* has emerged by the start of round *i*,
   detected meters are removed immediately, and the head-inspector query
   between rounds is free. With one meter per round this reproduces the
   paper's Table IX accounting exactly (checked in `tests.py`).
5. **Fig. 10 r-sweep subsampling.** The paper averages over every
   `r = 2..m`; for large `m` this replication subsamples the sweep with an
   even stride (≤ 25 values of r per γ) to keep runtime short, which leaves
   the average essentially unchanged.

## Replication outcome vs. the paper

| Result | Paper | This replication |
|---|---|---|
| Fig. 9: BI_v1 crosses scanning | γ ≈ 0.25 | γ ≈ 0.17 |
| Fig. 9: BI_v2 crosses scanning | γ ≈ 0.45 | γ ≈ 0.23 |
| Fig. 9: BI_v1 = BI_v2 = 2n−1 at γ = 1 | 1023 | 1023 |
| Fig. 9: ATI at γ = 1 | ≈ 580 | ≈ 543 |
| Fig. 10: D-Scanning at γ = 1 | ≈ 5700 | ≈ 4200 |
| Fig. 10: tree-based cluster | ≤ ~1000 | ≤ ~1150 |
| Fig. 11: D-Scanning at r = 24 | ≈ 2800 | 2796 |
| Fig. 11: tree-based at r = 24 | < 500 | ≈ 270–355 |

The qualitative claims all reproduce: binary inspection wins at low dirty
ratios and loses to scanning at high ones; ATI tracks the better of the two
regimes and is the best general-purpose choice; in the dynamic case the
tree-based schemes beat scanning by a wide margin that grows with the number
of rounds. Quantitative gaps (exact crossover points, D-Scanning's Fig. 10
magnitude, ATI's mid-range dip below scanning in the paper's Fig. 9) trace to
details the paper does not fully specify — the dirty-meter arrangement, the
emergence process of dynamic batches, and the parts of Table V noted above.
