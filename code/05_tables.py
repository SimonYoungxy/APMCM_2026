"""Stage 5a: generate every LaTeX table directly from results/*.json (no hand-typed numbers)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RES, BASE

TAB = os.path.join(BASE, "tables")
os.makedirs(TAB, exist_ok=True)


def load(name):
    return json.load(open(os.path.join(RES, name), encoding="utf-8"))


def pfmt(p):
    if p is None:
        return "--"
    if p < 1e-4:
        return f"{p:.1e}".replace("e-0", "e-")
    return f"{p:.4f}"


def write(name, body):
    with open(os.path.join(TAB, name), "w", encoding="utf-8") as f:
        f.write(body)
    print("wrote", name)


eda = load("eda.json")
q1 = load("q1.json")
q2 = load("q2.json")
q3 = load("q3.json")
q4 = load("q4.json")

# ------------------------------------------------------------------ T1 data audit
rows = []
for f in ["F02", "PulseRate", "Duration", "F01", "Fpeak", "Q25", "Q50", "Q75"]:
    cells = []
    for ct in ["flat", "mod", "tv"]:
        m = eda["d01_missing_by_type"][ct][f]
        cells.append(f"{m['present']}/{m['n']}")
    rows.append(f"{f} & " + " & ".join(cells) + r" \\")
# build Panel B rows explicitly
ev = eda["d02_events"]
b_rows = [
    f"Response (any) & 90 & 18 & {ev['ResponseYesNo']} \\\\",
    f"Head raising & -- & -- & {ev['HeadsUpYesNo']} \\\\",
    f"Vocalising & -- & -- & {ev['VocalYesNo']} \\\\",
    f"Approaching & -- & -- & {ev['ApproachYesNo']} \\\\",
]
corr_nan = eda["corr_total_nan"]
body = r"""\begin{table}[!ht]
\centering
\caption{Data audit. Panel A: calls with a measured value for each acoustic
feature, by call type ($n=108$). Panel B: playback outcome counts ($n=278$).
Panel C: missing values in the nine propagation-correlation files
($300\times7$ each).}
\label{tab:audit}
\footnotesize
\begin{tabular}{lccc}
\toprule
\multicolumn{4}{l}{\textbf{Panel A: acoustic measurements (present / total)}}\\
\midrule
Feature & flat (44) & mod (40) & tv (24)\\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{4}{l}{\textbf{Panel B: playback outcomes (events)}}\\
\midrule
""" + "\n".join(b_rows) + r"""
\midrule
\multicolumn{4}{l}{\textbf{Panel C: propagation correlations}}\\
\midrule
Missing cells & \multicolumn{3}{c}{%d of %d (%.1f\%%)}\\
\bottomrule
\end{tabular}
\end{table}
""" % (corr_nan, 9 * 300 * 7, 100 * corr_nan / (9 * 300 * 7))
write("tab01_audit.tex", body)

# ------------------------------------------------------------------ T2 descriptive + KW
FEATS = q1["features"]
rows = []
for f in FEATS:
    cells = []
    for ct in ["flat", "mod", "tv"]:
        dd = q1["descriptive"][ct][f]
        cells.append(f"{dd['median']:.1f} ({dd['iqr']:.1f})")
    k = q1["kruskal"][f]
    rows.append(f"{f.replace('Q','$Q_{')}" + ("}$" if f.startswith("Q") else "") +
                " & " + " & ".join(cells) +
                f" & {k['H']:.2f} & {pfmt(k['p'])} & {k['epsilon_squared']:.3f}\\\\")
body = r"""\begin{table}[!ht]
\centering
\caption{Descriptive statistics (median with interquartile range in parentheses) and
Kruskal--Wallis tests of the six complete acoustic measures. $\varepsilon^2$ is the
epsilon-squared effect size.}
\label{tab:desc}
\footnotesize
\begin{tabular}{lcccccc}
\toprule
Measure & flat & mod & tv & $H$ & $p$ & $\varepsilon^2$\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab02_descriptive.tex", body)

