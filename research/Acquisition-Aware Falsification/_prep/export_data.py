"""Export a slim, render-ready data layer for the Quarto manuscript.

Reads the full analysis repo (not shipped with the website) and writes small
CSVs into ../_data/. Only pandas + numpy are required; PCA is done with a
numpy SVD and Kaplan-Meier is computed directly, so the website render needs
no sklearn / scipy / lifelines.

Source repo:
  Desktop/Dr. Lama/Separating Cluster Stability from Biological Identity
  in Breast MRI Radiomic Phenotype Discovery
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd

SRC = os.environ["RADIOMICS_REPO"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_data")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

R = lambda *p: os.path.join(SRC, *p)
W = lambda name: os.path.join(OUT, name)

PID = "Patient ID"
EVENT = "Recurrence event(s)"
SUBTYPE = "Mol Subtype"
LOCAL_RECUR = "Days to local recurrence (from the date of diagnosis) "
DISTANT_RECUR = "Days to distant recurrence(from the date of diagnosis) "
LAST_LOCAL = "Days to last local recurrence free assessment (from the date of diagnosis) "
LAST_DISTANT = "Days to last distant recurrence free assemssment(from the date of diagnosis) "
DAYS_PER_YEAR = 365.25
MANUFACTURER_MAP = {0: "GE", 1: "MPTronic", 2: "Siemens", "0": "GE", "1": "MPTronic",
                    "2": "Siemens", "GE MEDICAL SYSTEMS": "GE", "SIEMENS": "Siemens",
                    "MPTronic software": "MPTronic"}
SUBTYPE_LABELS = {0: "Luminal-like", 1: "HR+/HER2+", 2: "HER2-enriched", 3: "Triple negative"}

log = lambda *a: print("[export]", *a, file=sys.stderr)

# ---------------------------------------------------------------- patient frame
merged = pd.read_csv(R("data", "interim", "merged_dataset.csv"), low_memory=False)
pca = pd.read_csv(R("data", "processed", "PCA_scores.csv"))
lab_raw = pd.read_csv(R("data", "results", "cluster_labels_k2.csv")).rename(columns={"Cluster": "cluster_raw"})
lab_res = pd.read_csv(R("data", "results", "cluster_labels_residualized_manufacturer.csv"))
lab_com = pd.read_csv(R("data", "results", "cluster_labels_combat.csv"))
for d, name in ((lab_res, "cluster_resid"), (lab_com, "cluster_combat")):
    col = [c for c in d.columns if c != PID][-1]
    d.rename(columns={col: name}, inplace=True)
    d.drop(columns=[c for c in d.columns if c not in (PID, name)], inplace=True)

df = merged.merge(pca, on=PID).merge(lab_raw[[PID, "cluster_raw"]], on=PID)
df = df.merge(lab_res, on=PID, how="left").merge(lab_com, on=PID, how="left")

df["manufacturer"] = df["Manufacturer"].map(MANUFACTURER_MAP).fillna(df["Manufacturer"].astype(str))
df["subtype"] = pd.to_numeric(df[SUBTYPE], errors="coerce")
df["subtype_label"] = df["subtype"].map(SUBTYPE_LABELS)
df["recurrence"] = pd.to_numeric(df[EVENT], errors="coerce")

# recurrence-free survival, replicating survival.build_rfs_frame
for c in (LOCAL_RECUR, DISTANT_RECUR, LAST_LOCAL, LAST_DISTANT):
    df[c] = pd.to_numeric(df[c], errors="coerce")
rec_days = df[[LOCAL_RECUR, DISTANT_RECUR]].min(axis=1)
fup_days = df[[LAST_LOCAL, LAST_DISTANT]].max(axis=1)
rfs_days = np.where(df["recurrence"] == 1, rec_days, fup_days)
df["rfs_years"] = rfs_days / DAYS_PER_YEAR
df.loc[~df["recurrence"].isin([0, 1]) | ~(df["rfs_years"] > 0), "rfs_years"] = np.nan

acq = {"tr": "TR (Repetition Time)", "te": "TE (Echo Time)",
       "acq_matrix": "Acquisition Matrix", "field_strength": "Field Strength (Tesla)",
       "slice_thickness": "Slice Thickness ", "tumor_volume_mm3": "Volume_cu_mm_Tumor"}
for new, old in acq.items():
    df[new] = pd.to_numeric(df[old], errors="coerce") if new != "acq_matrix" else df[old]

# bounding-box volume (voxels) — the size-linked residual structure in §4.4
for c in ("Start Row", "End Row", "Start Column", "End Column", "Start Slice", "End Slice"):
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["bbox_volume"] = ((df["End Row"] - df["Start Row"]).abs()
                     * (df["End Column"] - df["Start Column"]).abs()
                     * (df["End Slice"] - df["Start Slice"]).abs())

cols = [PID, "PC1", "PC2", "PC3", "PC4", "PC5", "cluster_raw", "cluster_resid",
        "cluster_combat", "manufacturer", "subtype", "subtype_label", "recurrence",
        "rfs_years", "tumor_volume_mm3", "bbox_volume", "tr", "te", "acq_matrix",
        "field_strength", "slice_thickness"]
patients = df[cols].rename(columns={PID: "patient_id"})
patients.to_csv(W("patients.csv"), index=False)
log("patients.csv", patients.shape)

# ---------------------------------------------------------- PCA variance (SVD)
X = pd.read_csv(R("data", "processed", "X_radiomics_zscored.csv"))
X = X.select_dtypes(include=[np.number]).to_numpy(dtype=float)
X = X - X.mean(axis=0)
sv = np.linalg.svd(X, full_matrices=False, compute_uv=False)
evr = (sv ** 2) / (sv ** 2).sum()
var = pd.DataFrame({"pc": np.arange(1, len(evr) + 1),
                    "explained_variance_ratio": evr,
                    "cumulative": np.cumsum(evr)}).head(30)
var.to_csv(W("pca_variance.csv"), index=False)
log("pca_variance.csv  top10 cum =", round(float(var.cumulative.iloc[9]), 4))

# ------------------------------------------------- acquisition dominance (eta^2)
def eta_squared(values: pd.Series, groups: pd.Series) -> float:
    """Proportion of variance in `values` explained by categorical `groups`."""
    d = pd.DataFrame({"v": pd.to_numeric(values, errors="coerce"), "g": groups}).dropna()
    if d["g"].nunique() < 2 or len(d) < 3:
        return np.nan
    grand = d["v"].mean()
    ss_total = ((d["v"] - grand) ** 2).sum()
    ss_between = sum(len(g) * (g["v"].mean() - grand) ** 2 for _, g in d.groupby("g"))
    return float(ss_between / ss_total) if ss_total > 0 else np.nan

def as_groups(s: pd.Series) -> pd.Series:
    """Each distinct observed value is its own group (the manuscript's grouping)."""
    x = pd.to_numeric(s, errors="coerce")
    return x.astype(str).where(x.notna()) if x.notna().any() else s.astype(str)

def binned(s: pd.Series, q: int = 10) -> pd.Series:
    """Quantile-binned grouping, used only for the sensitivity check."""
    x = pd.to_numeric(s, errors="coerce")
    try:
        return pd.qcut(x, q=q, duplicates="drop").astype(str).where(x.notna())
    except ValueError:
        return x.astype(str).where(x.notna())

grouping = {
    "TR (repetition time)": as_groups(df["tr"]),
    "TE (echo time)": as_groups(df["te"]),
    "Acquisition matrix": as_groups(df["acq_matrix"]),
    "Manufacturer": df["manufacturer"],
    "Field strength": as_groups(df["field_strength"]),
    "Slice thickness": as_groups(df["slice_thickness"]),
    "Molecular subtype": df["subtype_label"],
    "Recurrence": df["recurrence"].map({0: "No recurrence", 1: "Recurrence"}),
}
TECHNICAL = {"TR (repetition time)", "TE (echo time)", "Acquisition matrix",
             "Manufacturer", "Field strength", "Slice thickness"}
rows = []
for name, g in grouping.items():
    row = {"variable": name, "kind": "Technical" if name in TECHNICAL else "Biological",
           "n_groups": int(pd.Series(g).dropna().nunique())}
    for pc in ("PC1", "PC2", "PC3", "PC4", "PC5"):
        row[pc] = eta_squared(df[pc], g)
    rows.append(row)
eta = pd.DataFrame(rows).sort_values("PC1", ascending=False)
eta.to_csv(W("acquisition_eta2.csv"), index=False)

# Sensitivity: eta^2 on PC1 is upward-biased when a continuous acquisition
# variable has many distinct values. Recompute TR/TE under coarser groupings
# and as a linear R^2 so the manuscript can state the bias explicitly.
sens = []
for name, col in (("TR (repetition time)", "tr"), ("TE (echo time)", "te")):
    d = df[[col, "PC1"]].dropna()
    r = float(np.corrcoef(pd.to_numeric(d[col]), d["PC1"])[0, 1])
    sens.append({"variable": name,
                 "eta2_distinct_values": eta_squared(df["PC1"], as_groups(df[col])),
                 "eta2_10_bins": eta_squared(df["PC1"], binned(df[col], 10)),
                 "eta2_20_bins": eta_squared(df["PC1"], binned(df[col], 20)),
                 "linear_r_squared": r ** 2})
pd.DataFrame(sens).to_csv(W("acquisition_eta2_sensitivity.csv"), index=False)

log("acquisition_eta2.csv\n", eta.round(3).to_string(index=False))

# --------------------------------------------------- Kaplan-Meier (HR+/HER2+)
def km_curve(time: np.ndarray, event: np.ndarray):
    """Kaplan-Meier estimate with Greenwood standard errors and at-risk counts."""
    order = np.argsort(time)
    t, e = np.asarray(time)[order], np.asarray(event)[order]
    n = len(t)
    out, s, cum_var, at_risk = [{"t": 0.0, "surv": 1.0, "lo": 1.0, "hi": 1.0, "n_risk": n, "d": 0}], 1.0, 0.0, n
    for ut in np.unique(t):
        at_risk = int((t >= ut).sum())
        d = int(e[t == ut].sum())
        if d == 0:
            continue
        s *= 1 - d / at_risk
        cum_var += d / (at_risk * (at_risk - d)) if at_risk > d else 0.0
        se = s * np.sqrt(cum_var)
        out.append({"t": float(ut), "surv": s, "lo": max(0.0, s - 1.96 * se),
                    "hi": min(1.0, s + 1.96 * se), "n_risk": at_risk, "d": d})
    return pd.DataFrame(out)

HRHER2 = 1
surv = patients[(patients["subtype"] == HRHER2) & patients["rfs_years"].notna()
                & patients["recurrence"].isin([0, 1])]
curves, risk = [], []
grid = np.arange(0, 8.5, 1.0)
for cl, g in surv.groupby("cluster_raw"):
    c = km_curve(g["rfs_years"].to_numpy(), g["recurrence"].to_numpy())
    c["cluster"] = int(cl)
    curves.append(c)
    for gt in grid:
        risk.append({"cluster": int(cl), "t": float(gt),
                     "n_risk": int((g["rfs_years"].to_numpy() >= gt).sum())})
pd.concat(curves).to_csv(W("km_hrher2.csv"), index=False)
pd.DataFrame(risk).to_csv(W("km_at_risk.csv"), index=False)
log("km_hrher2.csv  n =", len(surv), " events =", int(surv["recurrence"].sum()))

# ------------------------------------------------ copy / trim pipeline outputs
COPY = ["kmeans_validity_metrics.csv", "stability_summary_raw_resid_combat.csv",
        "association_after_harmonization.csv", "cluster_by_manufacturer_counts.csv",
        "cluster_association_results.csv", "cox_cluster_only.csv",
        "cox_manufacturer_adjusted.csv", "survival_outcome_summary.csv",
        "within_manufacturer_clustering_results.csv", "bootstrap_ari_results.csv"]
for f in COPY:
    pd.read_csv(R("data", "results", f)).to_csv(W(f), index=False)
log("copied", len(COPY), "result tables")

top = pd.read_csv(R("data", "results", "top_cluster_features.csv"))
top.sort_values("abs_cohens_d", ascending=False).head(40).to_csv(W("top_cluster_features.csv"), index=False)
log("top_cluster_features.csv  (top 40 of %d)" % len(top))

# cross-tabs used in the supplement
pd.crosstab(patients["cluster_raw"], patients["subtype_label"]).to_csv(W("xtab_cluster_subtype.csv"))
pd.crosstab(patients["cluster_raw"], patients["recurrence"].map({0: "No recurrence", 1: "Recurrence"})).to_csv(W("xtab_cluster_recurrence.csv"))
log("done ->", OUT)
