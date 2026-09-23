"""Figure theme for the acquisition-aware falsification manuscript."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from portfolio_figures import base_rc, fmt_p, md_table, show_theme_pair
from portfolio_figures import hairline_grid as shared_hairline_grid
from portfolio_figures import panel_title as shared_panel_title
from portfolio_figures import render_themes


def _manuscript_dir() -> Path:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "_data" / "patients.csv").exists():
            return candidate
    raise FileNotFoundError("could not locate the manuscript _data directory")


DIR = _manuscript_dir()
DATA = DIR / "_data"
FIGDIR = DIR / "figures"


@dataclass(frozen=True)
class Palette:
    name: str
    ink: str
    muted: str
    paper: str
    paper2: str
    rule: str
    a: str
    b: str
    grid: str


LIGHT = Palette("light", "#14181d", "#5c6672", "#fdfdfc", "#f4f3f0", "#e3e1dc",
                "#1f5f5b", "#8a2f2f", "#ece9e4")
DARK = Palette("dark", "#e8e6e1", "#9aa1a9", "#14161a", "#1c1f24", "#2c3037",
               "#6fbfae", "#e0806f", "#232830")
THEMES = (LIGHT, DARK)
EDITORIAL_TITLES = False


def rc(p: Palette) -> dict:
    return base_rc(p)


def title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    if not EDITORIAL_TITLES:
        return
    ax.set_title("")
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, 30 if sub else 14), textcoords="offset points",
                fontsize=12, fontfamily="serif", color=p.ink,
                va="bottom", ha="left", annotation_clip=False)
    if sub:
        ax.annotate(sub, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 14), textcoords="offset points",
                    fontsize=8.6, color=p.muted, va="bottom", ha="left",
                    annotation_clip=False)


def panel_title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    shared_panel_title(ax, text, p, sub=sub if EDITORIAL_TITLES else None)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    shared_hairline_grid(ax, p, axis=axis, hide_spine="left" if axis == "y" else None)


def render(build, name: str, figsize=(7.4, 4.4), formats=("svg",)) -> str:
    return render_themes(build, name, figure_dir=FIGDIR, themes=THEMES,
                         rc_factory=rc, figsize=figsize, formats=formats)


def show(name: str, alt: str = "") -> str:
    return show_theme_pair(name, alt)


def figure(name: str, alt: str = "") -> str:
    return show_theme_pair(name, alt)
