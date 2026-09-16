"""Figure builders for the Baltic day-ahead price forecasting paper.

Each builder is a function of (fig, palette) and is rendered once per site theme
by `_theme.render`. Nothing here reads from outside `_data/`, so the whole figure
set rebuilds from the committed evaluation output.

A note on `_data/*_hourly_metrics.csv` and `_data/*_daily_metrics.csv`: those two
files come from the volatile-period analysis and describe each zone's most
volatile 21 days, not the full sample. Full-sample profiles are recomputed here
from the forecast archive.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from _theme import (DATA, MODEL_NAME, MODELS, SYNC_DATE, ZONE_NAME, ZONES,
                    Palette, hairline_grid, panel_title, render, zone_legend)

HOURS = range(24)


# ------------------------------------------------------------------- loading
def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


_FC_CACHE: dict[str, pd.DataFrame] = {}


def forecasts(zone: str) -> pd.DataFrame:
    """Wide daily frame: actual_h0..23 and one block of 24 per model."""
    if zone not in _FC_CACHE:
        df = pd.read_csv(DATA / f"{zone}_forecasts_all.csv.gz",
                         index_col=0, parse_dates=True)
        df.index.name = "date"
        _FC_CACHE[zone] = df
    return _FC_CACHE[zone]


def matrices(zone: str, model: str = "LEAR_ensemble"):
    """(dates, actual[N,24], forecast[N,24]) for one zone and model."""
    df = forecasts(zone)
    a = df[[f"actual_h{h}" for h in HOURS]].to_numpy(float)
    f = df[[f"{model}_h{h}" for h in HOURS]].to_numpy(float)
    return df.index, a, f


def daily_mae(zone: str, model: str = "LEAR_ensemble") -> pd.Series:
    idx, a, f = matrices(zone, model)
    return pd.Series(np.abs(a - f).mean(axis=1), index=idx)


def pick(df: pd.DataFrame, **eq) -> pd.DataFrame:
    """Rows matching every column == value. Plain masking, no query namespace."""
    mask = pd.Series(True, index=df.index)
    for k, v in eq.items():
        mask &= df[k] == v
    return df[mask]


def one(df: pd.DataFrame, col: str, **eq) -> float:
    return float(pick(df, **eq)[col].iloc[0])


def metrics() -> pd.DataFrame:
    return _csv("all_metrics.csv")


def _sync_marker(ax, p: Palette, label: bool = True, y: float = 0.97):
    """The 9 February 2025 synchronisation, drawn as context, not as a series."""
    x = pd.Timestamp(SYNC_DATE)
    ax.axvline(x, color=p.faint, lw=1.0, ls=(0, (4, 3)), zorder=2)
    if label:
        ax.annotate("9 Feb 2025\nsynchronisation", xy=(x, y),
                    xycoords=("data", "axes fraction"), xytext=(5, 0),
                    textcoords="offset points", fontsize=7.6, color=p.faint,
                    va="top", ha="left", linespacing=1.4)


def _zone_cmap(z: str, p: Palette):
    """A single-hue density ramp in the zone's own colour, on the page surface."""
    lo, mid, hi = p.ramp[z]
    near = "#e8f0fb" if p.name == "light" else "#1d2430"
    return LinearSegmentedColormap.from_list(f"{z}-{p.name}", [near, lo, mid, hi])