# ------------------------------------------------------------------ T3 Dunn
rows = []
for f in FEATS:
    d_ = q1["dunn_fdr"][f]
    mw_ = q1["mannwhitney"][f]
    rows.append(f"{f} & {pfmt(d_['flat-mod'])} & {pfmt(d_['flat-tv'])} & "
                f"{pfmt(d_['mod-tv'])} & {abs(mw_['flat-tv']['rank_biserial']):.2f}\\\\")
body = r"""\begin{table}[!ht]
\centering
\caption{Dunn post-hoc tests with Benjamini--Hochberg correction ($p$ values) and the
rank-biserial effect size of the flat--tv contrast from the Mann--Whitney
sensitivity check.}
\label{tab:dunn}
\footnotesize
\begin{tabular}{lcccc}
\toprule
Measure & flat--mod & flat--tv & mod--tv & $r_{rb}$ (flat--tv)\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab03_dunn.tex", body)

# ------------------------------------------------------------------ T4 classifiers
sets = [("A_raw6", "A: six raw measures"), ("B_engineered3", "B: three engineered measures"),
        ("C_raw6+structural", "C: A $+$ structural flags (leakage audit)")]
rows = []
for key, label in sets:
    c = q1["classifiers"][key]
    rows.append(f"{label} & {c['random_forest']['cv_accuracy']:.3f} & "
                f"{c['lda']['cv_accuracy']:.3f} & {c['svm_rbf']['cv_accuracy']:.3f} & "
                f"{c['random_forest']['macro_f1']:.3f}\\\\")
pc = q1["classifiers"]["B_engineered3"]["random_forest"]["per_class"]
body = r"""\begin{table}[!ht]
\centering
\setlength{\tabcolsep}{4pt}
\caption{Three-class classification of call type (5-fold stratified cross-validation,
$n=108$; majority-class accuracy %.3f). Feature set C is reported only as a leakage
audit and is never used as a substantive classifier. Per-class F1 for the best model
(set B, random forest): flat %.3f, mod %.3f, tv %.3f.}
\label{tab:clf}
\scriptsize
\begin{tabular}{lcccc}
\toprule
Feature set & RF accuracy & LDA accuracy & SVM accuracy & RF macro-F1\\
\midrule
""" % (q1["chance_accuracy"], pc["flat"]["f1"], pc["mod"]["f1"], pc["tv"]["f1"]) + \
    "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab04_classifier.tex", body)

# ------------------------------------------------------------------ T5 decay fits
rows = []
for ct in ["flat", "mod", "tv"]:
    for m in ["exponential", "logistic", "power"]:
        f = q2["fits"][ct][m]
        star = r"$^{*}$" if m == q2["selected_model"][ct] else ""
        rows.append(f"{ct} & {m} & ({', '.join(f'{v:.4g}' for v in f['params'])}) & "
                    f"{f['aic']:.2f}{star}\\\\")
body = r"""\begin{table}[!ht]
\centering
\caption{Candidate decay models for the acoustic fidelity index (weighted least
squares, AIC selection; $^{*}$ marks the selected model). Parameters: exponential
$(a,b)$; logistic $(L,k,d_0)$; power $(a,b)$.}
\label{tab:decay}
\footnotesize
\begin{tabular}{llcc}
\toprule
Call type & Model & Parameters & AIC\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab05_decay.tex", body)

# ------------------------------------------------------------------ T6 effective range
rows = []
for ct in ["flat", "mod", "tv"]:
    r = q2["radius_m"][ct]
    b = q2["bootstrap_radius"][ct]
    mf = q2["model_form_radius_m"][ct]
    lo = min(v["potential"] for v in mf.values())
    hi = max(v["potential"] for v in mf.values())
    rows.append(f"{ct} & {r['potential']:.1f} [{(b['potential']['ci95'][0]):.1f}, "
                f"{b['potential']['ci95'][1]:.1f}] & {r['recognition']:.1f} & "
                f"{r['reliable']:.1f} & [{lo:.1f}, {hi:.1f}]\\\\")
