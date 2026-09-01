"""Figure builders for the manuscript. Each returns a function of (fig, palette)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from _theme import DATA, Palette, hairline_grid, panel_title, render, title

d = lambda name: pd.read_csv(DATA / name)

CLUSTER_LABEL = {0: "Cluster 0", 1: "Cluster 1"}
VENDOR_ORDER = ["GE", "Siemens"]


def _legend(ax, entries, p: Palette, loc="upper right", ncol=1, **kw):
    handles = [Line2D([], [], color=c, marker="o", linestyle="none", markersize=6, label=l)
               for l, c in entries]
    leg = ax.legend(handles=handles, loc=loc, ncol=ncol, **kw)
    for t in leg.get_texts():
        t.set_color(p.ink)
    return leg


# ------------------------------------------------------------------ 1. scree
def scree(fig, p: Palette):
    v = d("pca_variance.csv").head(20)
    ax = fig.add_subplot(111)
    hairline_grid(ax, "y", p)
    ax.bar(v.pc, v.explained_variance_ratio * 100, width=0.62, color=p.a, zorder=3)
    ax2 = ax.twinx()
    ax2.plot(v.pc, v.cumulative * 100, color=p.b, marker="o", markersize=3.4, zorder=4)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("cumulative variance (%)", color=p.muted)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(p.rule)
    ax2.grid(False)

    cum10 = float(v.cumulative.iloc[9]) * 100
    ax2.annotate(f"top 10 PCs\n{cum10:.1f}% of variance",
                 xy=(10, cum10), xytext=(12.4, cum10 - 26), fontsize=8.6, color=p.b,
                 ha="left", va="center",
                 arrowprops=dict(arrowstyle="-", color=p.b, lw=0.9,
                                 connectionstyle="angle,angleA=0,angleB=90,rad=6"))
    ax.set_xticks(range(1, 21, 2))
    ax.set_xlabel("principal component")
    ax.set_ylabel("variance explained (%)")
    title(ax, "Variance declines smoothly — no natural cut",
          "There is no elbow, so any k is a modelling choice rather than a discovery.", p)


# --------------------------------------------------------------- 2. k metrics
def validity(fig, p: Palette):
    m = d("kmeans_validity_metrics.csv")
    specs = [("silhouette", "Silhouette", "higher is better"),
             ("calinski_harabasz", "Calinski–Harabasz", "higher is better"),
             ("davies_bouldin", "Davies–Bouldin", "lower is better")]
    axes = fig.subplots(1, 3)
    for ax, (col, name, hint) in zip(axes, specs):
        hairline_grid(ax, "y", p)
        wins = m[col].idxmax() if col != "davies_bouldin" else m[col].idxmin()
        best_k = int(m.k[wins])
        colors = [p.b if k == best_k else p.rule for k in m.k]
        ax.bar(m.k, m[col], width=0.6, color=colors, zorder=3)
        for k, v in zip(m.k, m[col]):
            ax.annotate(f"{v:.3g}", xy=(k, v), xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=7.6,
                        color=p.ink if k == best_k else p.muted)
        ax.set_ylim(top=float(m[col].max()) * 1.16)
        ax.set_xticks(m.k)
        ax.set_xlabel("k")
        ax.annotate(f"best: k = {best_k}", xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 1), textcoords="offset points", fontsize=7.6,
                    color=p.b if best_k == 2 else p.muted, va="bottom")
        panel_title(ax, name, hint, p)
    axes[2].annotate("k = 2 is the worst\nsolution on this metric —\nthe selection rests\non the other two",
                     xy=(0.5, 0.58), xycoords="axes fraction", ha="center", va="top",
                     fontsize=7.8, color=p.muted, linespacing=1.5)
    fig.subplots_adjust(wspace=0.34)


# ------------------------------------------------- 3. the PCA overlap (Fig 5)
def pca_dual(fig, p: Palette):
    q = d("patients.csv")
    axes = fig.subplots(1, 2, sharex=True, sharey=True)
    q = q.sample(frac=1.0, random_state=7)
    panels = [("cluster_raw", {0: p.a, 1: p.b}, CLUSTER_LABEL,
               "Colored by radiomic cluster", None),
              ("manufacturer", {"GE": p.a, "Siemens": p.b}, {v: v for v in VENDOR_ORDER},
               "Colored by manufacturer", None)]
    for ax, (col, cmap, labels, head, deck) in zip(axes, panels):
        for key, colour in cmap.items():
            s = q[q[col] == key]
            ax.scatter(s.PC1, s.PC2, s=7, c=colour, alpha=0.55, linewidths=0, zorder=3)
        ax.set_xlabel("PC1  (15.5% of variance)")
        panel_title(ax, head, deck, p)
        _legend(ax, [(l, cmap[k]) for k, l in labels.items()], p, loc="lower right")
    axes[0].set_ylabel("PC2  (9.6%)")
    fig.subplots_adjust(wspace=0.12)


# ----------------------------------------------------- 4. separating features
def features(fig, p: Palette):
    t = d("top_cluster_features.csv").head(14).iloc[::-1]
    pretty = (t.feature.str.replace("_", " ", regex=False)
              .str.replace(" tissue T1", " (T1)", regex=False)
              .str.replace(" tumor", " (tumour)", regex=False))
    y = np.arange(len(t))
    ax = fig.add_subplot(111)
    hairline_grid(ax, "x", p)
    ax.hlines(y, t.mean_cluster0, t.mean_cluster1, color=p.rule, lw=1.6, zorder=2)
    ax.scatter(t.mean_cluster0, y, s=34, c=p.a, zorder=3)
    ax.scatter(t.mean_cluster1, y, s=34, c=p.b, zorder=3)
    for i, dv in zip(y, t.cohens_d):
        ax.annotate(f"d = {dv:.2f}", xy=(max(t.mean_cluster1.iloc[i], t.mean_cluster0.iloc[i]), i),
                    xytext=(8, 0), textcoords="offset points", fontsize=7.8,
                    color=p.muted, va="center")
    ax.axvline(0, color=p.rule, lw=0.8, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(pretty, fontsize=8)
    ax.set_xlim(right=float(t.mean_cluster1.max()) + 0.75)
    ax.set_xlabel("cluster mean (z-scored feature units)")
    ax.spines["left"].set_visible(False)
    _legend(ax, [("Cluster 0", p.a), ("Cluster 1", p.b)], p, loc="lower right")
    title(ax, "The separating features read as vascularity",
          "Enhancement and texture descriptors — biologically plausible language for a technical split.", p)


# ------------------------------------------------ 5. manufacturer composition
def composition(fig, p: Palette):
    c = d("cluster_by_manufacturer_counts.csv").set_index("Cluster")
    pct = c.div(c.sum(axis=1), axis=0) * 100
    ax = fig.add_subplot(111)
    y = np.arange(len(pct))
    left = np.zeros(len(pct))
    for vendor, colour in zip(VENDOR_ORDER, (p.a, p.b)):
        ax.barh(y, pct[vendor], left=left, height=0.46, color=colour, zorder=3)
        for i, (val, l) in enumerate(zip(pct[vendor], left)):
            if val > 8:
                ax.annotate(f"{val:.0f}%  ({c[vendor].iloc[i]})", xy=(l + val / 2, i),
                            ha="center", va="center", fontsize=8.4, color=p.paper,
                            fontweight="semibold", zorder=4)
        left += pct[vendor].to_numpy()
    ax.set_yticks(y)
    ax.set_yticklabels([CLUSTER_LABEL[i] for i in pct.index], fontsize=9.5, color=p.ink)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of cluster (%)")
    ax.invert_yaxis()
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    _legend(ax, list(zip(VENDOR_ORDER, (p.a, p.b))), p, loc="lower center",
            ncol=2, bbox_to_anchor=(0.5, -0.34))
    title(ax, "Each cluster is a scanner",
          "The partition the pipeline discovered is, to first order, the vendor split.", p)


# ---------------------------------------------------- 6. acquisition dominance
def eta_squared(fig, p: Palette):
    e = d("acquisition_eta2.csv").sort_values("PC1")
    ax = fig.add_subplot(111)
    hairline_grid(ax, "x", p)
    y = np.arange(len(e))
    colours = [p.b if k == "Technical" else p.a for k in e.kind]
    ax.hlines(y, 0, e.PC1, color=colours, lw=2.2, alpha=0.45, zorder=2)
    ax.scatter(e.PC1, y, s=52, c=colours, zorder=3)
    for i, (v, k) in enumerate(zip(e.PC1, e.kind)):
        ax.annotate(f"{v:.3f}", xy=(v, i), xytext=(9, 0), textcoords="offset points",
                    fontsize=8.2, color=p.ink if k == "Technical" else p.muted, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels(e.variable, fontsize=8.8)
    ax.set_xlim(0, max(0.85, float(e.PC1.max()) * 1.22))
    ax.set_xlabel("η²  —  share of PC1 variance explained")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _legend(ax, [("Acquisition variable", p.b), ("Biological variable", p.a)], p,
            loc="lower right")
    title(ax, "The leading axis is built out of acquisition",
          "Biology explains less than 1% of PC1. The scanner explains most of it.", p)


# ------------------------------------------------------------ 7. Kaplan–Meier
def kaplan_meier(fig, p: Palette):
    km = d("km_hrher2.csv")
    risk = d("km_at_risk.csv")
    s = d("survival_outcome_summary.csv").set_index("Cluster")
    gs = fig.add_gridspec(2, 1, height_ratios=[3.5, 1], hspace=0.32)
    ax, tab = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    xmax = 8.0
    for cl, colour in ((0, p.a), (1, p.b)):
        g = km[km.cluster == cl].sort_values("t")
        t = np.append(g.t.to_numpy(), xmax)
        ax.step(t, np.append(g.surv, g.surv.iloc[-1]), where="post", color=colour, zorder=4)
        ax.fill_between(t, np.append(g.lo, g.lo.iloc[-1]), np.append(g.hi, g.hi.iloc[-1]),
                        step="post", color=colour, alpha=0.11, linewidth=0, zorder=2)
        ax.annotate(f"Cluster {cl}   {int(s.events[cl])}/{int(s.n[cl])} events"
                    f"  ({s.event_rate[cl]*100:.1f}%)",
                    xy=(xmax, g.surv.iloc[-1]), xytext=(-4, 8 if cl == 0 else -14),
                    textcoords="offset points", ha="right", fontsize=8.6, color=colour)
    hairline_grid(ax, "y", p)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0.55, 1.005)
    ax.set_ylabel("recurrence-free survival")
    ax.set_xlabel("years since diagnosis")
    title(ax, "The signal that looked like a phenotype",
          "HR+/HER2+ subgroup, unadjusted:  log-rank p = 0.010,  HR = 4.76 (95% CI 1.22–18.61).", p)

    tab.axis("off")
    grid = sorted(risk.t.unique())
    tab.annotate("at risk", xy=(0, 1.15), xycoords="axes fraction", fontsize=8,
                 color=p.muted, ha="left")
    for cl, colour, row in ((0, p.a, 0.62), (1, p.b, 0.16)):
        tab.annotate(f"Cluster {cl}", xy=(-0.02, row), xycoords="axes fraction",
                     fontsize=8.2, color=colour, ha="right", va="center")
        for gt in grid:
            n = int(risk[(risk.cluster == cl) & (risk.t == gt)].n_risk.iloc[0])
            tab.annotate(str(n), xy=(gt / xmax, row), xycoords="axes fraction",
                         fontsize=8.2, color=p.muted,
                         ha="left" if gt == 0 else "center", va="center")
    tab.set_xlim(0, 1)


# ------------------------------------------- 8. stability vs identity (new)
def stability_identity(fig, p: Palette):
    st = d("stability_summary_raw_resid_combat.csv")
    ax = fig.add_subplot(111)
    ax.add_patch(Rectangle((0.5, -0.08), 0.56, 0.36, facecolor=p.b, alpha=0.06,
                           linewidth=0, zorder=1))
    ax.annotate("THE STABILITY TRAP", xy=(0.515, 0.225), fontsize=8.4, color=p.b,
                fontweight="semibold", va="top", zorder=2)
    ax.annotate("as reproducible as the original,\nbut no longer the same phenotype",
                xy=(0.515, 0.175), fontsize=8.2, color=p.b, va="top",
                linespacing=1.45, alpha=0.85, zorder=2)
    # label offsets, hand-placed: Residualized and ComBat sit almost on top of each other
    place = {"Raw":          ("Raw discovery",             0,  18, "center"),
             "Residualized": ("Manufacturer residualized", 12, 20, "left"),
             "ComBat":       ("ComBat harmonized",        -12, -30, "right")}
    for _, r in st.iterrows():
        colour = p.a if r.Condition == "Raw" else p.b
        label, dx, dy, ha = place[r.Condition]
        ax.errorbar(r.Mean_ARI, r.ARI_vs_raw, xerr=r.SD_ARI, fmt="o", markersize=9,
                    color=colour, ecolor=colour, elinewidth=1.1, capsize=0, alpha=0.95,
                    zorder=4)
        ax.annotate(f"{label}\nidentity {r.ARI_vs_raw:.3f}",
                    xy=(r.Mean_ARI, r.ARI_vs_raw), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, fontsize=8.6, color=p.ink,
                    linespacing=1.5, zorder=5,
                    arrowprops=None if r.Condition == "Raw" else
                    dict(arrowstyle="-", color=p.rule, lw=0.8,
                         shrinkA=2, shrinkB=8))
    hairline_grid(ax, "y", p)
    ax.set_xlim(0.5, 1.06)
    ax.set_ylim(-0.14, 1.22)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("cluster stability  —  mean bootstrap ARI  (±SD)")
    ax.set_ylabel("partition identity  —  ARI vs the raw labels")
    title(ax, "Stability and identity are independent axes",
          "Harmonization left the clusters just as reproducible while replacing the patients in them.", p)


# ----------------------------------------------------- 9. bootstrap stability
def bootstrap(fig, p: Palette):
    st = d("stability_summary_raw_resid_combat.csv")
    raw = d("bootstrap_ari_results.csv")
    ax = fig.add_subplot(111)
    hairline_grid(ax, "x", p)
    order = ["Raw", "Residualized", "ComBat"]
    names = {"Raw": "Raw", "Residualized": "Residualized", "ComBat": "ComBat"}
    for i, cond in enumerate(order):
        r = st[st.Condition == cond].iloc[0]
        colour = p.a if cond == "Raw" else p.b
        ax.errorbar(r.Mean_ARI, i, xerr=r.SD_ARI, fmt="o", markersize=8, color=colour,
                    ecolor=colour, elinewidth=1.2, alpha=0.95, zorder=4)
        ax.annotate(f"{r.Mean_ARI:.3f}", xy=(r.Mean_ARI, i), xytext=(0, 13),
                    textcoords="offset points", ha="center", fontsize=8.4, color=p.ink)
        if cond == "Raw":
            rng = np.random.default_rng(42)
            ax.scatter(raw.ARI, i + rng.uniform(-0.09, 0.09, len(raw)), s=13,
                       c=colour, alpha=0.32, linewidths=0, zorder=3)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([names[c] for c in order], fontsize=9.5, color=p.ink)
    ax.set_ylim(-0.6, len(order) - 0.25)
    ax.set_xlim(0.6, 1.02)
    ax.invert_yaxis()
    ax.set_xlabel("bootstrap ARI  (20 × 80% subsamples)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    title(ax, "Every condition passes the stability check",
          "Which is exactly why stability cannot be the check.", p)


# --------------------------------------- 10. identity scramble after residualizing
def identity_scramble(fig, p: Palette):
    q = d("patients.csv").dropna(subset=["cluster_resid"]).sample(frac=1.0, random_state=7)
    axes = fig.subplots(1, 2, sharex=True, sharey=True)
    for ax, (col, head, deck) in zip(axes, [
            ("cluster_raw", "Raw clusters", None),
            ("cluster_resid", "Manufacturer-residualized clusters", None)]):
        for key, colour in ((0, p.a), (1, p.b)):
            s = q[q[col] == key]
            ax.scatter(s.PC1, s.PC2, s=7, c=colour, alpha=0.55, linewidths=0, zorder=3)
        ax.set_xlabel("PC1")
        panel_title(ax, head, deck, p)
    axes[0].set_ylabel("PC2")
    fig.subplots_adjust(wspace=0.12)


FIGURES = {
    "fig-scree": (scree, (7.4, 4.3)),
    "fig-validity": (validity, (7.6, 3.2)),
    "fig-pca-dual": (pca_dual, (7.8, 4.0)),
    "fig-features": (features, (7.6, 5.4)),
    "fig-composition": (composition, (7.2, 3.2)),
    "fig-eta2": (eta_squared, (7.4, 4.2)),
    "fig-km": (kaplan_meier, (7.4, 5.0)),
    "fig-stability-identity": (stability_identity, (7.4, 4.6)),
    "fig-bootstrap": (bootstrap, (7.2, 3.4)),
    "fig-identity-scramble": (identity_scramble, (7.8, 4.0)),
}


def build_all():
    for name, (fn, size) in FIGURES.items():
        render(fn, name, figsize=size)
        print("  rendered", name)


# ------------------------------- single-panel PCA views for the in-page toggle
def _pca_single(col: str, cmap: dict, labels: dict, deck: str):
    def build(fig, p: Palette):
        q = d("patients.csv").sample(frac=1.0, random_state=7)
        ax = fig.add_subplot(111)
        colours = {k: (p.a if v == "a" else p.b) for k, v in cmap.items()}
        for key, colour in colours.items():
            s = q[q[col] == key]
            ax.scatter(s.PC1, s.PC2, s=8, c=colour, alpha=0.55, linewidths=0, zorder=3)
        ax.set_xlim(-32, 56)
        ax.set_ylim(-24, 28)
        ax.set_xlabel("PC1  (15.5% of variance)")
        ax.set_ylabel("PC2  (9.6%)")
        _legend(ax, [(l, colours[k]) for k, l in labels.items()], p, loc="lower right")
        title(ax, deck, None, p)
    return build


pca_by_cluster = _pca_single("cluster_raw", {0: "a", 1: "b"}, CLUSTER_LABEL, "")
pca_by_vendor = _pca_single("manufacturer", {"GE": "a", "Siemens": "b"},
                            {"GE": "GE", "Siemens": "Siemens"}, "")

FIGURES["fig-pca-by-cluster"] = (pca_by_cluster, (6.6, 4.2))
FIGURES["fig-pca-by-vendor"] = (pca_by_vendor, (6.6, 4.2))


# ------------------------------------------- listing-card thumbnail (180px tall)
def thumbnail(fig, p: Palette):
    """Legible at card size: no axes, big marks, two words of label."""
    q = d("patients.csv").sample(frac=1.0, random_state=7)
    axes = fig.subplots(1, 2, sharex=True, sharey=True)
    specs = [("cluster_raw", {0: p.a, 1: p.b}, "the clusters"),
             ("manufacturer", {"GE": p.a, "Siemens": p.b}, "the scanners")]
    for ax, (col, cmap, label) in zip(axes, specs):
        for key, colour in cmap.items():
            s = q[q[col] == key]
            ax.scatter(s.PC1, s.PC2, s=15, c=colour, alpha=0.6, linewidths=0)
        ax.set_xlim(-32, 30)
        ax.set_ylim(-24, 28)
        ax.set_xticks([]); ax.set_yticks([])
        for side in ax.spines:
            ax.spines[side].set_visible(False)
        ax.annotate(label, xy=(0.5, -0.02), xycoords="axes fraction", ha="center",
                    va="top", fontsize=12, color=p.muted, fontfamily="serif",
                    fontstyle="italic")
    fig.subplots_adjust(wspace=0.06, bottom=0.12, top=0.98, left=0.02, right=0.98)


FIGURES["fig-thumb"] = (thumbnail, (7.2, 3.1))


# --- two figures the manuscript has that were missing from the first port ----

def pca_projection(fig, p: Palette):
    """Figure 2. Projection of patients onto PC1 and PC2 (unlabelled)."""
    q = d("patients.csv")
    ax = fig.add_subplot(111)
    ax.scatter(q.PC1, q.PC2, s=8, c=p.muted, alpha=0.45, linewidths=0, zorder=3)
    ax.set_xlabel("PC1  (15.5% of variance)")
    ax.set_ylabel("PC2  (9.6% of variance)")


def cluster_within_manufacturer(fig, p: Palette):
    """Supplementary Figure S1. Raw cluster distribution within each manufacturer."""
    c = d("cluster_by_manufacturer_counts.csv").set_index("Cluster")
    within = (c / c.sum(axis=0) * 100).T          # rows = manufacturer
    ax = fig.add_subplot(111)
    y = np.arange(len(within))
    left = np.zeros(len(within))
    for cl, colour in zip(within.columns, (p.a, p.b)):
        ax.barh(y, within[cl], left=left, height=0.46, color=colour, zorder=3)
        for i, (val, l) in enumerate(zip(within[cl], left)):
            if val > 8:
                ax.annotate(f"{val:.0f}%  ({c[cl] if False else c.loc[cl, within.index[i]]})",
                            xy=(l + val / 2, i), ha="center", va="center", fontsize=8.4,
                            color=p.paper, fontweight="semibold", zorder=4)
        left += within[cl].to_numpy()
    ax.set_yticks(y)
    ax.set_yticklabels(within.index, fontsize=9.5, color=p.ink)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of manufacturer (%)")
    ax.invert_yaxis()
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    _legend(ax, [(CLUSTER_LABEL[cl], col) for cl, col in zip(within.columns, (p.a, p.b))],
            p, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.34))


FIGURES["fig-pca-projection"] = (pca_projection, (7.0, 4.4))
FIGURES["fig-cluster-within-manufacturer"] = (cluster_within_manufacturer, (7.2, 3.2))
