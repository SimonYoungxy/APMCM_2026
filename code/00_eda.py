"""Stage 0: exploratory data audit. Writes eda/eda_report.md and results/eda.json."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BASE, CALL_TYPES, CORR_FILES, DATA, DIST_COLS, EDA, FEATS,
                    RES, data_path)

out = {}
lines = ["# Problem C data audit", ""]

# ---------------------------------------------------------------- Data01
d1 = pd.read_csv(data_path("Data01_AfricanPenguins_seasurface_calls_acoustics.csv"))
out["d01_n"] = int(len(d1))
out["d01_by_type"] = {k: int(v) for k, v in d1["CallType"].value_counts().items()}

miss_by_type = {}
for ct in CALL_TYPES:
    sub = d1[d1.CallType == ct]
    miss_by_type[ct] = {
        c: {"present": int(sub[c].notna().sum()), "n": int(len(sub))}
        for c in ["F02", "PulseRate"] + FEATS
    }
out["d01_missing_by_type"] = miss_by_type

leak_f02 = bool(
    ((d1.F02.notna()) == (d1.CallType == "tv")).all()
)
# PulseRate is not a perfect indicator: it is absent for every flat call but also
# missing for a few modulated and two-voice calls, so record the per-type rate
# instead of a single boolean with a misleading name.
pr_missing_rate = {
    ct: round(1.0 - float(d1.loc[d1.CallType == ct, "PulseRate"].notna().mean()), 4)
    for ct in CALL_TYPES
}
out["leak_F02_is_tv_indicator"] = leak_f02
out["pulse_rate_missing_rate_by_type"] = pr_missing_rate
out["pulse_rate_absent_for_flat"] = pr_missing_rate["flat"] == 1.0

complete_rows = int(d1[FEATS].notna().all(axis=1).sum())
out["d01_rows_with_6_complete_feats"] = complete_rows

lines += [
    "## Data01 acoustic measurements", "",
    f"- rows: {len(d1)}, CallType counts: {out['d01_by_type']}",
    f"- rows with all 6 complete features: {complete_rows}",
    f"- F02 present iff CallType == tv: **{leak_f02}** (structural leakage)",
    "- PulseRate missing rate by call type: "
    + ", ".join(f"{ct} {100*v:.1f}%" for ct, v in pr_missing_rate.items()),
    "",
    "| feature | flat present | mod present | tv present |",
    "|---|---|---|---|",
]
for c in ["F02", "PulseRate"] + FEATS:
    lines.append("| %s | %d/%d | %d/%d | %d/%d |" % (
        c,
        miss_by_type["flat"][c]["present"], miss_by_type["flat"][c]["n"],
        miss_by_type["mod"][c]["present"], miss_by_type["mod"][c]["n"],
        miss_by_type["tv"][c]["present"], miss_by_type["tv"][c]["n"]))
lines.append("")

# ---------------------------------------------------------------- Data02
d2 = pd.read_csv(data_path("Data02_AfricanPenguins_playbacks_data.csv"))
out["d02_n"] = int(len(d2))
out["d02_type"] = {k: int(v) for k, v in d2["Type"].value_counts().items()}
out["d02_calltype"] = {k: int(v) for k, v in d2["CallType"].value_counts().items()}
out["d02_context"] = {k: int(v) for k, v in d2["Context"].value_counts().items()}
out["d02_events"] = {
    k: int(d2[k].sum()) for k in
    ["ResponseYesNo", "HeadsUpYesNo", "ApproachYesNo", "VocalYesNo"]
}
out["d02_distance_levels"] = sorted(int(x) for x in d2["Distance"].unique())
out["d02_distance_counts"] = {
    str(int(k)): int(v) for k, v in d2["Distance"].value_counts().sort_index().items()
}
out["d02_npenguins_median"] = float(d2["Npenguins"].median())
out["d02_response_by_type"] = {
    t: {"n": int(len(g)), "responses": int(g.ResponseYesNo.sum())}
    for t, g in d2.groupby("Type")
}
ct_dist = pd.crosstab(d2["Distance"], d2["CallType"])
empty_cells = int((ct_dist == 0).sum().sum())
out["d02_distance_calltype_empty_cells"] = empty_cells
out["d02_latency_missing"] = {
    c: int(d2[c].isna().sum()) for c in
    ["HeadsUpLatency", "ApproachLatency", "VocalLatency"]
}

lines += [
    "## Data02 playback experiments", "",
    f"- rows: {len(d2)}; Type: {out['d02_type']}; CallType: {out['d02_calltype']}",
    f"- Context: {out['d02_context']}",
    f"- events: {out['d02_events']}",
    f"- Distance levels ({len(out['d02_distance_levels'])}): {out['d02_distance_levels']}",
    f"- Distance x CallType empty cells: {empty_cells} -> interaction terms are not estimable",
    f"- Npenguins median: {out['d02_npenguins_median']}",
    f"- response by Type: {out['d02_response_by_type']}",
    f"- missing latencies (right-censored): {out['d02_latency_missing']}",
    "",
    "| Distance | " + " | ".join(["control"] + CALL_TYPES) + " |",
    "|---" * 5 + "|",
]
for dist in ct_dist.index:
    row = [str(int(dist))] + [str(int(ct_dist.loc[dist, c])) if c in ct_dist.columns else "0"
                              for c in ["control"] + CALL_TYPES]
    lines.append("| " + " | ".join(row) + " |")
lines.append("")

# ---------------------------------------------------------------- Data03-11
corr_info = {}
for (ct, metric), fname in CORR_FILES.items():
    df = pd.read_csv(data_path(fname))
    key = f"{ct}|{metric}"
    corr_info[key] = {
        "n_rows": int(len(df)),
        "nan_total": int(df.isna().sum().sum()),
        "nan_by_col": {c: int(df[c].isna().sum()) for c in DIST_COLS},
        "median_by_dist": {c: round(float(df[c].median()), 4) for c in DIST_COLS},
        "min_by_dist": {c: round(float(df[c].min()), 4) for c in DIST_COLS},
    }
out["corr_files"] = corr_info
out["corr_total_nan"] = int(sum(v["nan_total"] for v in corr_info.values()))

lines += [
    "## Data03-11 propagation correlations", "",
    f"- 9 files, 300 x 7 each; total NaN = {out['corr_total_nan']}",
    "",
    "| call | metric | NaN | median@4m | median@256m |",
    "|---|---|---|---|---|",
]
for key, v in corr_info.items():
    ct, metric = key.split("|")
    lines.append("| %s | %s | %d | %.3f | %.3f |" % (
        ct, metric, v["nan_total"], v["median_by_dist"]["4m"],
        v["median_by_dist"]["256m"]))
lines.append("")

os.makedirs(EDA, exist_ok=True)
with open(os.path.join(EDA, "eda_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
with open(os.path.join(RES, "eda.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print("\n".join(lines))
print("\nwrote", os.path.join(RES, "eda.json"))
