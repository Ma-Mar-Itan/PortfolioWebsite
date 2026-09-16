"""Figure theme for the Baltic day-ahead price forecasting paper.

Mirrors assets/theme-light.scss and assets/theme-dark.scss so figures sit in the
page rather than on it. Every figure is rendered twice -- once per theme -- and
shown through Quarto's .light-content / .dark-content classes.

Colour discipline, used consistently across every figure in the paper:

    Estonia   = blue      Latvia = orange      Lithuania = aqua

The hue is the bidding zone and nothing else. Where the three LEAR
specifications appear inside a zone they are three steps of that zone's own hue,
weakest to strongest (8w, 12w, ensemble), always with direct value labels so the
model is never carried by shade alone. The weekly naive benchmark is never given
a hue: it is the grey reference the coloured marks are measured against.

The three zone hues are the first three slots of the reference categorical
palette and clear every all-pairs colour-vision gate in both modes
(CVD dE 9.2 light / 9.4 dark; normal-vision dE 24.0 light / 20.9 dark).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt


# --------------------------------------------------------------------- paths
def _manuscript_dir() -> Path:
    here = Path.cwd()
    for cand in (here, *here.parents):
        if (cand / "_data" / "all_metrics.csv").exists():
            return cand
    raise FileNotFoundError("could not locate the manuscript _data directory")


DIR = _manuscript_dir()
DATA = DIR / "_data"
FIGDIR = DIR / "figures"
FIGDIR.mkdir(exist_ok=True)

SANS = ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]
SERIF = ["Newsreader", "Georgia", "Times New Roman", "DejaVu Serif"]

ZONES = ["EE", "LV", "LT"]
ZONE_NAME = {"EE": "Estonia", "LV": "Latvia", "LT": "Lithuania"}
MODELS = ["LEAR_8w", "LEAR_12w", "LEAR_ensemble"]
MODEL_NAME = {"LEAR_8w": "LEAR 8w", "LEAR_12w": "LEAR 12w",
              "LEAR_ensemble": "Ensemble"}
SYNC_DATE = "2025-02-09"   # Baltic synchronisation with Continental Europe


@dataclass(frozen=True)
class Palette:
    name: str
    ink: str
    muted: str
    faint: str
    paper: str
    paper2: str
    rule: str
    grid: str
    # zone -> three steps of that zone's hue, weakest to strongest
    ramp: dict
    # zone -> the single canonical hue
    zone: dict
    accent: str      # one warm accent for "stress" callouts
    sequential: list  # single-hue density ramp, light -> dark on the surface


LIGHT = Palette(
    name="light",
    ink="#14181d", muted="#5c6672", faint="#8b939c",
    paper="#fdfdfc", paper2="#f4f3f0", rule="#e3e1dc", grid="#ece9e4",
    ramp={"EE": ["#64aaff", "#458ae1", "#125caf"],
          "LV": ["#fa8052", "#d76032", "#a33000"],
          "LT": ["#4bc18f", "#20a171", "#007346"]},
    zone={"EE": "#2a78d6", "LV": "#eb6834", "LT": "#1baf7a"},
    accent="#d03b3b",
    sequential=["#eef4fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                "#256abf", "#184f95", "#0d366b"],
)

DARK = Palette(
    name="dark",
    ink="#e8e6e1", muted="#9aa1a9", faint="#6f777f",
    paper="#14161a", paper2="#1c1f24", rule="#2c3037", grid="#232830",
    ramp={"EE": ["#2068bc", "#478de4", "#76bdff"],
          "LV": ["#b03e08", "#da6438", "#ff9468"],
          "LT": ["#007d55", "#36a277", "#6bd2a5"]},
    zone={"EE": "#3987e5", "LV": "#d95926", "LT": "#199e70"},
    accent="#e66767",
    sequential=["#151b26", "#16304f", "#184f95", "#256abf", "#3987e5",
                "#6da7ec", "#9ec5f4", "#cde2fb"],
)

THEMES = (LIGHT, DARK)


def rc(p: Palette) -> dict:
    return {
        "font.family": "sans-serif",
        "font.sans-serif": SANS,
        "font.serif": SERIF,
        "font.size": 9.5,
        "figure.facecolor": p.paper,
        "figure.edgecolor": p.paper,
        "savefig.facecolor": p.paper,
        "savefig.edgecolor": p.paper,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.28,
        "axes.facecolor": p.paper,
        "axes.edgecolor": p.rule,
        "axes.labelcolor": p.muted,
        "axes.labelsize": 9.5,
        "axes.labelpad": 7,
        "axes.titlesize": 12,
        "axes.titlecolor": p.ink,
        "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.grid": False,
        "grid.color": p.grid,
        "grid.linewidth": 0.7,
        "xtick.color": p.muted,
        "ytick.color": p.muted,
        "xtick.labelcolor": p.muted,
        "ytick.labelcolor": p.muted,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "legend.fontsize": 8.8,
        "legend.labelcolor": p.ink,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.6,
        "legend.columnspacing": 1.4,
        "lines.linewidth": 1.8,
        "lines.solid_capstyle": "round",
        "patch.linewidth": 0,
        "svg.fonttype": "none",
    }


def panel_title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    """A 'which panel is this' label above the axes, in the paper's serif."""
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, 27 if sub else 12), textcoords="offset points",
                fontsize=10.5, fontfamily="serif", color=p.ink,
                va="bottom", ha="left", annotation_clip=False)
    if sub:
        ax.annotate(sub, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 13), textcoords="offset points",
                    fontsize=7.8, color=p.muted, va="bottom", ha="left",
                    annotation_clip=False)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=p.grid, linewidth=0.7)
    ax.tick_params(length=0, axis=axis)
    if axis == "y":
        ax.spines["left"].set_visible(False)
    else:
        ax.spines["bottom"].set_visible(False)


