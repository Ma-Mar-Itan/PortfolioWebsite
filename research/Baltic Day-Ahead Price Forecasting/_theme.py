"""Figure theme and domain constants for the Baltic forecasting paper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from portfolio_figures import base_rc, md_table, show_theme_pair
from portfolio_figures import hairline_grid as shared_hairline_grid
from portfolio_figures import panel_title as shared_panel_title
from portfolio_figures import render_themes


def _manuscript_dir() -> Path:
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "_data" / "all_metrics.csv").exists():
            return candidate
    raise FileNotFoundError("could not locate the manuscript _data directory")


DIR = _manuscript_dir()
DATA = DIR / "_data"
FIGDIR = DIR / "figures"

ZONES = ["EE", "LV", "LT"]
ZONE_NAME = {"EE": "Estonia", "LV": "Latvia", "LT": "Lithuania"}
MODELS = ["LEAR_8w", "LEAR_12w", "LEAR_ensemble"]
MODEL_NAME = {"LEAR_8w": "LEAR 8w", "LEAR_12w": "LEAR 12w", "LEAR_ensemble": "Ensemble"}
SYNC_DATE = "2025-02-09"


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
    ramp: dict
    zone: dict
    accent: str
    sequential: list


LIGHT = Palette(
    name="light", ink="#14181d", muted="#5c6672", faint="#8b939c",
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
    name="dark", ink="#e8e6e1", muted="#9aa1a9", faint="#6f777f",
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
    return base_rc(p)


def panel_title(ax, text: str, sub: str | None = None, p: Palette = LIGHT):
    shared_panel_title(ax, text, p, sub=sub)


def hairline_grid(ax, axis: str = "y", p: Palette = LIGHT):
    shared_hairline_grid(ax, p, axis=axis,
                         hide_spine="left" if axis == "y" else "bottom")


def zone_legend(ax, p: Palette, loc="upper left", ncol=3, zones=None, **kwargs):
    from matplotlib.lines import Line2D

    zones = zones or ZONES
    handles = [Line2D([], [], color=p.zone[zone], lw=2.4, label=ZONE_NAME[zone]) for zone in zones]
    legend = ax.legend(handles=handles, loc=loc, ncol=ncol, **kwargs)
    for label in legend.get_texts():
        label.set_color(p.ink)
    return legend


def render(build, name: str, figsize=(7.4, 4.4), formats=("svg",)) -> str:
    return render_themes(build, name, figure_dir=FIGDIR, themes=THEMES,
                         rc_factory=rc, figsize=figsize, formats=formats)


def show(name: str, alt: str = "") -> str:
    return show_theme_pair(name, alt)
