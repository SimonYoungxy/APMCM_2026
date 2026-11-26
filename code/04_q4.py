"""Stage 4: Q4 - acoustic communication effectiveness index and conservation scenarios."""
import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CALL_TYPES, COLORS, FIG, RES, SEED, apply_style, data_path

plot = apply_style()
rng = np.random.default_rng(SEED)

q2 = json.load(open(os.path.join(RES, "q2.json"), encoding="utf-8"))
d = pd.read_csv(data_path("Data02_AfricanPenguins_playbacks_data.csv"))
d["log_dist"] = np.log10(d["Distance"])

res = {"index_definition": "CE(d) = w1 * F(d) + w2 * P(d), w1 = w2 = 0.5",
       "index_threshold": 0.5}


# ---------------------------------------------------------------- fidelity curves
def m_exp(x, a, b):
    return a * np.exp(-b * x)


def m_logi(x, L, k, d0):
    return L / (1.0 + np.exp(k * (x - d0)))


def m_pow(x, a, b):
    return a * np.power(x, -b)


MODELF = {"exponential": m_exp, "logistic": m_logi, "power": m_pow}


def fidelity(ct, dist):
    name = q2["selected_model"][ct]
    params = q2["fits"][ct][name]["params"]
    return MODELF[name](np.asarray(dist, float), *params)


# ---------------------------------------------------------------- response model
sub = d[d.Type == "call"].copy()
X = pd.get_dummies(sub[["CallType", "Context", "log_dist", "Npenguins"]],
                   columns=["CallType", "Context"], drop_first=True).astype(float)
Xc = sm.add_constant(X)
logit = sm.GLM(sub["ResponseYesNo"].to_numpy(float), Xc,
               family=sm.families.Binomial()).fit()
coef = logit.params
res["response_model_coef"] = {str(k): round(float(v), 4) for k, v in coef.items()}
res["response_model_aic"] = round(float(logit.aic), 2)
res["response_model_pseudo_r2"] = round(
    float(1 - logit.deviance / logit.null_deviance), 4)


def response_prob(ct, dist, npen, context="commuting"):
    row = {"const": 1.0, "log_dist": np.log10(dist), "Npenguins": npen}
    for c in CALL_TYPES:
        if c != "flat":
            row[f"CallType_{c}"] = 1.0 if c == ct else 0.0
    for c in ["commuting", "searching"]:
        if c != "after":
            row[f"Context_{c}"] = 1.0 if c == context else 0.0
    eta = sum(coef.get(k, 0.0) * v for k, v in row.items())
    return float(1 / (1 + np.exp(-eta)))


NP_MED = float(d["Npenguins"].median())
res["npenguins_median"] = NP_MED
res["group_size_distribution"] = {str(int(k)): int(v) for k, v in
                                  d["Npenguins"].value_counts().sort_index().items()}

# ---------------------------------------------------------------- index and radius
D_GRID = np.linspace(2, 1500, 150000)


def ce_curve(ct, dist, w1=0.5, npen=NP_MED, context="commuting", corr_factor=1.0):
    F = fidelity(ct, dist) * corr_factor
    P = np.array([response_prob(ct, dd, npen, context) for dd in np.atleast_1d(dist)])
    return w1 * F + (1 - w1) * P, F, P


def radius_of(curve, dist, level=0.5):
    vals = np.asarray(curve)
    if vals[0] < level:
        return 4.0 if not np.isfinite(vals[0]) else float(dist[0])
    idx = np.where(vals <= level)[0]
    if idx.size == 0:
        return float(dist[-1])
    i = idx[0]
    if i == 0:
        return float(dist[0])
    return float(dist[i - 1] + (vals[i - 1] - level) *
                 (dist[i] - dist[i - 1]) / (vals[i - 1] - vals[i]))


ce_radius, comp_radius, ce_curves = {}, {}, {}
for ct in CALL_TYPES:
    ce, F, P = ce_curve(ct, D_GRID)
    ce_curves[ct] = ce
    ce_radius[ct] = round(radius_of(ce, D_GRID, 0.5), 1)
    comp_radius[ct] = {"signal": round(radius_of(F, D_GRID, 0.5), 1),
                       "response": round(radius_of(P, D_GRID, 0.5), 1)}
res["ce_radius_m"] = ce_radius
res["component_radius_m"] = comp_radius
res["ce_at_reference_distances"] = {
    ct: {f"{dm}m": round(float(np.interp(dm, D_GRID, ce_curves[ct])), 4)
         for dm in [50, 100, 150, 200]} for ct in CALL_TYPES}

# ---------------------------------------------------------------- expected responders
groups = d["Npenguins"].to_numpy(float)
g_vals, g_freq = np.unique(groups, return_counts=True)
g_prob = g_freq / g_freq.sum()


