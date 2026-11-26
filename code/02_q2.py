"""Stage 2: Q2 - acoustic fidelity index, decay models and effective communication range."""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import optimize, stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CALL_TYPES, COLORS, CORR_FILES, DIST_COLS, DIST_M, FIG, RES,
                    SEED, apply_style, data_path)

rng = np.random.default_rng(SEED)
plt = apply_style()
METRICS = ["spectrogram", "amplitude_spectrum", "envelope"]
MCOL = {"spectrogram": "#4C72B0", "amplitude_spectrum": "#DD8452",
        "envelope": "#55A868"}

raw = {}
for (ct, metric), fname in CORR_FILES.items():
    raw[(ct, metric)] = pd.read_csv(data_path(fname))[DIST_COLS].to_numpy(float)

res = {"distances_m": DIST_M.tolist(), "metrics": METRICS,
       "call_types": CALL_TYPES}

# ---------------------------------------------------------------- per-cell means
cell = {}          # (ct, metric) -> mean per distance (nan if none)
counts = {}
for key, arr in raw.items():
    cell[key] = np.array([np.nanmean(arr[:, j]) for j in range(arr.shape[1])])
    counts[key] = np.array([int(np.isfinite(arr[:, j]).sum()) for j in range(arr.shape[1])])
res["cell_means"] = {f"{ct}|{m}": [round(float(v), 4) for v in cell[(ct, m)]]
                     for ct in CALL_TYPES for m in METRICS}
res["cell_counts"] = {f"{ct}|{m}": counts[(ct, m)].tolist()
                      for ct in CALL_TYPES for m in METRICS}

# ---------------------------------------------------------------- fidelity index
# equal-weight mean of the three per-distance means; weights verified by PCA
fid = {ct: np.mean([cell[(ct, m)] for m in METRICS], axis=0) for ct in CALL_TYPES}
res["fidelity"] = {ct: [round(float(v), 4) for v in fid[ct]] for ct in CALL_TYPES}

pooled = np.vstack([np.column_stack([cell[(ct, m)] for m in METRICS])
                    for ct in CALL_TYPES if True])
pooled = np.vstack([np.column_stack([cell[(ct, m)] for m in METRICS])
                    for ct in CALL_TYPES])
z = (pooled - pooled.mean(0)) / pooled.std(0)
evals, evecs = np.linalg.eigh(np.cov(z.T))
pc1 = evecs[:, -1] * np.sign(evecs[:, -1].sum())
res["pca_loadings_pc1"] = {m: round(float(v), 4) for m, v in zip(METRICS, pc1)}
res["pca_explained_pc1"] = round(float(evals[-1] / evals.sum()), 4)
res["fidelity_weights_equal"] = {m: 1 / 3 for m in METRICS}
res["fidelity_weights_pca"] = {m: round(float(abs(v) / np.abs(pc1).sum()), 4)
                               for m, v in zip(METRICS, pc1)}

# ---------------------------------------------------------------- decay models
def m_exp(d, a, b):
    return a * np.exp(-b * d)


def m_logi(d, L, k, d0):
    return L / (1.0 + np.exp(k * (d - d0)))


def m_pow(d, a, b):
    return a * np.power(d, -b)


MODELS = {
    "exponential": (m_exp, [0.95, 0.01], ([0, 1e-5], [1.2, 0.2])),
    "logistic": (m_logi, [0.95, 0.01, 60.0],
                 ([0.3, 1e-5, 1.0], [1.5, 0.3, 800.0])),
    "power": (m_pow, [1.2, 0.15], ([0, 1e-4], [3.0, 2.0])),
}


def fit_model(name, d, yv, w=None):
    f, p0, bnd = MODELS[name]
    popt, pcov = optimize.curve_fit(f, d, yv, p0=p0, bounds=bnd,
                                    sigma=None if w is None else 1 / np.sqrt(w),
                                    maxfev=200000)
    pred = f(d, *popt)
    n, k = len(d), len(popt)
    rss = float(np.sum((yv - pred) ** 2))
    aic = n * np.log(rss / n) + 2 * k
    return {"params": [round(float(v), 6) for v in popt],
            "pcov_diag": [float(v) for v in np.diag(pcov)],
            "rss": round(rss, 6), "aic": round(float(aic), 3), "k": k}


