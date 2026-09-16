"""Builds every figure on this page, once per site theme.

    python3 _figures.py

Figures 2, 4 and 5 are drawn from actual runs of the engine in _engine.py, not
sketched by hand: the event times, start times, queue depths and summary metrics
are whatever the simulation produced.
"""
from __future__ import annotations

import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from _theme import LIGHT, Palette, hairline_grid, panel_title, render
from _engine import CLUSTER, WORKLOAD, Cluster, Task, simulate


# ----------------------------------------------------------------- helpers
def box(ax, x, y, w, h, title, lines, p: Palette, face=None, edge=None, lw=1.1):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=face if face else p.paper2,
        edgecolor=edge if edge else p.rule, linewidth=lw, zorder=2))
    ax.text(x + w / 2, y + h - 0.052, title, ha="center", va="top",
            fontsize=10, fontfamily="serif", color=p.ink, zorder=3)
    for i, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.115 - i * 0.052, line, ha="center", va="top",
                fontsize=8.3, color=p.muted, zorder=3)


def arrow(ax, xy_from, xy_to, p: Palette, label=None, rad=0.0, color=None,
          label_offset=(0, 0.022), fontsize=8.1, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        xy_from, xy_to, arrowstyle=style, mutation_scale=11,
        connectionstyle=f"arc3,rad={rad}", linewidth=1.2,
        color=color or p.muted, zorder=1, shrinkA=3, shrinkB=3))
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + label_offset[0]
        my = (xy_from[1] + xy_to[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=fontsize,
                color=p.muted, zorder=3,
                bbox=dict(facecolor=p.paper, edgecolor="none", pad=1.6))


# --------------------------------------------- fig 1 · the abstraction
def fig_abstraction(fig, p: Palette):
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    real = ["2.4 TB of detector strain data",
            "read from a distributed store",
            "40 minutes on 32 CPU cores",
            "96 GB of memory, no accelerator",
            "queued behind the calibration stage",
            "at 08:32 on a Tuesday",
            "one of 120,000 like it"]
    meta = [("arrival_time_sec", "512"),
            ("estimated_runtime_sec", "2400"),
            ("cpu_required", "32"),
            ("gpu_required", "0"),
            ("memory_required_gb", "96"),
            ("priority", "2"),
            ("parent_task_ids", "T00417"),
            ("logical_input_size_gb", "2400")]

    box(ax, 0.02, 0.10, 0.40, 0.80, "One task, as it really is", [], p,
        face=p.paper, edge=p.rule)
    for i, line in enumerate(real):
        ax.text(0.055, 0.685 - i * 0.083, "\u2014", ha="left", va="center",
                fontsize=9, color=p.rule)
        ax.text(0.095, 0.685 - i * 0.083, line, ha="left", va="center",
                fontsize=9, color=p.muted)

    box(ax, 0.58, 0.10, 0.40, 0.80, "What the simulator keeps", [], p,
        face=p.paper2, edge=p.rule)
    for i, (name, value) in enumerate(meta):
        y = 0.695 - i * 0.077
        ax.text(0.615, y, name, ha="left", va="center",
                fontsize=8.3, family="monospace", color=p.muted)
        ax.text(0.945, y, value, ha="right", va="center",
                fontsize=8.3, family="monospace", color=p.ink)

    arrow(ax, (0.435, 0.50), (0.565, 0.50), p, color=p.b)
    ax.text(0.50, 0.585, "keep behaviour", ha="center", va="center",
            fontsize=8.5, color=p.b,
            bbox=dict(facecolor=p.paper, edgecolor="none", pad=1.5))
    ax.text(0.50, 0.415, "drop bytes", ha="center", va="center",
            fontsize=8.5, color=p.muted,
            bbox=dict(facecolor=p.paper, edgecolor="none", pad=1.5))


# --------------------------------------------- fig 2 · why the clock jumps
def fig_clock(fig, p: Palette):
    mini = [Task("A", 0, 300, 6, 0, 32, 3),
            Task("B", 30, 120, 4, 0, 24, 3),
            Task("C", 120, 90, 2, 0, 16, 3)]
    run = simulate(mini, Cluster(cpus=8, gpus=0, mem=128), "FCFS")
    moments = sorted({round(t, 3) for t, _, _ in run.events})
    span = 450

    # (time, label, row, horizontal anchor)
    labels = [(0, "A arrives, A starts", 0, "left"),
              (30, "B arrives, waits", 1, "left"),
              (120, "C arrives, C starts", 0, "left"),
              (210, "C completes", 1, "center"),
              (300, "A completes, B starts", 0, "center"),
              (420, "B completes", 1, "right")]

    top = fig.add_axes([0.06, 0.70, 0.90, 0.13])
    bot = fig.add_axes([0.06, 0.14, 0.90, 0.31])

    for ax in (top, bot):
        ax.set_xlim(-6, span + 6); ax.set_ylim(0, 1)
        ax.set_yticks([]); ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(p.rule)
        ax.set_xticks(range(0, span + 1, 50))

    for s in range(0, span + 1):
        top.plot([s, s], [0.12, 0.88], color=p.a, linewidth=0.5, alpha=0.5,
                 solid_capstyle="butt")
    panel_title(top, "Fixed time step", p, dy=14)
    top.annotate("450 evaluations \u00b7 444 of them find nothing changed",
                 xy=(1, 1), xycoords="axes fraction", xytext=(0, 14),
                 textcoords="offset points", ha="right", va="bottom",
                 fontsize=8.8, color=p.a, annotation_clip=False)
    top.tick_params(axis="x", labelbottom=False)

    for m in moments:
        bot.plot([m, m], [0.05, 0.40], color=p.b, linewidth=2.0,
                 solid_capstyle="butt")
        bot.plot([m], [0.40], marker="o", markersize=4.2, color=p.b)
    for t, text, row, ha in labels:
        bot.annotate(text, xy=(t, 0.50 + row * 0.23),
                     xycoords=("data", "axes fraction"),
                     ha=ha, va="bottom", fontsize=8.2, color=p.muted,
                     annotation_clip=False)
    panel_title(bot, "Event-driven clock", p, dy=14)
    bot.annotate(f"{len(moments)} evaluations \u00b7 the clock jumps between them",
                 xy=(1, 1), xycoords="axes fraction", xytext=(0, 14),
                 textcoords="offset points", ha="right", va="bottom",
                 fontsize=8.8, color=p.b, annotation_clip=False)
    bot.set_xlabel("simulated time (seconds)")


# --------------------------------------------- fig 3 · the loop
def fig_loop(fig, p: Palette):
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    box(ax, 0.06, 0.70, 0.32, 0.24, "Event queue",
        ["future arrivals and completions", "held in time order"], p)
    box(ax, 0.62, 0.70, 0.32, 0.24, "Virtual clock",
        ["jumps to the timestamp", "of the next event"], p)
    box(ax, 0.06, 0.30, 0.32, 0.24, "Event handlers",
        ["arrival: reject or queue", "completion: release capacity"], p)
    box(ax, 0.62, 0.30, 0.32, 0.24, "System state",
        ["queues, CPUs, GPUs, memory,", "task status, metric records"], p)
    box(ax, 0.34, 0.02, 0.32, 0.20, "Scheduler",
        ["FCFS \u00b7 SJF \u00b7 Priority \u00b7 Random", "picks who is considered next"],
        p, face=p.paper, edge=p.b, lw=1.4)

    arrow(ax, (0.38, 0.82), (0.62, 0.82), p, "pop next event", color=p.b)
    arrow(ax, (0.78, 0.70), (0.78, 0.54), p, "advance time",
          label_offset=(0.105, 0), color=p.b)
    arrow(ax, (0.38, 0.42), (0.62, 0.42), p, "read and update state",
          label_offset=(0, 0.055), style="<|-|>")
    arrow(ax, (0.16, 0.54), (0.16, 0.70), p, "schedule future events",
          label_offset=(0.135, 0))
    arrow(ax, (0.17, 0.30), (0.35, 0.145), p, "invoke policy",
          label_offset=(-0.085, -0.015), rad=-0.12)
    arrow(ax, (0.65, 0.145), (0.79, 0.30), p, "start what fits",
          label_offset=(0.09, -0.015), rad=-0.12, color=p.b)


# --------------------------------------------- gantt helper
def gantt(ax, run, p: Palette, xmax, show_labels=True, note=True):
    tasks = sorted(run.tasks, key=lambda t: t.task_id)
    for i, t in enumerate(tasks):
        y = len(tasks) - i - 1
        if t.status == "rejected":
            ax.plot([t.arrival], [y], marker="x", markersize=7,
                    markeredgewidth=1.8, color=p.muted)
            if note:
                ax.text(t.arrival + xmax * 0.012, y,
                        "rejected — demand exceeds the cluster",
                        va="center", ha="left", fontsize=7.8, color=p.muted)
            continue
        if t.start > t.arrival:
            ax.barh(y, t.start - t.arrival, left=t.arrival, height=0.52,
                    color=p.rule, zorder=2)
        colour = p.a if t.gpu else p.b
        ax.barh(y, t.finish - t.start, left=t.start, height=0.52,
                color=colour, zorder=3)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t.task_id for t in tasks][::-1] if show_labels
                       else [""] * len(tasks), fontsize=8)
    ax.set_ylim(-0.7, len(tasks) - 0.3)
    ax.set_xlim(0, xmax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    hairline_grid(ax, "x", p)


# --------------------------------------------- fig 4 · one run
def fig_run(fig, p: Palette):
    run = simulate(WORKLOAD, CLUSTER, "FCFS")
    xmax = run.makespan * 1.06

    g = fig.add_axes([0.075, 0.42, 0.90, 0.46])
    u = fig.add_axes([0.075, 0.10, 0.90, 0.22], sharex=g)

    gantt(g, run, p, xmax)
    panel_title(g, "Every task, from arrival to completion", p, dy=26)
    g.tick_params(axis="x", labelbottom=False)
    g.axvline(run.makespan, color=p.muted, linewidth=0.9, linestyle=(0, (4, 3)))
    g.text(run.makespan - xmax * 0.008, len(run.tasks) - 0.55,
           f"makespan {run.makespan:.0f} s", ha="right", va="top",
           fontsize=8.4, color=p.muted)

    handles = [mpatches.Patch(color=p.rule, label="waiting in the queue"),
               mpatches.Patch(color=p.b, label="running (CPU only)"),
               mpatches.Patch(color=p.a, label="running (holds a GPU)")]
    g.legend(handles=handles, loc="lower right", ncol=3,
             bbox_to_anchor=(1.0, 1.005))

    ts = [r[0] for r in run.utilization]
    cpu = [100 * r[1] / CLUSTER.cpus for r in run.utilization]
    gpu = [100 * r[2] / CLUSTER.gpus for r in run.utilization]
    u.step(ts, cpu, where="post", color=p.b, linewidth=1.6, label="CPU")
    u.step(ts, gpu, where="post", color=p.a, linewidth=1.4, label="GPU")
    u.fill_between(ts, cpu, step="post", color=p.b, alpha=0.10)
    u.set_ylim(0, 108); u.set_yticks([0, 50, 100])
    u.set_yticklabels(["0", "50", "100%"])
    u.set_xlabel("simulated time (seconds)")
    panel_title(u, "Capacity in use", p)
    u.legend(loc="lower right", ncol=2)
    hairline_grid(u, "y", p)


# --------------------------------------------- fig 5 · controlled comparison
def fig_compare(fig, p: Palette):
    runs = [simulate(WORKLOAD, CLUSTER, policy) for policy in ("FCFS", "SJF")]
    xmax = max(r.makespan for r in runs) * 1.06

    axes = [fig.add_axes([0.075, 0.56, 0.90, 0.34]),
            fig.add_axes([0.075, 0.10, 0.90, 0.34])]
    for i, (ax, run) in enumerate(zip(axes, runs)):
        gantt(ax, run, p, xmax, note=(i == 0))
        panel_title(ax, run.policy, p, dy=22)
        ax.annotate(f"makespan {run.makespan:.0f} s     "
                    f"mean wait {run.mean_wait:.0f} s",
                    xy=(1, 1), xycoords="axes fraction", xytext=(0, 10),
                    textcoords="offset points", ha="right", va="bottom",
                    fontsize=8.6, color=p.muted, annotation_clip=False)
        ax.axvline(run.makespan, color=p.muted, linewidth=0.9,
                   linestyle=(0, (4, 3)))
    axes[0].tick_params(axis="x", labelbottom=False)
    axes[1].set_xlabel("simulated time (seconds)")


def build_all():
    render(fig_abstraction, "fig-abstraction", figsize=(7.4, 3.5))
    render(fig_clock, "fig-clock", figsize=(7.4, 3.5))
    render(fig_loop, "fig-loop", figsize=(7.4, 4.3))
    render(fig_run, "fig-run", figsize=(7.4, 5.4))
    render(fig_compare, "fig-compare", figsize=(7.4, 5.2))


if __name__ == "__main__":
    build_all()
    print("built")
