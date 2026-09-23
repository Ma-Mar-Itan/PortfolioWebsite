"""Reusable Matplotlib conventions shared across portfolio projects."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt


SANS = ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]
SERIF = ["Newsreader", "Georgia", "Times New Roman", "DejaVu Serif"]


def base_rc(palette: Any, *, title_size: float = 12, title_pad: float = 12) -> dict[str, Any]:
    """Return the common site-matched Matplotlib configuration."""
    return {
        "font.family": "sans-serif",
        "font.sans-serif": SANS,
        "font.serif": SERIF,
        "font.size": 9.5,
        "figure.facecolor": palette.paper,
        "figure.edgecolor": palette.paper,
        "savefig.facecolor": palette.paper,
        "savefig.edgecolor": palette.paper,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.28,
        "axes.facecolor": palette.paper,
        "axes.edgecolor": palette.rule,
        "axes.labelcolor": palette.muted,
        "axes.labelsize": 9.5,
        "axes.labelpad": 7,
        "axes.titlesize": title_size,
        "axes.titlecolor": palette.ink,
        "axes.titlelocation": "left",
        "axes.titlepad": title_pad,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.grid": False,
        "grid.color": palette.grid,
        "grid.linewidth": 0.7,
        "xtick.color": palette.muted,
        "ytick.color": palette.muted,
        "xtick.labelcolor": palette.muted,
        "ytick.labelcolor": palette.muted,
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
        "legend.labelcolor": palette.ink,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.6,
        "legend.columnspacing": 1.4,
        "lines.linewidth": 1.8,
        "lines.solid_capstyle": "round",
        "patch.linewidth": 0,
        "svg.fonttype": "none",
    }


def panel_title(ax: Any, text: str, palette: Any, *, sub: str | None = None, dy: int = 12) -> None:
    """Place a site-styled panel label above an axes."""
    ax.annotate(
        text,
        xy=(0, 1),
        xycoords="axes fraction",
        xytext=(0, 27 if sub else dy),
        textcoords="offset points",
        fontsize=10.5,
        fontfamily="serif",
        color=palette.ink,
        va="bottom",
        ha="left",
        annotation_clip=False,
    )
    if sub:
        ax.annotate(
            sub,
            xy=(0, 1),
            xycoords="axes fraction",
            xytext=(0, 13),
            textcoords="offset points",
            fontsize=7.8,
            color=palette.muted,
            va="bottom",
            ha="left",
            annotation_clip=False,
        )


def hairline_grid(ax: Any, palette: Any, *, axis: str = "y", hide_spine: str | None = None) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color=palette.grid, linewidth=0.7)
    ax.tick_params(length=0, axis=axis)
    if hide_spine:
        ax.spines[hide_spine].set_visible(False)


def render_themes(
    build: Callable[[Any, Any], None],
    name: str,
    *,
    figure_dir: Path,
    themes: Iterable[Any],
    rc_factory: Callable[[Any], dict[str, Any]],
    figsize: tuple[float, float] = (7.4, 4.4),
    formats: Sequence[str] = ("svg",),
) -> str:
    figure_dir.mkdir(exist_ok=True)
    for palette in themes:
        with mpl.rc_context(rc_factory(palette)):
            figure = plt.figure(figsize=figsize)
            try:
                build(figure, palette)
                for extension in formats:
                    figure.savefig(figure_dir / f"{name}-{palette.name}.{extension}")
            finally:
                plt.close(figure)
    return name


def show_theme_pair(name: str, alt: str = "") -> str:
    rel = f"figures/{name}"
    safe_alt = alt.replace('"', "&quot;")
    return (
        f'::: {{.light-content}}\n![]({rel}-light.svg){{fig-alt="{safe_alt}"}}\n:::\n'
        f'::: {{.dark-content}}\n![]({rel}-dark.svg){{fig-alt="{safe_alt}"}}\n:::'
    )


def fmt_p(value: float) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value != value:
        return "—"
    if value < 0.001:
        mantissa, exponent = f"{value:.1e}".split("e")
        superscript = str(int(exponent)).replace("-", "⁻")
        for ordinary, raised in zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"):
            superscript = superscript.replace(ordinary, raised)
        return f"{mantissa} × 10{superscript}"
    return f"{value:.3f}"


def md_table(frame: Any, align: list[str] | None = None, index: bool = False) -> str:
    import pandas as pd

    data = frame.reset_index() if index else frame
    columns = [str(column) for column in data.columns]
    align = align or ["l"] + ["r"] * (len(columns) - 1)
    bars = {"l": ":---", "r": "---:", "c": ":--:"}
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(bars[item] for item in align) + " |",
    ]
    for _, row in data.iterrows():
        rows.append("| " + " | ".join("" if pd.isna(value) else str(value) for value in row) + " |")
    return "\n".join(rows)