fits = {}
for ct in CALL_TYPES:
    d = DIST_M
    yv = fid[ct]
    w = np.array([min(counts[(ct, m)][j] for m in METRICS)
                  for j in range(len(d))], dtype=float)
    fits[ct] = {name: fit_model(name, d, yv, w) for name in MODELS}
    best = min(fits[ct].items(), key=lambda kv: kv[1]["aic"])[0]
    fits[ct]["_best"] = best
res["fits"] = {ct: {k: v for k, v in fits[ct].items()} for ct in CALL_TYPES}


def predict(ct, d, model=None):
    model = model or fits[ct]["_best"]
    f, _, _ = MODELS[model]
    return f(np.asarray(d, dtype=float), *fits[ct][model]["params"])


res["selected_model"] = {ct: fits[ct]["_best"] for ct in CALL_TYPES}

# ---------------------------------------------------------------- reachability + radius
THRESHOLDS = {"potential": 0.50, "recognition": 0.60, "reliable": 0.70}
res["thresholds"] = THRESHOLDS
d_grid = np.linspace(1, 2000, 200000)


def solve_radius(ct, thr, model=None, pred_fn=None):
    """Return radius in m, or None if the threshold is unreachable (> fidelity at 4 m)."""
    f = pred_fn if pred_fn is not None else (lambda dd: predict(ct, dd, model))
    if f(4.0) < thr:
        return None                     # threshold above the 4 m observation
    vals = f(d_grid)
    idx = np.where(vals <= thr)[0]
    if idx.size == 0:
        return float(d_grid[-1])        # never drops below within grid (report as > 2000 m)
    i = idx[0]
    if i == 0:
        return float(d_grid[0])
    # linear interpolation between grid points
    x0, x1 = d_grid[i - 1], d_grid[i]
    y0, y1 = vals[i - 1], vals[i]
    return float(x0 + (y0 - thr) * (x1 - x0) / (y0 - y1))


radius = {}
for ct in CALL_TYPES:
    radius[ct] = {}
    for lvl, thr in THRESHOLDS.items():
        r = solve_radius(ct, thr)
        radius[ct][lvl] = None if r is None else round(r, 1)
res["radius_m"] = radius

# ---------------------------------------------------------------- bootstrap
NB = 1000
boot = {ct: {lvl: [] for lvl in THRESHOLDS} for ct in CALL_TYPES}
for b in range(NB):
    for ct in CALL_TYPES:
        # resample rows within each distance for each metric, then rebuild the index
        yv = []
        for j in range(len(DIST_M)):
            per_metric = []
            for m in METRICS:
                col = raw[(ct, m)][:, j]
                col = col[np.isfinite(col)]
                per_metric.append(rng.choice(col, size=col.size, replace=True).mean())
            yv.append(np.mean(per_metric))
        yv = np.array(yv)
        w = np.array([min(counts[(ct, m)][j] for m in METRICS)
                      for j in range(len(DIST_M))], dtype=float)
        try:
            ft = fit_model(fits[ct]["_best"], DIST_M, yv, w)
        except Exception:
            continue
        f, _, _ = MODELS[fits[ct]["_best"]]
        pf = lambda dd, f=f, p=ft["params"]: f(np.asarray(dd, float), *p)
        for lvl, thr in THRESHOLDS.items():
            r = solve_radius(ct, thr, pred_fn=pf)
            if r is not None:
                boot[ct][lvl].append(r)

bootstrap = {}
for ct in CALL_TYPES:
    bootstrap[ct] = {}
    for lvl in THRESHOLDS:
        arr = np.array(boot[ct][lvl])
        if arr.size < 20:
            bootstrap[ct][lvl] = {"n": int(arr.size), "reachable_rate":
                                  round(float(arr.size / NB), 3)}
        else:
            bootstrap[ct][lvl] = {
                "n": int(arr.size),
                "reachable_rate": round(float(arr.size / NB), 3),
                "median": round(float(np.median(arr)), 1),
                "ci95": [round(float(np.percentile(arr, 2.5)), 1),
                         round(float(np.percentile(arr, 97.5)), 1)],
                "p05": round(float(np.percentile(arr, 5)), 1),
                "p95": round(float(np.percentile(arr, 95)), 1)}
res["bootstrap_radius"] = bootstrap

# ---------------------------------------------------------------- sensitivity
THR_GRID = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]
sens = {ct: [] for ct in CALL_TYPES}
for ct in CALL_TYPES:
    for thr in THR_GRID:
        r = solve_radius(ct, thr)
        sens[ct].append(None if r is None else round(r, 1))
