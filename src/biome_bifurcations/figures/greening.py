# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Because plants help water soak in, grass appears suddenly and holds on in drier years.

Grass alone, run to a steady state at each rainfall while rainfall rises slowly from desert and
then falls back. Rising, grass appears only where a few seeds can grow, and then at once in
force; falling, it holds on far below that rainfall, then collapses. Arrows mark the two jumps.
In grey, the same experiment if plants did not open the soil, so that water soaked in
everywhere as on bare soil: grass appears gradually and stays sparse, the same both ways.
"""

from dataclasses import replace
from functools import cache
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import (
    GRASS_LABEL,
    PRM,
    SWEEP_CODE,
    rain_axis,
    scale,
    stored,
    swept,
)
from biome_bifurcations.settle import up_and_down

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAINS = np.arange(10.0, 451.0, 1.0)  # mm/yr, visited in 1 mm steps
DENSE = np.array([0.0, 0.0, 0.5, 0.0])  # thick grass, no trees: where the falling sweep starts
PLAIN = replace(PRM, infiltration_feedback=False, fixed_cover=0.0)  # soaking as on bare soil
JUMP = 0.03  # least change of grass between neighboring rainfalls that counts as a jump


@cache
def sweeps() -> Array:
    """Grass along rising and falling rainfall: with the soaking loop, then without it."""

    def compute() -> Array:
        p = RAINS / scale()
        up, down = up_and_down(p, np.zeros(4), DENSE, PRM, trees=False)
        plain_up, plain_down = up_and_down(p, np.zeros(4), DENSE, PLAIN, trees=False)
        return np.array([up[:, 2], down[:, 2], plain_up[:, 2], plain_down[:, 2]])

    rows = "with the loop: up, down; without: up, down"  # part of the key: what is stored
    return stored("greening", (rows, RAINS, DENSE, PLAIN, scale()), compute, SWEEP_CODE)


def grass_axes(ax: Axes) -> None:
    """The axes that both grass sweeps share, so the two figures can be compared at a glance."""
    rain_axis(ax, float(RAINS[-1]), step=100.0)
    ax.set_ylim(-0.005, 0.35)
    ax.set_yticks([0.0, 0.1, 0.2, 0.3])
    ax.spines["left"].set_bounds(0.0, 0.3)
    ax.set_ylabel(GRASS_LABEL)


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    up, down, plain, _ = sweeps()
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.4))
    ax.plot(RAINS, plain, color=style.NEUTRAL.data, lw=0.8 * medium.line)
    rising = swept(ax, (RAINS, up), medium, style.GRASS.mark, JUMP)
    falling = swept(ax, (RAINS[::-1], down[::-1]), medium, style.GRASS.mark, JUMP)
    # Each sweep jumps once: name the direction of rainfall beside its arrow, on the side where
    # no curve passes: right of the rising jump, below the thick grass; left of the falling one.
    labels = ((rising[0], "rain rising", "left", 0.55), (falling[0], "rain falling", "right", 0.45))
    for (x, start, end), text, ha, along in labels:
        ax.text(
            x + (6.0 if ha == "left" else -6.0),
            start + along * (end - start),
            text,
            ha=ha,
            va="center",
            color=style.NEUTRAL.label,
            fontsize=medium.small,
        )
    # A key in the empty upper left, where nothing grows: which line has the soaking loop.
    for y, color, width, text in (
        (0.92, style.GRASS.mark, medium.line, "with the soaking loop"),
        (0.8, style.NEUTRAL.data, 0.8 * medium.line, "without it"),
    ):
        ax.plot([0.03, 0.09], [y, y], color=color, lw=width, transform=ax.transAxes)
        ax.text(
            0.11,
            y,
            text,
            ha="left",
            va="center",
            color=style.NEUTRAL.label,
            fontsize=medium.small,
            transform=ax.transAxes,
        )
    grass_axes(ax)
    return fig
