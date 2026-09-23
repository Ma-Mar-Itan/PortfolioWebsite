"""Figure theme for the manuscript.

Mirrors assets/theme-light.scss and assets/theme-dark.scss so figures sit in
the page rather than on it. Every figure is rendered twice -- once per theme --
and shown through Quarto's .light-content / .dark-content classes.

Colour discipline, used consistently across all figures:
    GROUP_A (teal)    = Cluster 0  and  GE
    GROUP_B (oxblood) = Cluster 1  and  Siemens
Clusters and manufacturers deliberately share a palette: that is the argument.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# --------------------------------------------------------------------- paths
def _manuscript_dir() -> Path:
    here = Path.cwd()
    for cand in (here, *here.parents):
        if (cand / "_data" / "patients.csv").exists():
            return cand
    raise FileNotFoundError("could not locate the manuscript _data directory")

DIR = _manuscript_dir()
DATA = DIR / "_data"
FIGDIR = DIR / "figures"
FIGDIR.mkdir(exist_ok=True)

SANS = ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]
SERIF = ["Newsreader", "Georgia", "Times New Roman", "DejaVu Serif"]


@dataclass(frozen=True)
class Palette:
    name: str
    ink: str
    muted: str
    paper: str
    paper2: str
    rule: str
    a: str      # group A  — teal
    b: str      # group B  — oxblood
    grid: str

LIGHT = Palette("light", "#14181d", "#5c6672", "#fdfdfc", "#f4f3f0", "#e3e1dc",
                "#1f5f5b", "#8a2f2f", "#ece9e4")
DARK = Palette("dark", "#e8e6e1", "#9aa1a9", "#14161a", "#1c1f24", "#2c3037",
               "#6fbfae", "#e0806f", "#232830")
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


# Editorial headlines inside figures are OFF. Every word a reader sees on this
# page comes from the author's manuscript; the captions do the talking.
EDITORIAL_TITLES = False


def title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    if not EDITORIAL_TITLES:
        return
    """Serif title with an optional muted sans deck, stacked above the axes."""
    ax.set_title("")
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, 30 if sub else 14), textcoords="offset points",
                fontsize=12, fontfamily="serif", color=p.ink, va="bottom", ha="left",
                annotation_clip=False)
    if sub:
        ax.annotate(sub, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 14), textcoords="offset points",
                    fontsize=8.6, color=p.muted, va="bottom", ha="left",
                    annotation_clip=False)


def panel_title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    """Smaller variant for one panel. The deck is editorial and is suppressed;
    the head is a plain "which panel is this" label and always shows."""
    if not EDITORIAL_TITLES:
        sub = None
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, 27 if sub else 12), textcoords="offset points",
                fontsize=10.5, fontfamily="serif", color=p.ink, va="bottom", ha="left",
                annotation_clip=False)
    if sub:
        ax.annotate(sub, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 13), textcoords="offset points",
                    fontsize=7.8, color=p.muted, va="bottom", ha="left",
                    annotation_clip=False)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=p.grid, linewidth=0.7)
    ax.tick_params(length=0, axis=axis)
    for side in ("left", "right", "top"):
        if side in ("left",) and axis == "y":
            ax.spines[side].set_visible(False)


def render(build, name: str, figsize=(7.4, 4.4), formats=("svg",)) -> str:
    """Call `build(fig, palette)` once per theme; write figures/<name>-<theme>.svg.

    Returns the markdown that shows the right one for the reader's theme.
    """
    for p in THEMES:
        with mpl.rc_context(rc(p)):
            fig = plt.figure(figsize=figsize)
            build(fig, p)
            for ext in formats:
                fig.savefig(FIGDIR / f"{name}-{p.name}.{ext}")
            plt.close(fig)
    return name


def show(name: str, alt: str = "") -> str:
    """Markdown pair that swaps with the site theme."""
    rel = f"figures/{name}"
    # NB: the link text must stay empty. A lone ![alt](src) in a paragraph is
    # promoted by Pandoc to an implicit figure, which would print the alt text
    # as a second caption above Quarto's own.
    return (f'::: {{.light-content}}\n![]({rel}-light.svg){{fig-alt="{alt}"}}\n:::\n'
            f'::: {{.dark-content}}\n![]({rel}-dark.svg){{fig-alt="{alt}"}}\n:::')


# ------------------------------------------------------------ table helpers
def fmt_p(v: float) -> str:
    """p-values the way a reader reads them, not the way floats print."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if v != v:
        return "—"
    if v < 0.001:
        m, e = f"{v:.1e}".split("e")
        sup = str(int(e)).replace("-", "⁻")
        for a, b in zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"):
            sup = sup.replace(a, b)
        return f"{m} × 10{sup}"
    return f"{v:.3f}"


def md_table(df, align=None, index=False) -> str:
    """GitHub-flavoured markdown table with no third-party dependency."""
    import pandas as pd  # local import keeps _theme importable without a hard pandas dep
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    align = align or ["l"] + ["r"] * (len(cols) - 1)
    bar = {"l": ":---", "r": "---:", "c": ":--:"}
    rows = ["| " + " | ".join(cols) + " |",
            "| " + " | ".join(bar[a] for a in align) + " |"]
    for _, r in d.iterrows():
        rows.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(rows)


def figure(name: str, alt: str = "") -> str:
    """Theme-aware figure pair, for use inside a Quarto figure div."""
    return show(name, alt)