# ------------------------------------------------------- 1. the price series
def prices(fig, p: Palette):
    """Daily mean day-ahead price per zone, with the daily min-max range."""
    axes = fig.subplots(3, 1, sharex=True, sharey=True)
    for ax, z in zip(axes, ZONES):
        df = forecasts(z)
        a = df[[f"actual_h{h}" for h in HOURS]].to_numpy(float)
        idx = df.index
        lo, hi, mean = a.min(axis=1), a.max(axis=1), a.mean(axis=1)
        smooth = pd.Series(mean, index=idx).rolling(7, center=True,
                                                    min_periods=4).mean()
        hairline_grid(ax, "y", p)
        ax.fill_between(idx, lo, hi, color=p.zone[z], alpha=0.14,
                        linewidth=0, zorder=3)
        ax.plot(idx, mean, color=p.zone[z], lw=0.6, alpha=0.55, zorder=4)
        ax.plot(idx, smooth.values, color=p.zone[z], lw=1.9, zorder=5)
        _sync_marker(ax, p, label=(z == "EE"), y=0.99)
        ax.set_ylim(-60, 480)
        ax.set_yticks([0, 150, 300, 450])
        panel_title(ax, ZONE_NAME[z], None, p)
        ax.annotate(f"daily range peaks at €{hi.max():,.0f}/MWh, above the axis",
                    xy=(0.997, 1.02), xycoords="axes fraction", ha="right",
                    va="bottom", fontsize=7.6, color=p.muted)
    axes[1].set_ylabel("day-ahead price  (€/MWh)")
    axes[-1].set_xlabel("delivery day")
    leg = fig.legend(handles=[Line2D([], [], color=p.zone["EE"], lw=2.2,
                                     label="7-day mean"),
                              Line2D([], [], color=p.zone["EE"], lw=0.9, alpha=0.55,
                                     label="daily mean"),
                              Line2D([], [], color=p.zone["EE"], lw=7, alpha=0.25,
                                     label="daily low–high range")],
                     loc="lower left", ncol=3, bbox_to_anchor=(0.10, 0.985),
                     frameon=False)
    for t in leg.get_texts():
        t.set_color(p.ink)
    fig.subplots_adjust(hspace=0.46, top=0.93)