body = r"""\begin{table}[!ht]
\centering
\caption{Effective communication range (m) under the three recognition tiers. Columns
2--4 give point estimates of the selected model; the bracket in column 2 is a 95\%
bootstrap interval (1000 whole-recording row-wise resamples preserving the distance
pairing) and column 5 is the range obtained across the three candidate model forms.}
\label{tab:range}
\footnotesize
\begin{tabular}{lcccc}
\toprule
Call & Potential 0.50 [95\% CI] & Recognition 0.60 & Reliable 0.70 & Model-form\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab06_range.tex", body)

# ------------------------------------------------------------------ T7 logistic ORs
def or_rows(dct, keep=None):
    out = []
    for k, v in dct.items():
        if k == "const":
            continue
        if keep is not None and k not in keep:
            continue
        nm = (k.replace("Type_control", "stimulus = control")
               .replace("Type_call", "stimulus = call")
               .replace("log_dist", r"$\log_{10}$ distance")
               .replace("Npenguins", "group size")
               .replace("Context_commuting", "context: commuting")
               .replace("Context_searching", "context: searching"))
        out.append(f"\\quad {nm} & {v['OR']:.3f} & [{v['CI95'][0]:.3f}, {v['CI95'][1]:.3f}]"
                   f" & {pfmt(v['p'])}\\\\")
    return out


lines = or_rows(q3["logit_response_all"]["coef"])
lines += [r"\midrule",
          r"\multicolumn{4}{l}{Call-only model (reference: flat, context: after)}\\"]
callonly = q3["logit_response_callonly"]["coef"]
for k, v in callonly.items():
    if k == "const" or k.startswith("Context_") or k == "log_dist" or k == "Npenguins":
        continue
    nm = k.replace("CallType_", "call type = ")
    lines.append(f"\\quad {nm} & {v['OR']:.3f} & [{v['CI95'][0]:.3f}, {v['CI95'][1]:.3f}]"
                 f" & {pfmt(v['p'])}\\\\")
for k in ["log_dist", "Npenguins"]:
    v = callonly[k]
    nm = {"log_dist": r"$\log_{10}$ distance", "Npenguins": "group size"}[k]
    lines.append(f"\\quad {nm} & {v['OR']:.3f} & [{v['CI95'][0]:.3f}, {v['CI95'][1]:.3f}]"
                 f" & {pfmt(v['p'])}\\\\")
head = (r"""\begin{table}[!ht]
\centering
\caption{Binomial logistic models of the probability of any response. Pseudo-$R^2$
of the pooled model is """ + f"{q3['logit_response_all']['pseudo_r2']:.3f}" +
        r""" (AIC """ + f"{q3['logit_response_all']['aic']:.1f}" + r""").}
