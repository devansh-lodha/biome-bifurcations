# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""With fire, the same rainfall ends in savanna or forest, and the start decides which.

Two runs at one rainfall inside the range where savanna and forest both persist, from nearly the
same mix of grass and trees. With a little less tree cover, grass carries fire, which holds the
trees down: savanna. With a little more, shade thins the grass until fire cannot spread: forest.
"""

from functools import cache
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import COVER_LABEL, PRM, TIME_LABEL, scale
from biome_bifurcations.model import cover
from biome_bifurcations.settle import path

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAIN_MM = 1100.0  # inside the range where savanna and forest both persist
GRASS = 0.3  # grass at the start of both runs
START_COVER = (70.0, 76.0)  # percent tree cover at the start: just below and above the divide
DURATION = 6000.0  # long enough for both runs to settle


def _trees(percent: float) -> float:
    """Tree biomass that gives a tree cover (percent): cover is 1 - exp(-k T)."""
    return -float(np.log(1.0 - percent / 100.0)) / PRM.k


@cache
def runs() -> tuple[Array, Array]:
    """Times, and tree cover (percent) along each run, one row per start."""
    times = np.linspace(0.0, DURATION, 600)
    p = RAIN_MM / scale()
    covers = [
        100 * np.asarray(cover(path(np.array([0.0, 0.0, GRASS, _trees(c)]), p, PRM, times)[3], PRM))
        for c in START_COVER
    ]
    return times, np.array(covers)


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    times, covers = runs()
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.36))
    ends = (("savanna", style.FIRE), ("forest", style.TREES))  # the lower start ends in savanna
    for c, (name, role) in zip(covers.tolist(), ends, strict=True):
        ax.plot(times, c, color=role.mark, lw=medium.line)
        ax.text(
            times[-1],
            float(c[-1]) + 3.0,
            name,
            ha="right",
            va="bottom",
            color=role.ink,
            fontsize=medium.small,
        )
    ax.set_xlim(0.0, DURATION)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 50, 100])
    ax.set_xlabel(TIME_LABEL)
    ax.set_ylabel(COVER_LABEL)
    return fig