# --------------------------------------------------- 2. what feeds the model
def design(fig, p: Palette):
    """Left: the 247-predictor lag structure. Right: daily recalibration."""
    axes = fig.subplots(1, 2, width_ratios=[1.0, 0.95])
    seq = p.sequential

    # ---- panel A: which lags enter each hourly equation
    ax = axes[0]
    rows = [("day-ahead price", [7, 3, 2, 1], 96),
            ("day-ahead load forecast", [7, 1, 0], 72),
            ("day-ahead wind forecast", [7, 1, 0], 72)]
    lags = [7, 3, 2, 1, 0]
    xpos = {lag: i * 1.15 for i, lag in enumerate(lags)}
    right = xpos[0] + 0.75
    for r, (label, used, count) in enumerate(rows):
        y = len(rows) - 1 - r
        for lag in lags:
            on = lag in used
            ax.add_patch(Rectangle((xpos[lag] - 0.44, y - 0.28), 0.88, 0.56,
                                   facecolor=seq[5] if on else p.paper2,
                                   edgecolor=p.paper, linewidth=1.8, zorder=3))
            if on:
                ax.annotate("24", xy=(xpos[lag], y), ha="center", va="center",
                            fontsize=7.4, color=p.paper, zorder=4)
        ax.annotate(label, xy=(-0.85, y), ha="right", va="center",
                    fontsize=8.6, color=p.ink)
        ax.annotate(f"{count}", xy=(right, y), ha="left", va="center",
                    fontsize=8.6, color=p.muted)
    ax.add_patch(Rectangle((xpos[0] - 0.44, -1.28), 0.88, 0.56,
                           facecolor=seq[3], edgecolor=p.paper, linewidth=1.8, zorder=3))
    ax.annotate("7", xy=(xpos[0], -1.0), ha="center", va="center",
                fontsize=7.4, color=p.ink, zorder=4)
    ax.annotate("day-of-week dummies", xy=(-0.85, -1.0), ha="right", va="center",
                fontsize=8.6, color=p.ink)
    ax.annotate("7", xy=(right, -1.0), ha="left", va="center",
                fontsize=8.6, color=p.muted)
    ax.plot([-0.85, right + 0.55], [-1.72, -1.72], color=p.rule, lw=0.9, zorder=3)
    ax.annotate("247 candidate predictors", xy=(right + 0.55, -2.08),
                ha="right", va="center", fontsize=9.0, color=p.ink)
    ax.set_xticks(list(xpos.values()))
    ax.set_xticklabels([("day $d$" if l == 0 else f"$d\\!-\\!{l}$") for l in lags],
                       fontsize=8.2)
    ax.set_xlim(-4.6, right + 0.9)
    ax.set_ylim(-2.5, 2.9)
    ax.set_yticks([])
    for side in ax.spines:
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    panel_title(ax, "Inputs", "one filled cell = 24 hourly values", p)

    # ---- panel B: the rolling calibration windows
    ax = axes[1]
    for k, lab in enumerate(["day $D$", "$D+1$", "$D+2$"]):
        y = 2 - k          # D on top, later days below and further right
        off = k
        for w, (span, colour, name) in enumerate(
                [(84, seq[2], "12-week window"), (56, seq[5], "8-week window")]):
            ax.add_patch(Rectangle((off - span, y - 0.20 + w * 0.22), span, 0.19,
                                   facecolor=colour, edgecolor="none", zorder=3))
            if k == 0:
                ax.annotate(name, xy=(off - span, y - 0.105 + w * 0.22),
                            xytext=(-7, 0), textcoords="offset points",
                            ha="right", va="center", fontsize=7.8, color=p.muted)
        ax.scatter([off + 1.5], [y], s=32, color=p.accent, zorder=5, linewidths=0)
        ax.annotate(lab, xy=(off + 1.5, y), xytext=(8, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8.4, color=p.ink)
    ax.annotate("refitted from scratch every delivery day", xy=(-42, -0.75),
                ha="center", va="center", fontsize=8.0, color=p.muted)
    ax.set_xlim(-118, 22)
    ax.set_ylim(-1.35, 3.3)
    ax.set_xticks([-84, -56, -28, 0])
    ax.set_xticklabels(["12 wk\nback", "8 wk\nback", "4 wk\nback", "gate\nclosure"],
                       fontsize=7.8, linespacing=1.4)
    ax.set_yticks([])
    for side in ax.spines:
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    panel_title(ax, "Estimation", "no information after gate closure enters the fit", p)
    fig.subplots_adjust(wspace=0.06)


# ------------------------------------------------------ 3. headline accuracy
def rmae(fig, p: Palette):
    """rMAE by zone and specification, against the weekly naive benchmark."""
    m = pick(metrics(), period="overall")
    ax = fig.add_subplot(111)
    hairline_grid(ax, "y", p)
    width = 0.24
    base = np.arange(len(ZONES))
    for j, model in enumerate(MODELS):
        xs = base + (j - 1) * width
        vals = [one(m, "rMAE", country=z, model=model) for z in ZONES]
        ax.bar(xs, vals, width=width * 0.86, color=[p.ramp[z][j] for z in ZONES],
               zorder=3)
        for x, v in zip(xs, vals):
            ax.annotate(f"{v:.3f}", xy=(x, v), xytext=(0, 4),
                        textcoords="offset points", ha="center", fontsize=7.8,
                        color=p.ink)
    ax.axhline(1.0, color=p.muted, lw=1.1, ls=(0, (4, 3)), zorder=4)
    ax.annotate("weekly naive benchmark  (rMAE = 1)", xy=(len(ZONES) - 0.55, 1.0),
                xytext=(0, 5), textcoords="offset points", ha="right",
                fontsize=8.0, color=p.muted)
    ax.set_xticks(base)
    ax.set_xticklabels([ZONE_NAME[z] for z in ZONES], fontsize=10, color=p.ink)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("rMAE   (model MAE ÷ naive MAE)")
    ax.legend(handles=[Line2D([], [], color=p.ramp["EE"][j], lw=7,
                              label=MODEL_NAME[m_]) for j, m_ in enumerate(MODELS)],
              loc="upper left", ncol=3, bbox_to_anchor=(0, 1.04))
    for t in ax.get_legend().get_texts():
        t.set_color(p.ink)
    ax.annotate("bars run 8w · 12w · ensemble, left to right, in every zone",
                xy=(0.995, -0.15), xycoords="axes fraction", ha="right",
                fontsize=7.6, color=p.muted, annotation_clip=False)


# ----------------------------------------------------- 4. the gap over naive
def naive_gap(fig, p: Palette):
    """How far the ensemble moves MAE away from 'last week, same hour'."""
    m = pick(metrics(), period="overall", model="LEAR_ensemble")
    ax = fig.add_subplot(111)
    hairline_grid(ax, "x", p)
    for i, z in enumerate(ZONES):
        y = len(ZONES) - 1 - i
        row = pick(m, country=z).iloc[0]
        mae, r = float(row.MAE), float(row.rMAE)
        naive = mae / r
        ax.plot([mae, naive], [y, y], color=p.rule, lw=3.2, zorder=3,
                solid_capstyle="round")
        ax.scatter([naive], [y], s=64, color=p.faint, zorder=4, linewidths=0)
        ax.scatter([mae], [y], s=96, color=p.zone[z], zorder=5, linewidths=0)
        ax.annotate(f"€{mae:.2f}", xy=(mae, y), xytext=(0, 11),
                    textcoords="offset points", ha="center", fontsize=8.4, color=p.ink)
        ax.annotate(f"€{naive:.2f}", xy=(naive, y), xytext=(0, 11),
                    textcoords="offset points", ha="center", fontsize=8.4, color=p.muted)
        ax.annotate(f"−{(1 - r) * 100:.1f}%", xy=((mae + naive) / 2, y),
                    xytext=(0, -16), textcoords="offset points", ha="center",
                    fontsize=9.2, color=p.zone[z])
    ax.set_yticks(range(len(ZONES)))
    ax.set_yticklabels([ZONE_NAME[z] for z in reversed(ZONES)], fontsize=10, color=p.ink)
    ax.set_ylim(-0.75, len(ZONES) - 0.30)
    ax.set_xlim(29, 55)
    ax.set_xlabel("mean absolute error over 964 days  (€/MWh)")
    ax.legend(handles=[Line2D([], [], color=p.faint, marker="o", ls="none",
                              markersize=7, label="weekly naive"),
                       Line2D([], [], color=p.zone["EE"], marker="o", ls="none",
                              markersize=8, label="short-window ensemble")],
              loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12))
    for t in ax.get_legend().get_texts():
        t.set_color(p.ink)


