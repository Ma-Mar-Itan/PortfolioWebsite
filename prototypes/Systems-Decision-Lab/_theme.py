"""Figure theme for the Systems Decision Lab page.

Mirrors assets/theme-light.scss and assets/theme-dark.scss so the figures sit in
the page rather than on it. Every figure is rendered twice -- once per theme --
and shown through Quarto's .light-content / .dark-content classes.

Colour discipline used across all figures on this page:
    ACCENT (oxblood) = the thing under study  (running work, event-driven clock)
    ALT    (teal)    = the comparison         (waiting work, fixed time step)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

DIR = Path(__file__).resolve().parent
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
    a: str      # teal
    b: str      # oxblood
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
        "axes.titlesize": 10.5,
        "axes.titlecolor": p.ink,
        "axes.titlelocation": "left",
        "axes.titlepad": 10,
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


def panel_title(ax, text: str, p: Palette = LIGHT, dy: int = 12):
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, dy), textcoords="offset points",
                fontsize=10.5, fontfamily="serif", color=p.ink,
                va="bottom", ha="left", annotation_clip=False)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=p.grid, linewidth=0.7)
    ax.tick_params(length=0, axis=axis)


def render(build, name: str, figsize=(7.4, 4.4)) -> str:
    """Call build(fig, palette) once per theme; write figures/<name>-<theme>.svg."""
    for p in THEMES:
        with mpl.rc_context(rc(p)):
            fig = plt.figure(figsize=figsize)
            build(fig, p)
            fig.savefig(FIGDIR / f"{name}-{p.name}.svg")
            plt.close(fig)
    return name
