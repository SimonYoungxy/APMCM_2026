"""Stage 3: Q3 - playback response modelling with EPV-controlled covariate sets."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.miscmodels.ordinal_model import OrderedModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CALL_TYPES, COLORS, FIG, RES, SEED, apply_style, data_path

import matplotlib.pyplot as plt
from lifelines import CoxPHFitter, KaplanMeierFitter, WeibullAFTFitter
from lifelines.statistics import logrank_test, proportional_hazard_test

warnings.filterwarnings("ignore")
plot = apply_style()
rng = np.random.default_rng(SEED)

d = pd.read_csv(data_path("Data02_AfricanPenguins_playbacks_data.csv"))
d["log_dist"] = np.log10(d["Distance"])
d["dist_bin"] = pd.cut(d["Distance"], [0, 50, 100, 250],
                       labels=["<=50 m", "50-100 m", ">100 m"])
d["n_behaviours"] = (d["HeadsUpYesNo"] + d["VocalYesNo"] + d["ApproachYesNo"])

res = {"n": int(len(d)), "events": {k: int(d[k].sum()) for k in
                                    ["ResponseYesNo", "HeadsUpYesNo", "VocalYesNo",
                                     "ApproachYesNo"]},
       "npenguins_median": float(d["Npenguins"].median())}
res["distance_bins"] = {"<=50": int((d.Distance <= 50).sum()),
                        "50-100": int(((d.Distance > 50) & (d.Distance <= 100)).sum()),
                        ">100": int((d.Distance > 100).sum())}


def or_table(model, names=None):
    """Odds ratios with 95% CI from a statsmodels discrete/GLM binomial fit."""
    params = model.params
    conf = model.conf_int()
    pvals = model.pvalues
    out = {}
    for k in params.index:
        out[str(k)] = {
            "coef": round(float(params[k]), 4),
            "OR": round(float(np.exp(params[k])), 3),
            "CI95": [round(float(np.exp(conf.loc[k, 0])), 3),
                     round(float(np.exp(conf.loc[k, 1])), 3)],
            "p": round(float(pvals[k]), 4)}
    return out


def fit_logit(yv, X, tag, events):
    Xc = sm.add_constant(X)
    mdl = sm.GLM(yv, Xc, family=sm.families.Binomial()).fit()
    out = {"tag": tag, "n": int(len(yv)), "events": int(events),
           "n_covariates": int(X.shape[1]),
           "n_params": int(Xc.shape[1]),
           "epv": round(float(events / X.shape[1]), 2),
           "aic": round(float(mdl.aic), 2),
           "pseudo_r2": round(float(1 - mdl.deviance / mdl.null_deviance), 4),
           "coef": or_table(mdl),
           "deviance": round(float(mdl.deviance), 3),
           "llf": round(float(mdl.llf), 3)}
    return mdl, out


# ------------------------------------------------ 1. overall response rate
tab = pd.crosstab(d["Type"], d["ResponseYesNo"])
chi2, p_chi, dof, exp = stats.chi2_contingency(tab, correction=False)
odds, p_fish = stats.fisher_exact(tab.to_numpy())
n = tab.to_numpy().sum()
cramers_v = np.sqrt(chi2 / n)
res["overall_response"] = {
    "table": tab.to_dict(),
    "call_rate": round(float(d.loc[d.Type == "call", "ResponseYesNo"].mean()), 4),
    "control_rate": round(float(d.loc[d.Type == "control", "ResponseYesNo"].mean()), 4),
    "chi2": round(float(chi2), 3), "df": int(dof), "p_chi2": float(p_chi),
    "cramers_v": round(float(cramers_v), 4),
    "fisher_or": round(float(odds), 3), "p_fisher": float(p_fish),
    "fisher_or_call_vs_control": round(float(1.0 / odds), 3),
    "fisher_or_note": ("scipy returns the odds of response in the first row "
                       "(natural call) relative to the second (control); the "
                       "reciprocal is reported as natural versus control"),
    "risk_difference": round(float(d.loc[d.Type == "call", "ResponseYesNo"].mean()
                                   - d.loc[d.Type == "control", "ResponseYesNo"].mean()), 4),
}

# ------------------------------------------------ 2. logistic models
X1 = pd.get_dummies(d[["Type", "Context", "log_dist", "Npenguins"]],
                    columns=["Type", "Context"], drop_first=True).astype(float)
_, m1 = fit_logit(d["ResponseYesNo"].to_numpy(float), X1,
                  "Response ~ Type + Context + log10(Distance) + Npenguins",
                  d["ResponseYesNo"].sum())
res["logit_response_all"] = m1

sub = d[d.Type == "call"].copy()
X2 = pd.get_dummies(sub[["CallType", "Context", "log_dist", "Npenguins"]],
                    columns=["CallType", "Context"], drop_first=True).astype(float)
_, m2 = fit_logit(sub["ResponseYesNo"].to_numpy(float), X2,
                  "Response ~ CallType + Context + log10(Distance) + Npenguins (call only)",
                  sub["ResponseYesNo"].sum())
res["logit_response_callonly"] = m2

# per-behaviour models, covariate budget = events // 10
behav = {"HeadsUp": "HeadsUpYesNo", "Vocal": "VocalYesNo", "Approach": "ApproachYesNo"}
ctx_d = pd.get_dummies(d["Context"], prefix="ctx", drop_first=True).astype(float)
base_X = pd.concat([
    pd.Series((d.Type == "call").astype(float), name="call", index=d.index),
    d["log_dist"].rename("log_dist"),
    d["Npenguins"].astype(float).rename("Npenguins"),
    ctx_d], axis=1)
ctx_cols = list(ctx_d.columns)

beh_models = {}
separation = {}
for name, col in behav.items():
    ev = int(d[col].sum())
    ctrl_ev = int(d.loc[d.Type == "control", col].sum())
    separation[name] = {"control_events": ctrl_ev, "call_events": ev - ctrl_ev,
                        "complete_separation": ctrl_ev == 0}
    budget = max(1, ev // 10)          # number of covariates allowed at EPV >= 10
    cols = ["call"]
    if budget >= 2:
        cols.append("log_dist")
    if budget >= 3:
        cols.append("Npenguins")
    if budget >= 5:
        cols += ctx_cols
    cols = cols[:budget]
    if ctrl_ev == 0:                   # stimulus effect not estimable (separation)
        cols = [c for c in cols if c != "call"] or ["log_dist"]
    _, mb = fit_logit(d[col].to_numpy(float), base_X[cols],
                      f"{name} ~ " + " + ".join(cols), ev)
    mb["covariates"] = cols
    mb["budget"] = int(budget)
    mb["stimulus_separation"] = bool(ctrl_ev == 0)
    beh_models[name] = mb
res["behaviour_models"] = beh_models
res["behaviour_separation"] = separation

# single-factor tests for Approach (23 events -> multivariable model not estimable)
approach_tests = {}
for fac, series in [("Type", d.Type), ("dist_bin", d.dist_bin),
                    ("CallType", d.CallType)]:
    t = pd.crosstab(series, d["ApproachYesNo"])
    c2, p2, _, _ = stats.chi2_contingency(t, correction=False)
    approach_tests[fac] = {"table": t.to_dict(), "chi2": round(float(c2), 3),
                           "p": float(p2)}
res["approach_single_factor"] = approach_tests

# ------------------------------------------------ 3. number of behaviours (ordinal)
y_ord = d["n_behaviours"].to_numpy(int)
dist_bin_d = pd.get_dummies(d["dist_bin"], drop_first=True).astype(float)
Xo = pd.concat([pd.get_dummies(d["Type"], drop_first=True).astype(float),
                pd.get_dummies(d["Context"], drop_first=True).astype(float),
                dist_bin_d, d[["Npenguins"]].astype(float)], axis=1)
Xo.columns = [str(c) for c in Xo.columns]

om = OrderedModel(y_ord, Xo, distr="logit").fit(method="bfgs", maxiter=2000, disp=False)
po = {"params": {str(k): round(float(v), 4) for k, v in om.params.items()},
      "pvalues": {str(k): round(float(v), 4) for k, v in om.pvalues.items()},
      "aic": round(float(om.aic), 3), "llf": round(float(om.llf), 3)}
# proportional-odds check: LR test against the unrestricted multinomial model
mn = sm.MNLogit(y_ord, sm.add_constant(Xo)).fit(disp=False, maxiter=500)
lr = 2 * (mn.llf - om.llf)
df_diff = int(mn.df_model - om.df_model)
p_po = float(stats.chi2.sf(lr, df_diff)) if df_diff > 0 else float("nan")
po["po_lr_stat"] = round(float(lr), 3)
po["po_df"] = df_diff
po["po_p"] = round(p_po, 4)
po["mnlogit_aic"] = round(float(mn.aic), 3)
po["assumption_met"] = bool(p_po > 0.05)

# fallback model when proportional odds is rejected
mn_res = {
    "aic": round(float(mn.aic), 3),
    "llf": round(float(mn.llf), 3),
    "pseudo_r2": round(float(1 - mn.llf / mn.llnull), 4),
    "lrt_vs_null_p": float(mn.llr_pvalue),
    "n_params": int(mn.df_model),
    "coef": {str(k): [round(float(v), 4) for v in row]
             for k, row in mn.params.iterrows()},
    "p": {str(k): [round(float(v), 4) for v in row]
          for k, row in mn.pvalues.iterrows()},
    "predicted_shares_call_vs_control": {},
}
for tp in ["call", "control"]:
    mask = (d.Type == tp).to_numpy()
    pr = mn.predict(sm.add_constant(Xo))[mask]
    mn_res["predicted_shares_call_vs_control"][tp] = [
        round(float(v), 4) for v in pr.mean(axis=0)]
res["multinomial_nbehaviour"] = mn_res
res["ordinal_nbehaviour"] = po

# ------------------------------------------------ 3b. response intensity
# vocalisation count: a zero-inflated count, modelled with NB2 and two covariates
Xd = pd.DataFrame({"const": 1.0,
                   "call": (d.Type == "call").astype(float).to_numpy(),
                   "log_dist": d["log_dist"].to_numpy()})
nb = sm.NegativeBinomial(d["VocalNcalls"].astype(float), Xd).fit(disp=False, maxiter=500)
ci = nb.conf_int()
res["vocal_calls_model"] = {
    "model": "negative binomial NB2",
    "n": int(len(d)),
    "zeros": int((d.VocalNcalls == 0).sum()),
    "zero_share_call": round(float((d.loc[d.Type == "call", "VocalNcalls"] == 0).mean()), 4),
    "zero_share_control": round(float((d.loc[d.Type == "control", "VocalNcalls"] == 0).mean()), 4),
    "mean_call": round(float(d.loc[d.Type == "call", "VocalNcalls"].mean()), 3),
    "mean_control": round(float(d.loc[d.Type == "control", "VocalNcalls"].mean()), 3),
    "alpha": round(float(nb.params.iloc[-1]), 4),
    "terms": {str(k): {"coef": round(float(nb.params[k]), 4),
                       "IRR": round(float(np.exp(nb.params[k])), 3),
                       "CI95": [round(float(np.exp(ci.loc[k, 0])), 3),
                                round(float(np.exp(ci.loc[k, 1])), 3)],
                       "p": round(float(nb.pvalues[k]), 4)}
              for k in ["call", "log_dist"]},
    "aic": round(float(nb.aic), 2),
}

# durations are recorded as zero when the behaviour did not occur, so they are
# summarised only among trials in which the behaviour was observed
dur_desc = {}
for c in ["HeadsUpDuration", "ApproachDuration"]:
    ev = d[d[c] > 0]
    dur_desc[c] = {"n_events": int(len(ev)),
                   "by_type": {t: {"n": int(len(g)),
                                   "median": round(float(g[c].median()), 1),
                                   "q1": round(float(g[c].quantile(.25)), 1),
                                   "q3": round(float(g[c].quantile(.75)), 1)}
                               for t, g in ev.groupby("Type")}}
res["duration_descriptives"] = dur_desc

# distribution of the eight combinations
combo = d.groupby(["Type", "HeadsUpYesNo", "VocalYesNo", "ApproachYesNo"]).size()
res["combination_counts"] = {str(k): int(v) for k, v in combo.items()}
res["nbehaviour_distribution"] = {
    t: {str(k): int(v) for k, v in g["n_behaviours"].value_counts().sort_index().items()}
    for t, g in d.groupby("Type")}

# ------------------------------------------------ 4. latency survival models
LAT = {"HeadsUp": ("HeadsUpYesNo", "HeadsUpLatency"),
       "Vocal": ("VocalYesNo", "VocalLatency"),
       "Approach": ("ApproachYesNo", "ApproachLatency")}
surv = {}
cox_tables = {}
for name, (flag_col, col) in LAT.items():
    flag = d[flag_col].astype(int)
    t = d[col].astype(float)
    ev_mask = (flag == 1) & t.notna()
    cens_mask = (flag == 0)
    dropped = int(((flag == 1) & t.isna()).sum())
    censor_time = float(t[ev_mask].max())
    tt = np.where(ev_mask, t.clip(lower=0.1), censor_time)
    tt = pd.Series(tt, index=d.index)
    event = ev_mask.astype(int)

    lr = logrank_test(tt[d.Type == "call"], tt[d.Type == "control"],
                      event_observed_A=event[d.Type == "call"],
                      event_observed_B=event[d.Type == "control"])
    mismatch = int(((flag == 0) & t.notna()).sum())   # latency recorded but YesNo = 0
    surv[name] = {"n_events": int(event.sum()), "censored": int(cens_mask.sum()),
                  "dropped_flag_without_latency": dropped,
                  "mismatch_latency_without_flag": mismatch,
                  "censor_time": round(censor_time, 2),
                  "censor_time_note": ("surrogate: longest observed latency "
                                       "(observation window not stated in the data)"),
                  "logrank_p": float(lr.p_value),
                  "logrank_stat": round(float(lr.test_statistic), 3)}
    for grp in ["call", "control"]:
        m = tt[(d.Type == grp) & (event == 1)]
        surv[name][f"median_latency_{grp}"] = (round(float(np.median(m)), 2)
                                              if len(m) else None)

    ctrl_ev = int(d.loc[d.Type == "control", flag_col].sum())
    cols = ["call", "log_dist"] if ctrl_ev > 0 else ["log_dist"]
    cdf = pd.DataFrame({"T": tt, "E": event,
                        "call": (d.Type == "call").astype(float).values,
                        "log_dist": d["log_dist"].values}, index=d.index)
    cph = CoxPHFitter()
    cph.fit(cdf[["T", "E"] + cols], duration_col="T", event_col="E")
    summ = cph.summary
    cox_tables[name] = {
        "n": int(len(cdf)), "events": int(event.sum()),
        "n_covariates": len(cols), "epv": round(float(event.sum() / len(cols)), 2),
        "covariates": cols,
        "stimulus_separation": bool(ctrl_ev == 0),
        "concordance": round(float(cph.concordance_index_), 3),
        "log_likelihood": round(float(cph.log_likelihood_), 3),
        "hazard_ratios": {k: {"HR": round(float(np.exp(summ.loc[k, "coef"])), 3),
                              "CI95": [round(float(np.exp(summ.loc[k, "coef lower 95%"])), 3),
                                       round(float(np.exp(summ.loc[k, "coef upper 95%"])), 3)],
                              "p": round(float(summ.loc[k, "p"]), 4)}
                          for k in summ.index}}
    ph = proportional_hazard_test(cph, cdf[["T", "E"] + cols],
                                  time_transform="rank")
    cox_tables[name]["ph_test"] = {str(i): round(float(v), 4)
                                   for i, v in ph.summary["p"].items()}
    # sensitivity of the Cox model to the surrogate censoring time (0.5x / 1x / 1.5x)
    censor_sens = {}
    for mult, lab in [(0.5, "0.5x"), (1.0, "1.0x"), (1.5, "1.5x")]:
        tt_s = pd.Series(np.where(ev_mask, t.clip(lower=0.1), censor_time * mult),
                         index=d.index)
        cdf_s = pd.DataFrame({"T": tt_s, "E": event,
                              "call": (d.Type == "call").astype(float).values,
                              "log_dist": d["log_dist"].values}, index=d.index)
        cph_s = CoxPHFitter()
        cph_s.fit(cdf_s[["T", "E"] + cols], duration_col="T", event_col="E")
        censor_sens[lab] = {k: round(float(np.exp(cph_s.summary.loc[k, "coef"])), 3)
                            for k in cols if k in cph_s.summary.index}
    cox_tables[name]["censor_time_sensitivity_hr"] = censor_sens
    surv[name]["cox"] = cox_tables[name]

res["survival"] = surv

# ------------------------------------------------ 5. predicted latency table
_hu_flag = d["HeadsUpYesNo"].fillna(0).to_numpy(int)
_hu_t = d["HeadsUpLatency"].to_numpy(float)
_keep = ~((_hu_flag == 1) & np.isnan(_hu_t))
censor_time = float(np.nanmax(_hu_t[(_hu_flag == 1) & _keep]))
aft_df = pd.DataFrame({
    "T": np.where(_hu_flag[_keep] == 1, np.clip(_hu_t[_keep], 0.1, None), censor_time),
    "E": _hu_flag[_keep],
    "CallType": d["CallType"].to_numpy()[_keep],
    "log_dist": d["log_dist"].to_numpy(float)[_keep],
    "Npenguins": d["Npenguins"].to_numpy(float)[_keep]})
aft = WeibullAFTFitter()
aft.fit(aft_df, duration_col="T", event_col="E",
        formula="CallType + log_dist + Npenguins")
res["aft_heads_up"] = {
    "n_events": int(aft_df.E.sum()),
    "n_covariates": 4,
    "epv": round(float(aft_df.E.sum() / 4), 2),
    "median_survival_time": round(float(aft.median_survival_time_), 2),
    "summary": {str(k): {"coef": round(float(v), 4),
                         "p": round(float(aft.summary.loc[k, "p"]), 4)}
                for k, v in aft.params_.items()},
}

pred_rows = []
np_med = float(d["Npenguins"].median())
max_obs = float(d.loc[d.HeadsUpLatency.notna(), "HeadsUpLatency"].max())
for ct in ["control"] + CALL_TYPES:
    for dist in [50, 100, 150]:
        row = pd.DataFrame({"CallType": [ct], "log_dist": [np.log10(dist)],
                            "Npenguins": [np_med]})
        sf = aft.predict_survival_function(row, times=[max_obs])
        s_at = float(sf.iloc[0, 0])
        med = float(aft.predict_median(row).iloc[0])
        pred_rows.append({
            "CallType": ct, "Distance": dist, "Npenguins": np_med,
            "pred_median_latency_s": None if not np.isfinite(med) else round(med, 1),
            "pred_response_prob_within_%.0fs" % max_obs: round(1 - s_at, 3),
            "call": "no response" if (not np.isfinite(med)) or med > max_obs
                    or (1 - s_at) < 0.5 else "response"})
res["predicted_latency_table"] = pred_rows
res["predicted_latency_meta"] = {"npenguins": np_med,
                                 "horizon_s": round(max_obs, 2)}

# ------------------------------------------------ figures
# fig07 response rate by distance bin / call type
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8))
rate = d.groupby(["dist_bin", "Type"], observed=True)["ResponseYesNo"].agg(["mean", "count"]).reset_index()
w = 0.35
for k, tp in enumerate(["call", "control"]):
    s = rate[rate.Type == tp]
    axes[0].bar(np.arange(len(s)) + (k - 0.5) * w, s["mean"], w,
                yerr=np.sqrt(s["mean"] * (1 - s["mean"]) / s["count"]),
                capsize=3, label=tp, color=COLORS.get(tp, "grey"), alpha=0.85)
axes[0].set_xticks(range(rate.dist_bin.nunique()))
axes[0].set_xticklabels(sorted(rate.dist_bin.unique(), key=str))
axes[0].set_ylabel("response rate"); axes[0].set_xlabel("playback distance")
axes[0].set_title("Response rate by distance and stimulus type")
axes[0].legend()

rate2 = d.groupby("CallType")["ResponseYesNo"].agg(["mean", "count"])
axes[1].bar(rate2.index, rate2["mean"],
            yerr=np.sqrt(rate2["mean"] * (1 - rate2["mean"]) / rate2["count"]),
            capsize=3, color=[COLORS.get(c, "grey") for c in rate2.index], alpha=0.85)
axes[1].set_ylabel("response rate"); axes[1].set_title("Response rate by call type")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig07_response_rate.png"))
plt.close(fig)

# fig08 number-of-behaviour distribution
fig, ax = plt.subplots(figsize=(6.2, 3.6))
dist_df = pd.DataFrame(res["nbehaviour_distribution"]).T.fillna(0)
dist_df = dist_df / dist_df.sum(axis=1).values[:, None]
bottom = np.zeros(len(dist_df))
for k in dist_df.columns:
    ax.bar(dist_df.index, dist_df[k], bottom=bottom, label=f"{k} behaviours")
    bottom += dist_df[k].values
ax.set_ylabel("proportion"); ax.set_title("Number of response behaviours per playback")
ax.legend(title="", fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.15))
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig08_behaviour_count.png"))
plt.close(fig)

# fig09 KM curves
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
for ax, (name, (flag_col, col)) in zip(axes, LAT.items()):
    flag = d[flag_col].astype(int)
    t = d[col].astype(float)
    ev_mask = (flag == 1) & t.notna()
    cmax = float(t[ev_mask].max())
    tt = pd.Series(np.where(ev_mask, t.clip(lower=0.1), cmax), index=d.index)
    ev = ev_mask.astype(int)
    for grp in ["call", "control"]:
        m = d.Type == grp
        KaplanMeierFitter().fit(tt[m], event_observed=ev[m], label=grp).plot_survival_function(
            ax=ax, ci_show=False, color=COLORS.get(grp, "grey"))
    ax.set_title(f"{name} (log-rank p={surv[name]['logrank_p']:.3g})")
    ax.set_xlabel("time since playback (s)")
    ax.set_ylim(0, 1.02)
axes[0].set_ylabel("P(no response yet)")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig09_km_latency.png"))
plt.close(fig)

with open(os.path.join(RES, "q3.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, ensure_ascii=False, default=str)

print("Q3 done")
print("overall", {k: res["overall_response"][k] for k in
                  ["call_rate", "control_rate", "p_chi2", "fisher_or", "p_fisher"]})
for k, v in beh_models.items():
    print(f"{k:9s} n_params={v['n_params']} epv={v['epv']} aic={v['aic']} "
          f"pseudoR2={v['pseudo_r2']}")
print("ordinal po_p", po["po_p"], "aic", po["aic"])
for k, v in surv.items():
    print(f"{k:9s} events={v['n_events']} logrank_p={v['logrank_p']:.3g} "
          f"cox_c={v['cox']['concordance']}")
print("pred table", pred_rows[:4])