# ------------------------------------------------------- 5. accuracy in time
def rolling(fig, p: Palette):
    """28-day rolling MAE of the ensemble in all three zones."""
    ax = fig.add_subplot(111)
    hairline_grid(ax, "y", p)
    for z in ZONES:
        s = daily_mae(z).rolling(28).mean().dropna()
        ax.plot(s.index, s.values, color=p.zone[z], lw=1.7, zorder=4)
    _sync_marker(ax, p, y=0.99)
    ax.set_ylabel("28-day rolling MAE  (€/MWh)")
    ax.set_xlabel("delivery day")
    ax.set_ylim(0, None)
    zone_legend(ax, p, loc="upper left", ncol=3, bbox_to_anchor=(0, 1.12))


# ------------------------------------------------------ 6. the daily profile
def hourly(fig, p: Palette):
    """Where in the day the error sits, over the full sample and under stress."""
    ax = fig.add_subplot(111)
    hairline_grid(ax, "y", p)
    for z in ZONES:
        _, a, f = matrices(z)
        full = np.nanmean(np.abs(a - f), axis=0)
        ax.plot(range(24), full, color=p.zone[z], lw=2.1, zorder=5)
        hot = pick(_csv(f"{z}_hourly_metrics.csv"), model="LEAR_ensemble") \
            .sort_values("hour")
        ax.plot(hot.hour, hot.MAE, color=p.zone[z], lw=1.3, alpha=0.55,
                ls=(0, (3, 2)), zorder=4)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 3)])
    ax.set_xlim(-0.6, 23.6)
    ax.set_xlabel("delivery hour  (local time)")
    ax.set_ylabel("MAE  (€/MWh)")
    ax.set_ylim(0, None)
    style = ax.legend(handles=[Line2D([], [], color=p.muted, lw=2.1,
                                      label="full 964 days"),
                               Line2D([], [], color=p.muted, lw=1.3, alpha=0.7,
                                      ls=(0, (3, 2)), label="most volatile 21 days")],
                      loc="upper left", ncol=1, bbox_to_anchor=(0.005, 0.99))
    for t in style.get_texts():
        t.set_color(p.ink)
    ax.add_artist(style)
    zone_legend(ax, p, loc="upper left", ncol=3, bbox_to_anchor=(0, 1.12))


