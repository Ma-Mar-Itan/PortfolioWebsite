"""Figure theme for the Systems Decision Lab page."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from portfolio_figures import base_rc
from portfolio_figures import hairline_grid as shared_hairline_grid
from portfolio_figures import panel_title as shared_panel_title
from portfolio_figures import render_themes

DIR = Path(__file__).resolve().parent
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


def rc(p: Palette) -> dict:
    return base_rc(p, title_size=10.5, title_pad=10)


def panel_title(ax, text: str, p: Palette = LIGHT, dy: int = 12):
    shared_panel_title(ax, text, p, dy=dy)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    shared_hairline_grid(ax, p, axis=axis)


def render(build, name: str, figsize=(7.4, 4.4)) -> str:
    return render_themes(build, name, figure_dir=FIGDIR, themes=THEMES,
                         rc_factory=rc, figsize=figsize)