def zone_legend(ax, p: Palette, loc="upper left", ncol=3, zones=None, **kw):
    """The zone key. Present whenever more than one zone shares an axis."""
    from matplotlib.lines import Line2D
    zones = zones or ZONES
    handles = [Line2D([], [], color=p.zone[z], lw=2.4, label=ZONE_NAME[z])
               for z in zones]
    leg = ax.legend(handles=handles, loc=loc, ncol=ncol, **kw)
    for t in leg.get_texts():
        t.set_color(p.ink)
    return leg


def render(build, name: str, figsize=(7.4, 4.4), formats=("svg",)) -> str:
    """Call `build(fig, palette)` once per theme; write figures/<name>-<theme>.svg."""
    for p in THEMES:
        with mpl.rc_context(rc(p)):
            fig = plt.figure(figsize=figsize)
            build(fig, p)
            for ext in formats:
                fig.savefig(FIGDIR / f"{name}-{p.name}.{ext}")
            plt.close(fig)
    return name


def show(name: str, alt: str = "") -> str:
    """Markdown pair that swaps with the site theme.

    NB: the link text must stay empty. A lone ![alt](src) in a paragraph is
    promoted by Pandoc to an implicit figure, which would print the alt text as
    a second caption above Quarto's own.
    """
    rel = f"figures/{name}"
    return (f'::: {{.light-content}}\n![]({rel}-light.svg){{fig-alt="{alt}"}}\n:::\n'
            f'::: {{.dark-content}}\n![]({rel}-dark.svg){{fig-alt="{alt}"}}\n:::')


# ------------------------------------------------------------ table helpers
def md_table(df, align=None, index=False) -> str:
    """GitHub-flavoured markdown table with no third-party dependency."""
    import pandas as pd
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    align = align or ["l"] + ["r"] * (len(cols) - 1)
    bar = {"l": ":---", "r": "---:", "c": ":--:"}
    rows = ["| " + " | ".join(cols) + " |",
            "| " + " | ".join(bar[a] for a in align) + " |"]
    for _, r in d.iterrows():
        rows.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(rows)