res["sensitivity_thresholds"] = {"thresholds": THR_GRID, "radius_m": sens}

# ---------------------------------------------------------------- model-form uncertainty
model_form = {}
for ct in CALL_TYPES:
    model_form[ct] = {}
    for name in MODELS:
        model_form[ct][name] = {}
        for lvl, thr in THRESHOLDS.items():
            r = solve_radius(ct, thr, model=name)
            model_form[ct][name][lvl] = None if r is None else round(r, 1)
res["model_form_radius_m"] = model_form

# ---------------------------------------------------------------- robustness ranking
d_probe = [64.0, 128.0, 256.0]
rob = {ct: {f"{int(d)}m": round(float(predict(ct, d)), 4) for d in d_probe}
       for ct in CALL_TYPES}
res["fidelity_at_distance"] = rob
res["ranking_by_fidelity_256m"] = sorted(
    CALL_TYPES, key=lambda c: -rob[c]["256m"])

# ---------------------------------------------------------------- figures
# fig04: correlation vs distance, 3 metrics x 3 calls
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
for ax, m in zip(axes, METRICS):
    for ct in CALL_TYPES:
        ax.plot(DIST_M, cell[(ct, m)], marker="o", ms=4, color=COLORS[ct], label=ct)
    ax.set_xscale("log", base=2)
    ax.set_xticks(DIST_M)
    ax.set_xticklabels([str(int(v)) for v in DIST_M], fontsize=8)
    ax.set_xlabel("distance (m)")
    ax.set_title(m.replace("_", " "))
axes[0].set_ylabel("mean correlation with 1 m recording")
axes[-1].legend(title="call type", fontsize=8)
fig.suptitle("Signal degradation: correlation against propagation distance", y=1.03)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig04_correlation_decay.png"))
plt.close(fig)

# fig05: fidelity + fitted curve + thresholds + radius
fig, ax = plt.subplots(figsize=(6.6, 4.2))
dd = np.linspace(2, 400, 800)
for ct in CALL_TYPES:
    ax.plot(DIST_M, fid[ct], "o", ms=5, color=COLORS[ct])
    ax.plot(dd, predict(ct, dd), "-", lw=1.8, color=COLORS[ct],
            label=f"{ct} ({fits[ct]['_best']})")
for lvl, thr in THRESHOLDS.items():
    ax.axhline(thr, ls="--", lw=0.9, color="grey")
    ax.text(390, thr + 0.012, f"{lvl} {thr:.2f}", ha="right", fontsize=7, color="grey")
for ct in CALL_TYPES:
    r = radius[ct]["potential"]
    if r is not None:
        ax.plot([r], [THRESHOLDS["potential"]], marker="v", color=COLORS[ct], ms=7)
ax.set_xscale("log", base=2)
ax.set_xticks(DIST_M); ax.set_xticklabels([str(int(v)) for v in DIST_M], fontsize=8)
ax.set_xlabel("distance (m)"); ax.set_ylabel("acoustic fidelity index F(d)")
ax.set_title("Fidelity decay and effective communication range")
ax.legend(fontsize=8, title="selected model")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig05_fidelity_range.png"))
plt.close(fig)

# fig06: bootstrap radius distributions
fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
for ax, ct in zip(axes, CALL_TYPES):
    arr = np.array(boot[ct]["potential"])
    if arr.size:
        ax.hist(arr, bins=30, color=COLORS[ct], alpha=0.8)
        ax.axvline(np.median(arr), color="k", lw=1.2)
        ax.set_title(f"{ct}: median {np.median(arr):.0f} m")
    else:
        ax.text(0.5, 0.5, "threshold unreachable", ha="center", transform=ax.transAxes)
    ax.set_xlabel("potential-recognition radius (m)")
axes[0].set_ylabel("bootstrap frequency")
fig.suptitle("Bootstrap distribution of effective range (threshold 0.50, 1000 resamples)", y=1.03)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig06_bootstrap_range.png"))
plt.close(fig)

with open(os.path.join(RES, "q2.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, ensure_ascii=False)

print("Q2 done")
print("fidelity:", {ct: [round(v, 3) for v in fid[ct]] for ct in CALL_TYPES})
for ct in CALL_TYPES:
    print(f"{ct:5s} best={fits[ct]['_best']:12s} AIC="
          f"{ {k: v['aic'] for k, v in fits[ct].items() if k != '_best'} }")
print("radius:", radius)
print("bootstrap:", bootstrap)
