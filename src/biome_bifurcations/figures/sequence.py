# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""From desert to forest, vegetation changes in jumps, at different rainfalls going up and down.

Tree cover where the full model settles while rainfall rises slowly from desert to forest, and
then falls back. The two sweeps agree except at the desert edge and between savanna and forest,
where each jumps at one rainfall going up and at another coming down; arrows mark the jumps.

Two more figures reuse the same sweeps: one shades the two stretches where the land remembers,
and one sets the model against the field sites, marking the stretch where fire keeps every tree
out although real land has trees.
"""

from functools import cache
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import (
    COVER_LABEL,
    PRM,
    SWEEP_CODE,
    lines,
    rain_axis,
    scale,
    sites,
    stored,
    swept,
)
from biome_bifurcations.model import cover
from biome_bifurcations.settle import up_and_down

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAINS = np.arange(50.0, 2501.0, 2.0)  # mm/yr, visited in 2 mm steps
FOREST = np.array([0.0, 0.0, 0.05, 0.3])  # little grass, many trees: where the fall starts
JUMP = 10.0  # least change of tree cover (percent) between neighboring rainfalls that is a jump
SHOWN = 2000.0  # mm/yr: the axis ends here; above 1,540 only forest remains, and it changes little
LABELS = (  # (rain mm/yr, tree cover %, text, alignment, vertical alignment): beside the stretch
    # they name, and clear of every line at slide size too, where text is larger against the plot
    (0.0, 36.0, "desert", "left", "bottom"),  # above the bare stretch, clear of the jump arrows
    (290.0, 53.0, "open woodland", "center", "bottom"),  # over the hump, above "desert"
    (490.0, 20.0, "grassland", "center", "bottom"),  # over the bare stretch, between two slopes
    (1180.0, 20.0, "savanna", "center", "bottom"),  # under the rising savanna
    (SHOWN - 20.0, 80.0, "forest", "right", "top"),  # under the forest
)


@cache
def sweeps() -> Array:
    """Tree cover (percent) along rising and falling rainfall."""

    def compute() -> Array:
        up, down = up_and_down(RAINS / scale(), np.zeros(4), FOREST, PRM)
        return 100 * np.array([cover(up[:, 3], PRM), cover(down[:, 3], PRM)])

    return stored("sequence", (RAINS, FOREST, PRM, scale()), compute, SWEEP_CODE)


WINDOWS = ("bare or green", "savanna or forest")  # the two states possible in each window
TREELESS_COVER = 0.5  # percent: less tree cover than this counts as none
WOODLAND_END = 1000.0  # mm/yr: the open woodland and the grassland after it both lie below this


def _both_ways(
    ax: Axes, medium: style.Medium, *, arrows: bool = True
) -> tuple[list[float], list[float]]:
    """Draw both sweeps; return where the rising one jumps and where the falling one does."""
    up, down = sweeps()
    draw_sweep = swept if arrows else lines
    rising = draw_sweep(ax, (RAINS, up), medium, style.TREES.mark, JUMP)
    falling = draw_sweep(ax, (RAINS[::-1], down[::-1]), medium, style.TREES.mark, JUMP)
    return sorted(x for x, _, _ in rising), sorted(x for x, _, _ in falling)


def _cover_axes(ax: Axes, top: float = 104.0) -> None:
    """The rainfall and tree-cover axes all three figures share."""
    rain_axis(ax, SHOWN)
    ax.set_ylim(-2, top)
    ax.set_yticks([0, 50, 100])
    ax.spines["left"].set_bounds(0, 100)
    ax.set_ylabel(COVER_LABEL)


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.42))
    _both_ways(ax, medium)
    for rain_mm, tree, text, ha, va in LABELS:
        ax.text(
            rain_mm,
            tree,
            text,
            ha=ha,
            va=va,
            color=style.NEUTRAL.label,
            fontsize=medium.small,
        )
    _cover_axes(ax)
    return fig


def draw_windows(medium: style.Medium) -> Figure:
    """The land remembers: where two states are possible, shaded, and named above.

    Each window runs from where the falling sweep jumps to where the rising one does: the desert
    edge, bare or green, and the savanna-forest jump, which fire decides.
    """
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.42))
    rising, falling = _both_ways(ax, medium)
    washes = (style.SOIL.wash, style.FIRE.wash)
    for low, high, wash, name in zip(falling, rising, washes, WINDOWS, strict=True):
        ax.fill_between([low, high], -2.0, 100.0, color=wash, lw=0, zorder=0)
        ax.text(
            (low + high) / 2,
            104,
            name,
            ha="center",
            va="bottom",
            color=style.NEUTRAL.label,
            fontsize=medium.small,
        )
    _cover_axes(ax, top=118.0)
    return fig


def draw_versus(medium: style.Medium) -> Figure:
    """The model against the field sites, with the stretch where fire keeps every tree out."""
    up, _ = sweeps()
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.42))
    data = sites()
    ax.scatter(data.rain, 100 * data.woody, s=1.5 * medium.line**2, color=style.NEUTRAL.data, lw=0)
    # Past the open woodland, the first stretch with no trees at all is the fire-cleared grassland.
    # A run that has not settled is NaN, and nanargmax skips it.
    peak = RAINS[int(np.nanargmax(np.where(RAINS < WOODLAND_END, up, 0.0)))]
    bare = (peak < RAINS) & (RAINS < WOODLAND_END) & (up < TREELESS_COVER)
    if bare.any():
        low, high = float(RAINS[bare].min()), float(RAINS[bare].max())
        ax.fill_between([low, high], -2.0, 100.0, color=style.GRASS.wash, lw=0, zorder=0)
        ax.text(
            (low + high) / 2,
            104,
            "no trees in the model",
            ha="center",
            va="bottom",
            color=style.NEUTRAL.label,
            fontsize=medium.small,
        )
    _both_ways(ax, medium, arrows=False)  # among the sites, arrows would read as data
    ax.text(
        SHOWN - 20.0,
        float(up[-1]) - 4.0,
        "model",
        ha="right",
        va="top",
        color=style.TREES.ink,
        fontsize=medium.small,
    )
    _cover_axes(ax, top=118.0)
    return fig