def expected_responders(ct, dist, context="commuting"):
    p = np.array([response_prob(ct, dist, g, context) for g in g_vals])
    return float(np.sum(g_prob * g_vals * p))


res["expected_responders"] = {
    ct: {f"{dm}m": round(expected_responders(ct, dm), 3) for dm in [50, 100, 150, 200]}
    for ct in CALL_TYPES}

# ---------------------------------------------------------------- sensitivity
# (a) recognition threshold 0.5 -> 0.6 / 0.7
thr_sens = {}
for lvl in [0.5, 0.6, 0.7]:
    thr_sens[str(lvl)] = {ct: round(radius_of(ce_curves[ct], D_GRID, lvl), 1)
                          for ct in CALL_TYPES}
res["sensitivity_threshold"] = thr_sens

# (b) global correlation reduction 5%-20%
corr_sens = {}
for red in [0.0, 0.05, 0.10, 0.15, 0.20]:
    corr_sens[f"{int(red*100)}%"] = {}
    for ct in CALL_TYPES:
        ce, _, _ = ce_curve(ct, D_GRID, corr_factor=1 - red)
        corr_sens[f"{int(red*100)}%"][ct] = round(radius_of(ce, D_GRID, 0.5), 1)
res["sensitivity_correlation_reduction"] = corr_sens

# (c) weight on the signal component
w_sens = {}
for w1 in [0.3, 0.4, 0.5, 0.6, 0.7]:
    w_sens[str(w1)] = {}
    for ct in CALL_TYPES:
        ce, _, _ = ce_curve(ct, D_GRID, w1=w1)
        w_sens[str(w1)][ct] = round(radius_of(ce, D_GRID, 0.5), 1)
res["sensitivity_weight"] = w_sens

# (d) responder proportion assumption (scales the expected number only)
prop_sens = {}
for frac in [0.25, 0.5, 0.75, 1.0]:
    prop_sens[str(frac)] = {
        ct: {f"{dm}m": round(frac * expected_responders(ct, dm), 3)
             for dm in [50, 100, 150]} for ct in CALL_TYPES}
res["sensitivity_responder_proportion"] = prop_sens

# ---------------------------------------------------------------- figures
fig, axes = plot.subplots(1, 3, figsize=(12.2, 3.8), sharey=True)
for ax, ct in zip(axes, CALL_TYPES):
    ce, F, P = ce_curve(ct, D_GRID)
    ax.plot(D_GRID, F, "--", lw=1.1, color="#4C72B0", label="F(d) signal fidelity")
    ax.plot(D_GRID, P, ":", lw=1.4, color="#DD8452", label="P(d) response prob.")
    ax.plot(D_GRID, ce, "-", lw=2.0, color=COLORS[ct], label="CE(d) index")
    ax.axhline(0.5, color="grey", lw=0.8)
    ax.axvline(ce_radius[ct], color="k", lw=0.8, ls="-.")
    ax.text(ce_radius[ct], 0.06, f" {ce_radius[ct]:.0f} m", fontsize=8)
    ax.set_xscale("log")
    ax.set_title(f"{ct}: CE radius {ce_radius[ct]:.0f} m")
    ax.set_xlabel("distance (m)")
    ax.set_ylim(0, 1.02)
axes[0].set_ylabel("index value")
axes[0].legend(fontsize=7, loc="upper right")
fig.suptitle("Acoustic communication effectiveness index (group size = median 8)", y=1.03)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig10_ce_index.png"))
plot.close(fig)

fig, axes = plot.subplots(1, 2, figsize=(10.5, 3.8))
for ct in CALL_TYPES:
    axes[0].plot([50, 100, 150, 200],
                 [res["expected_responders"][ct][f"{x}m"] for x in [50, 100, 150, 200]],
                 marker="o", color=COLORS[ct], label=ct)
axes[0].set_xlabel("playback distance (m)")
axes[0].set_ylabel("expected number of responders")
axes[0].set_title("Expected responders per playback (empirical group sizes)")
axes[0].legend()

reds = [0.0, 0.05, 0.10, 0.15, 0.20]
for ct in CALL_TYPES:
    axes[1].plot([r * 100 for r in reds],
                 [corr_sens[f"{int(r*100)}%"][ct] for r in reds],
                 marker="s", color=COLORS[ct], label=ct)
axes[1].set_xlabel("global correlation reduction (%)")
axes[1].set_ylabel("CE radius (m)")
axes[1].set_title("Scenario: weakened signal recognition")
axes[1].legend()
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig11_scenarios.png"))
plot.close(fig)

with open(os.path.join(RES, "q4.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, ensure_ascii=False)

print("Q4 done")
print("CE radius", ce_radius)
print("components", comp_radius)
print("threshold sens", thr_sens)
print("corr sens", corr_sens)
print("weight sens", w_sens)
print("expected responders", res["expected_responders"]["tv"])