# ------------------------------------------------------ 7. the error tails
def errdist(fig, p: Palette):
    """Signed ensemble error: a tight centre and a very long tail."""
    ax = fig.add_subplot(111)
    hairline_grid(ax, "x", p)
    lim = 220
    for i, z in enumerate(ZONES):
        y = len(ZONES) - 1 - i
        _, a, f = matrices(z)
        e = (a - f).ravel()
        e = e[~np.isnan(e)]
        parts = ax.violinplot([np.clip(e, -lim, lim)], positions=[y], vert=False,
                              widths=0.72, showextrema=False, showmedians=False)
        for body in parts["bodies"]:
            body.set_facecolor(p.zone[z])
            body.set_alpha(0.50)
            body.set_linewidth(0)
        q05, q25, q75, q95 = np.percentile(e, [5, 25, 75, 95])
        ax.plot([q05, q95], [y, y], color=p.zone[z], lw=1.4, zorder=5)
        ax.plot([q25, q75], [y, y], color=p.zone[z], lw=5.4, zorder=6,
                solid_capstyle="butt")
        ax.scatter([np.median(e)], [y], s=22, color=p.paper, zorder=7, linewidths=0)
        share = float((np.abs(e) > lim).mean() * 100)
        ax.annotate(f"{share:.1f}% of hours land beyond this axis · worst €{np.abs(e).max():,.0f}",
                    xy=(lim, y), xytext=(-2, 30), textcoords="offset points",
                    ha="right", fontsize=7.6, color=p.muted)
    ax.axvline(0, color=p.rule, lw=1.0, zorder=2)
    ax.set_yticks(range(len(ZONES)))
    ax.set_yticklabels([ZONE_NAME[z] for z in reversed(ZONES)], fontsize=10, color=p.ink)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-0.62, len(ZONES) - 0.12)
    ax.set_xlabel("forecast error, actual − forecast  (€/MWh, clipped at ±220)")
    ax.annotate("bar = interquartile range · line = 5th to 95th percentile",
                xy=(0.5, -0.30), xycoords="axes fraction", ha="center",
                fontsize=7.8, color=p.muted)
    ax.annotate("under-forecast →", xy=(0.99, -0.20), xycoords="axes fraction",
                ha="right", fontsize=7.8, color=p.muted)
    ax.annotate("← over-forecast", xy=(0.01, -0.20), xycoords="axes fraction",
                ha="left", fontsize=7.8, color=p.muted)


# --------------------------------------------------- 8. actual vs forecast
def calibration(fig, p: Palette):
    """Every forecast hour against what actually cleared."""
    axes = fig.subplots(1, 3, sharex=True, sharey=True)
    lim = (-60, 520)
    for ax, z in zip(axes, ZONES):
        _, a, f = matrices(z)
        x, y = f.ravel(), a.ravel()
        ok = ~(np.isnan(x) | np.isnan(y))
        ax.plot(lim, lim, color=p.rule, lw=1.0, zorder=2)
        ax.hexbin(x[ok], y[ok], gridsize=46, extent=(*lim, *lim), bins="log",
                  cmap=_zone_cmap(z, p), mincnt=1, linewidths=0, zorder=3)
        ax.set_xlim(*lim)
        ax.set_ylim(*lim)
        ax.set_aspect("equal")
        ax.set_xlabel("forecast  (€/MWh)")
        r = np.corrcoef(x[ok], y[ok])[0, 1]
        ax.annotate(f"r = {r:.3f}", xy=(0.06, 0.94), xycoords="axes fraction",
                    fontsize=8.6, color=p.ink, va="top")
        panel_title(ax, ZONE_NAME[z], None, p)
    axes[0].set_ylabel("actual  (€/MWh)")
    fig.subplots_adjust(wspace=0.16)


# ------------------------------------------------------ 9. around the switch
def sync(fig, p: Palette):
    """The same three metrics, before and after 9 February 2025."""
    m = pick(metrics(), model="LEAR_ensemble")
    specs = [("MAE", "MAE  (€/MWh)", "€{:.2f}"),
             ("RMSE", "RMSE  (€/MWh)", "€{:.2f}"),
             ("rMAE", "rMAE", "{:.3f}")]
    axes = fig.subplots(1, 3)
    for ax, (col, label, fmt) in zip(axes, specs):
        for z in ZONES:
            pre = one(m, col, country=z, period="pre_sync")
            post = one(m, col, country=z, period="post_sync")
            ax.plot([0, 1], [pre, post], color=p.zone[z], lw=2.0, zorder=4)
            ax.scatter([0, 1], [pre, post], s=40, color=p.zone[z], zorder=5,
                       linewidths=1.6, edgecolors=p.paper)
            ax.annotate(fmt.format(pre), xy=(0, pre), xytext=(-7, 0),
                        textcoords="offset points", ha="right", va="center",
                        fontsize=7.8, color=p.muted)
            ax.annotate(fmt.format(post), xy=(1, post), xytext=(7, 0),
                        textcoords="offset points", ha="left", va="center",
                        fontsize=7.8, color=p.ink)
        ax.set_xlim(-0.66, 1.66)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["before", "after"], fontsize=8.6)
        ax.set_yticks([])
        for side in ("left", "bottom"):
            ax.spines[side].set_visible(False)
        ax.tick_params(length=0)
        panel_title(ax, label, None, p)
    axes[1].annotate("each panel carries its own scale; every endpoint is labelled",
                     xy=(0.5, -0.19), xycoords="axes fraction", ha="center",
                     fontsize=7.8, color=p.muted)
    zone_legend(axes[0], p, loc="upper center", ncol=3, bbox_to_anchor=(1.92, 1.30))
    fig.subplots_adjust(wspace=0.60)