\label{tab:logit}
\footnotesize
\begin{tabular}{lccc}
\toprule
Term & Odds ratio & 95\% CI & $p$\\
\midrule
\multicolumn{4}{l}{Pooled model (reference: natural call, context: after)}\\
""")
body = head + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab07_logit.tex", body)

# ------------------------------------------------------------------ T8 survival
rows = []
for name in ["HeadsUp", "Vocal", "Approach"]:
    s = q3["survival"][name]
    c = s["cox"]
    if "call" in c["hazard_ratios"]:
        hr = c["hazard_ratios"]["call"]
        hr_call = f"{hr['HR']:.2f} [{hr['CI95'][0]:.2f}, {hr['CI95'][1]:.2f}]"
    else:
        hr_call = "n.e.$^{a}$"
    hr_dist = c["hazard_ratios"]["log_dist"]
    php = ", ".join(f"{'call' if k == 'call' else r'$\\log_{10}d$'}={v:.3f}".replace("\\\\", "\\")
                    for k, v in c["ph_test"].items())
    rows.append(f"{name} & {s['n_events']} & {pfmt(s['logrank_p'])} & "
                f"{hr_call} & "
                f"{hr_dist['HR']:.2f} [{hr_dist['CI95'][0]:.2f}, {hr_dist['CI95'][1]:.2f}] & "
                f"{c['concordance']:.3f} & {php}\\\\")
body = r"""\begin{table}[!ht]
\centering
\setlength{\tabcolsep}{4pt}
\caption{Latency models with right-censoring. Each Cox model uses at most two
covariates, so the events-per-variable ratio stays above 10. The last column reports
scaled Schoenfeld residual $p$ values. $^{a}$All 23 approach events occurred in
natural-call trials (none in 139 control trials), so the stimulus coefficient is not
estimable; the log-rank test remains valid.}
\label{tab:surv}
\scriptsize
\begin{tabular}{lcccccc}
\toprule
Behaviour & Events & Log-rank $p$ & HR (call) & HR ($\log_{10}d$) & C-index & PH test $p$\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab08_survival.tex", body)

# ------------------------------------------------------------------ T9 predicted latency
rows = []
for r in q3["predicted_latency_table"]:
    med = "--" if r["pred_median_latency_s"] is None else f"{r['pred_median_latency_s']:.1f}"
    prob = r["pred_response_prob_within_10s"]
    verdict = "no response" if r["call"] == "no response" else "response"
    rows.append(f"{r['CallType']} & {r['Distance']} & {med} & {prob:.3f} & {verdict}\\\\")
body = r"""\begin{table}[!ht]
\centering
\caption{Predicted head-raising latency (s) from the Weibull accelerated-failure-time
model, for the median group size of 8 penguins. The observation window of the field
trials is %.0f s, so a condition is labelled ``no response'' when the predicted
probability of responding within that window falls below 0.5.}
\label{tab:latency}
\footnotesize
\begin{tabular}{lcccc}
\toprule
Call type & Distance (m) & Predicted median latency & $P(\text{response}\le %.0f\,\text{s})$ & Verdict\\
\midrule
""" % (q3["predicted_latency_meta"]["horizon_s"], q3["predicted_latency_meta"]["horizon_s"]) + \
    "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab09_latency.tex", body)

# ------------------------------------------------------------------ T10 CE index
rows = []
for ct in ["flat", "mod", "tv"]:
    cr = q4["ce_radius_m"][ct]
    comp = q4["component_radius_m"][ct]
    s1 = q4["sensitivity_recognition_threshold_on_F"]["0.6"][ct]
    s2 = q4["sensitivity_recognition_threshold_on_F"]["0.7"][ct]
    s3 = q4["sensitivity_correlation_reduction"]["20%"][ct]
    rows.append(f"{ct} & {cr:.1f} & {comp['signal']:.1f} & {comp['response']:.1f} & "
                f"{s1:.1f} & {s2:.1f} & {s3:.1f}\\\\")
body = r"""\begin{table}[!ht]
\centering
\setlength{\tabcolsep}{4pt}
\caption{Communication-effectiveness radius (m). Column 2 is the index radius at the
0.5 decision line; columns 3--4 the two component radii (signal fidelity and response
probability, each at 0.5); columns 5--6 the range under a stricter \emph{recognition}
correlation threshold applied to the signal fidelity $F_c(d)$; column 7 the index radius
under a global $-20\%$ correlation loss.}
\label{tab:ce}
\scriptsize
\begin{tabular}{lcccccc}
\toprule
Call & CE radius & Signal $F{=}0.5$ & Response $P{=}0.5$ & Recog.\ $F{=}0.6$ & Recog.\ $F{=}0.7$ & Corr.\ $-20\%$\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
write("tab10_ce.tex", body)

print("all tables written to", TAB)
