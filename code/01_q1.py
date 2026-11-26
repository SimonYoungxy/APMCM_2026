"""Stage 1: Q1 - acoustic characterisation, non-parametric tests and call-type classifiers.

Three feature sets are compared:
  A. six raw measures (fair, complete for all 108 calls)
  B. three dimensionless engineered measures (spectral spread / harmonic ratios)
  C. six raw measures + structural voicing flags (leakage audit only, NOT a valid model)
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BASE, CALL_TYPES, COLORS, FEATS, FIG, LABELS, RES, SEED,
                    apply_style, data_path)

import scikit_posthocs as sp
import seaborn as sns
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

rng = np.random.default_rng(SEED)
plt = apply_style()
os.makedirs(FIG, exist_ok=True)

d1 = pd.read_csv(data_path("Data01_AfricanPenguins_seasurface_calls_acoustics.csv"))
y = d1["CallType"].to_numpy()
res = {"n": int(len(d1)), "features": FEATS,
       "counts": {k: int(v) for k, v in d1.CallType.value_counts().items()}}

# ------------------------------------------------------------ descriptive
desc = {}
for ct in CALL_TYPES:
    sub = d1[d1.CallType == ct]
    desc[ct] = {}
    for f in FEATS:
        v = sub[f].dropna().to_numpy(float)
        q1, q3 = np.percentile(v, [25, 75])
        desc[ct][f] = {"n": int(v.size), "mean": round(float(v.mean()), 3),
                       "sd": round(float(v.std(ddof=1)), 3),
                       "median": round(float(np.median(v)), 3),
                       "q1": round(float(q1), 3), "q3": round(float(q3), 3),
                       "iqr": round(float(q3 - q1), 3)}
res["descriptive"] = desc

# ------------------------------------------------------------ normality
shapiro = {}
for ct in CALL_TYPES:
    sub = d1[d1.CallType == ct]
    shapiro[ct] = {}
    for f in FEATS:
        w, p = stats.shapiro(sub[f].dropna().to_numpy(float))
        shapiro[ct][f] = {"W": round(float(w), 4), "p": round(float(p), 4)}
res["shapiro"] = shapiro
res["shapiro_nonnormal_cells"] = int(sum(
    1 for ct in CALL_TYPES for f in FEATS if shapiro[ct][f]["p"] < 0.05))
res["shapiro_total_cells"] = len(CALL_TYPES) * len(FEATS)

# ------------------------------------------------------------ Kruskal-Wallis
kw = {}
for f in FEATS:
    groups = [d1.loc[d1.CallType == ct, f].dropna().to_numpy(float) for ct in CALL_TYPES]
    h, p = stats.kruskal(*groups)
    n, k = sum(g.size for g in groups), len(groups)
    kw[f] = {"H": round(float(h), 3), "df": k - 1, "p": float(p),
             "epsilon_squared": round(float(max(0.0, (h - k + 1) / (n - k))), 4),
             "significant": bool(p < 0.05)}
res["kruskal"] = kw

# ------------------------------------------------------------ Dunn (FDR)
dunn = {}
for f in FEATS:
    tmp = d1[["CallType", f]].dropna()
    mat = sp.posthoc_dunn(tmp, val_col=f, group_col="CallType", p_adjust="fdr_bh")
    dunn[f] = {f"{a}-{b}": float(mat.loc[a, b])
               for i, a in enumerate(CALL_TYPES) for b in CALL_TYPES[i + 1:]}
res["dunn_fdr"] = dunn

# ------------------------------------------------------------ Mann-Whitney sensitivity
mw = {}
for f in FEATS:
    pairs = {}
    for i, a in enumerate(CALL_TYPES):
        for b in CALL_TYPES[i + 1:]:
            va = d1.loc[d1.CallType == a, f].dropna().to_numpy(float)
            vb = d1.loc[d1.CallType == b, f].dropna().to_numpy(float)
            u, p = stats.mannwhitneyu(va, vb, alternative="two-sided")
            pairs[f"{a}-{b}"] = {"U": round(float(u), 2), "p": round(float(p), 4),
                                 "rank_biserial": round(float(1 - 2 * u / (va.size * vb.size)), 3)}
    mw[f] = pairs
res["mannwhitney"] = mw

# ------------------------------------------------------------ feature sets
raw6 = d1[FEATS].to_numpy(float)
band = (d1.Q75 - d1.Q25).to_numpy(float)                 # spectral bandwidth (Hz)
r_peak = (d1.Fpeak / d1.F01).to_numpy(float)             # peak-to-fundamental ratio
r_med = (d1.Q50 / d1.F01).to_numpy(float)                # median-to-fundamental ratio
eng3 = np.c_[band, r_peak, r_med]
flags = np.c_[d1.F02.notna().astype(float),
              d1.PulseRate.notna().astype(float),
              d1.F02.fillna(d1.F02.median()).to_numpy(float),
              d1.PulseRate.fillna(d1.PulseRate.median()).to_numpy(float)]
leak_set = np.c_[raw6, flags]

ENG_NAMES = ["bandwidth Q75-Q25", "Fpeak/F01", "Q50/F01"]
FEATURE_SETS = {"A_raw6": (raw6, FEATS), "B_engineered3": (eng3, ENG_NAMES),
                "C_raw6+structural": (leak_set, FEATS + ["has_F02", "has_PulseRate",
                                                         "F02_filled", "PulseRate_filled"])}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def make_models():
    return {
        "random_forest": RandomForestClassifier(
            n_estimators=800, class_weight="balanced", random_state=SEED, n_jobs=-1),
        "lda": make_pipeline(StandardScaler(), LinearDiscriminantAnalysis()),
        "svm_rbf": make_pipeline(StandardScaler(),
                                 SVC(kernel="rbf", C=1.0, class_weight="balanced",
                                     random_state=SEED)),
    }


clf_all, oof = {}, {}
for set_name, (X, names) in FEATURE_SETS.items():
    clf_all[set_name] = {}
    for mname, mdl in make_models().items():
        pred = cross_val_predict(mdl, X, y, cv=cv)
        cm = confusion_matrix(y, pred, labels=CALL_TYPES)
        p_, r_, f1_, sup_ = precision_recall_fscore_support(
            y, pred, labels=CALL_TYPES, zero_division=0)
        fold = []
        for tr, te in cv.split(X, y):
            mdl.fit(X[tr], y[tr])
            fold.append(accuracy_score(y[te], mdl.predict(X[te])))
        clf_all[set_name][mname] = {
            "cv_accuracy": round(float(accuracy_score(y, pred)), 4),
            "fold_mean": round(float(np.mean(fold)), 4),
            "fold_sd": round(float(np.std(fold, ddof=1)), 4),
            "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
            "confusion_matrix": cm.tolist(),
            "per_class": {c: {"precision": round(float(p_[i]), 3),
                              "recall": round(float(r_[i]), 3),
                              "f1": round(float(f1_[i]), 3),
                              "support": int(sup_[i])}
                          for i, c in enumerate(CALL_TYPES)},
        }
        oof[(set_name, mname)] = pred
res["classifiers"] = clf_all
res["chance_accuracy"] = round(float(max(np.bincount(
    pd.factorize(y)[0]) / len(y))), 4)
res["feature_set_definitions"] = {
    "A_raw6": FEATS, "B_engineered3": ENG_NAMES,
    "C_raw6+structural": "A + has_F02, has_PulseRate, F02_filled, PulseRate_filled"}

# ------------------------------------------------------------ importance
# MDI is reported only for reference; the robust "main influencing factors"
# evidence is the out-of-fold (cross-validated) permutation importance, which is
# evaluated on held-out folds rather than on the training data.
rfB = RandomForestClassifier(n_estimators=800, class_weight="balanced",
                             random_state=SEED, n_jobs=-1).fit(eng3, y)
impB = dict(zip(ENG_NAMES, np.round(rfB.feature_importances_, 4).tolist()))
res["engineered_importance_mdi"] = {k: float(v) for k, v in impB.items()}

rfA = RandomForestClassifier(n_estimators=800, class_weight="balanced",
                             random_state=SEED, n_jobs=-1).fit(raw6, y)
res["raw_importance_mdi"] = dict(zip(FEATS, np.round(rfA.feature_importances_, 4).tolist()))


def cv_permutation_importance(X, yv, feat_names):
    """Mean decrease in held-out accuracy from permuting each feature, averaged
    over the 5 stratified folds (out-of-fold, so no training-set leakage)."""
    imp = {n: [] for n in feat_names}
    for tr, te in cv.split(X, yv):
        rf = RandomForestClassifier(n_estimators=800, class_weight="balanced",
                                    random_state=SEED, n_jobs=-1).fit(X[tr], yv[tr])
        r = permutation_importance(rf, X[te], yv[te], n_repeats=10,
                                   random_state=SEED, scoring="accuracy", n_jobs=-1)
        for i, n in enumerate(feat_names):
            imp[n].append(float(r.importances_mean[i]))
    return {n: round(float(np.mean(v)), 4) for n, v in imp.items()}


res["raw_permutation_importance_cv"] = cv_permutation_importance(raw6, y, FEATS)
res["engineered_permutation_importance_cv"] = cv_permutation_importance(eng3, y, ENG_NAMES)

# ------------------------------------------------------------ figure 1
fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.0))
for ax, f in zip(axes.ravel(), FEATS):
    data = [d1.loc[d1.CallType == ct, f].dropna().to_numpy() for ct in CALL_TYPES]
    bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False,
                    medianprops=dict(color="black", lw=1.2))
    for patch, ct in zip(bp["boxes"], CALL_TYPES):
        patch.set_facecolor(COLORS[ct]); patch.set_alpha(0.65)
    for i, (v, ct) in enumerate(zip(data, CALL_TYPES), start=1):
        ax.scatter(np.full(v.size, i) + rng.normal(0, 0.06, v.size), v, s=10,
                   color=COLORS[ct], alpha=0.75, linewidths=0)
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(CALL_TYPES)
    star = "***" if kw[f]["p"] < 0.001 else ("**" if kw[f]["p"] < 0.01 else
                                             ("*" if kw[f]["p"] < 0.05 else "n.s."))
    ax.set_title(f"{f}  (KW p={kw[f]['p']:.2g}, {star})")
    ax.set_ylabel(LABELS[f])
fig.suptitle("Acoustic measures by call type (n = 44 / 40 / 24)", y=1.00)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig01_boxplots.png"))
plt.close(fig)

# ------------------------------------------------------------ figure 2
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
long = d1.melt(id_vars="CallType", value_vars=FEATS, var_name="feature", value_name="value")
long["z"] = long.groupby("feature")["value"].transform(
    lambda s: (s - s.mean()) / s.std(ddof=0))
sns.violinplot(data=long, x="feature", y="z", hue="CallType", palette=COLORS,
               inner="quartile", cut=0, ax=axes[0], order=FEATS,
               hue_order=CALL_TYPES, linewidth=0.8)
axes[0].axhline(0, color="grey", lw=0.8, ls="--")
axes[0].set_title("Distribution of the six complete features\n(standardised within feature)")
axes[0].set_xlabel(""); axes[0].set_ylabel("z-score within feature")
axes[0].tick_params(axis="x", rotation=30)
axes[0].legend(title="", fontsize=8)

prof = d1.groupby("CallType")[FEATS].median()
prof_n = prof / prof.mean(axis=0)
for ct in CALL_TYPES:
    axes[1].plot(FEATS, prof_n.loc[ct], marker="o", color=COLORS[ct], label=ct)
axes[1].axhline(1, color="grey", lw=0.8, ls="--")
axes[1].set_title("Median feature profile normalised by grand median")
axes[1].set_ylabel("relative value"); axes[1].tick_params(axis="x", rotation=30)
axes[1].legend(title="call type")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig02_violin_profile.png"))
plt.close(fig)

# ------------------------------------------------------------ figure 3
fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8))
labels = ["A raw6", "B eng3", "C raw6+flags"]
width = 0.26
for k, mname in enumerate(["random_forest", "lda", "svm_rbf"]):
    vals = [clf_all[s][mname]["cv_accuracy"] for s in FEATURE_SETS]
    errs = [clf_all[s][mname]["fold_sd"] for s in FEATURE_SETS]
    axes[0].bar(np.arange(3) + (k - 1) * width, vals, width, yerr=errs,
                capsize=3, label=mname.replace("_", " "))
axes[0].axhline(res["chance_accuracy"], color="grey", ls="--", lw=0.9,
                label=f"majority class ({res['chance_accuracy']:.2f})")
axes[0].set_xticks(range(3)); axes[0].set_xticklabels(labels)
axes[0].set_ylabel("5-fold CV accuracy"); axes[0].set_ylim(0, 1.05)
axes[0].set_title("Feature-set comparison")
axes[0].legend(fontsize=7)

cm = np.array(clf_all["B_engineered3"]["random_forest"]["confusion_matrix"])
im = axes[1].imshow(cm, cmap="Blues")
for i in range(3):
    for j in range(3):
        axes[1].text(j, i, cm[i, j], ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
axes[1].set_xticks(range(3)); axes[1].set_xticklabels(CALL_TYPES)
axes[1].set_yticks(range(3)); axes[1].set_yticklabels(CALL_TYPES)
axes[1].set_xlabel("predicted"); axes[1].set_ylabel("observed")
axes[1].set_title("RF on engineered features")
fig.colorbar(im, ax=axes[1], fraction=0.046)

order = np.argsort([res["engineered_permutation_importance_cv"][n] for n in ENG_NAMES])
axes[2].barh([ENG_NAMES[i] for i in order],
             [res["engineered_permutation_importance_cv"][ENG_NAMES[i]] for i in order],
             color="#55A868", alpha=0.9)
axes[2].set_xlabel("CV permutation importance (held-out acc. decrease)")
axes[2].set_title("Engineered feature importance")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig03_classifier.png"))
plt.close(fig)

with open(os.path.join(RES, "q1.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, ensure_ascii=False)

print("Q1 done")
for f in FEATS:
    print(f"{f:9s} H={kw[f]['H']:7.2f} p={kw[f]['p']:.3g} eps2={kw[f]['epsilon_squared']:.3f} "
          f"dunn_min={min(dunn[f].values()):.3g}")
for s in FEATURE_SETS:
    print(f"{s:20s} RF={clf_all[s]['random_forest']['cv_accuracy']:.3f} "
          f"LDA={clf_all[s]['lda']['cv_accuracy']:.3f} "
          f"SVM={clf_all[s]['svm_rbf']['cv_accuracy']:.3f}")
print("importance", res["engineered_importance_mdi"])