# ------------------------------------------------------- 10. under stress
def stress(fig, p: Palette):
    """Full sample against each zone's most volatile 21 days."""
    over = pick(metrics(), period="overall")
    vol = _csv("volatile_21d_model_metrics.csv")
    axes = fig.subplots(1, 2, width_ratios=[1.35, 1.0])

    ax = axes[0]
    hairline_grid(ax, "x", p)
    rows = [(z, m_) for z in ZONES for m_ in MODELS]
    n = len(rows)
    for i, (z, m_) in enumerate(rows):
        y = n - 1 - i
        full = one(over, "rMAE", country=z, model=m_)
        hot = one(vol, "rMAE", country=z, model=m_)
        j = MODELS.index(m_)
        ax.plot([full, hot], [y, y], color=p.rule, lw=2.6, zorder=3,
                solid_capstyle="round")
        ax.scatter([full], [y], s=44, color=p.faint, zorder=4, linewidths=0)
        ax.scatter([hot], [y], s=72, color=p.ramp[z][j], zorder=5, linewidths=0)
        ax.annotate(f"{hot:.3f}", xy=(hot, y), xytext=(8, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=7.8, color=p.ink)
    ax.axvline(1.0, color=p.muted, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.annotate("naive", xy=(1.0, n - 0.45), xytext=(3, 0),
                textcoords="offset points", fontsize=7.6, color=p.muted)
    ax.set_yticks(range(n))
    ax.set_yticklabels([MODEL_NAME[m_] for _, m_ in reversed(rows)], fontsize=8.4)
    for i, z in enumerate(ZONES):
        centre = n - 2 - i * 3          # middle row of the zone's three
        ax.annotate(ZONE_NAME[z], xy=(0, centre), xycoords=("axes fraction", "data"),
                    xytext=(-128, 0), textcoords="offset points", fontsize=9.6,
                    color=p.zone[z], fontfamily="serif", va="center",
                    ha="left", annotation_clip=False)
    ax.set_xlim(0.62, 1.06)
    ax.set_ylim(-0.6, n - 0.3)
    ax.set_xlabel("rMAE")
    leg = ax.legend(handles=[Line2D([], [], color=p.faint, marker="o", ls="none",
                                    markersize=6, label="full 964 days"),
                             Line2D([], [], color=p.zone["LV"], marker="o", ls="none",
                                    markersize=7, label="most volatile 21 days")],
                    loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12))
    for t in leg.get_texts():
        t.set_color(p.ink)

    ax = axes[1]
    hairline_grid(ax, "y", p)
    xs = np.arange(len(ZONES))
    vals = [one(vol, "max_absolute_error", country=z, model="LEAR_ensemble")
            for z in ZONES]
    ax.bar(xs, vals, width=0.5, color=[p.zone[z] for z in ZONES], zorder=3)
    for x, v in zip(xs, vals):
        ax.annotate(f"€{v:,.0f}", xy=(x, v), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8.6, color=p.ink)
    ax.set_xticks(xs)
    ax.set_xticklabels([ZONE_NAME[z] for z in ZONES], fontsize=9, color=p.ink)
    ax.set_ylim(0, 980)
    ax.set_ylabel("worst single hour  (€/MWh)")
    panel_title(ax, "The worst hour", "ensemble, inside the stress window", p)
    fig.subplots_adjust(wspace=0.34)


# ------------------------------------------- 11. inside the stress windows
def stress_trace(fig, p: Palette):
    """Hour by hour through each zone's most volatile 21 days."""
    per = _csv("volatile_periods.csv").set_index("country")
    axes = fig.subplots(3, 1)
    for ax, z in zip(axes, ZONES):
        start, end = per.loc[z, "start_date"], per.loc[z, "end_date"]
        idx, a, f = matrices(z)
        mask = (idx >= start) & (idx <= end)
        act, fc = a[mask].ravel(), f[mask].ravel()
        t = np.arange(len(act)) / 24.0
        hairline_grid(ax, "y", p)
        ax.fill_between(t, act, fc, color=p.zone[z], alpha=0.18, linewidth=0, zorder=3)
        ax.plot(t, fc, color=p.zone[z], lw=1.4, zorder=4)
        ax.plot(t, act, color=p.ink, lw=0.9, zorder=5)
        worst = int(np.nanargmax(np.abs(act - fc)))
        ax.scatter([t[worst]], [act[worst]], s=36, color=p.accent, zorder=6,
                   linewidths=1.4, edgecolors=p.paper)
        ax.annotate(f"€{abs(act[worst] - fc[worst]):,.0f} miss",
                    xy=(t[worst], act[worst]), xytext=(7, -1),
                    textcoords="offset points", fontsize=7.6, color=p.accent, va="top")
        top = float(np.nanmax([act.max(), fc.max()])) * 1.14
        ax.set_xlim(0, 21)
        ax.set_xticks(range(0, 22, 3))
        ax.set_ylim(-90, top)
        panel_title(ax, f"{ZONE_NAME[z]}  ·  {start} to {end}", None, p)
    axes[1].set_ylabel("price  (€/MWh)")
    axes[-1].set_xlabel("day within the stress window")
    leg = axes[0].legend(handles=[Line2D([], [], color=p.ink, lw=1.5, label="actual"),
                                  Line2D([], [], color=p.zone["EE"], lw=1.8,
                                         label="short-window ensemble")],
                         loc="upper right", ncol=2, bbox_to_anchor=(1.0, 1.36))
    for t_ in leg.get_texts():
        t_.set_color(p.ink)
    fig.subplots_adjust(hspace=0.58)


# ------------------------------------------- listing-card thumbnail (180 px)
def thumbnail(fig, p: Palette):
    """Legible at card size: three bars, three numbers, no axis furniture."""
    m = pick(metrics(), period="overall", model="LEAR_ensemble")
    ax = fig.add_subplot(111)
    for i, z in enumerate(ZONES):
        y = len(ZONES) - 1 - i
        cut = (1 - one(m, "rMAE", country=z)) * 100
        ax.barh([y], [cut], height=0.52, color=p.zone[z], zorder=3)
        ax.annotate(z, xy=(0, y), xytext=(-8, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=15, color=p.zone[z],
                    fontfamily="serif")
        ax.annotate(f"−{cut:.0f}%", xy=(cut, y), xytext=(9, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=15, color=p.ink)
    ax.set_xlim(0, 44)
    ax.set_ylim(-0.6, len(ZONES) - 0.4)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines:
        ax.spines[side].set_visible(False)
    ax.annotate("forecast error vs. weekly naive", xy=(0, -0.55), fontsize=9.5,
                color=p.muted, ha="left", va="center")


FIGURES = {
    "fig-prices": (prices, (7.6, 6.4)),
    "fig-design": (design, (8.6, 3.9)),
    "fig-rmae": (rmae, (7.4, 4.3)),
    "fig-naive-gap": (naive_gap, (7.2, 3.6)),
    "fig-rolling": (rolling, (7.6, 4.0)),
    "fig-hourly": (hourly, (7.4, 4.2)),
    "fig-errdist": (errdist, (7.4, 4.2)),
    "fig-calibration": (calibration, (7.8, 3.4)),
    "fig-sync": (sync, (7.8, 3.7)),
    "fig-stress": (stress, (8.4, 4.6)),
    "fig-stress-trace": (stress_trace, (7.6, 6.4)),
    "fig-thumb": (thumbnail, (5.2, 2.4)),
}


def build_all():
    for name, (fn, size) in FIGURES.items():
        render(fn, name, figsize=size)
        print("  rendered", name)
