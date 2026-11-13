# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Run forward in time, grass grows from a few seeds and settles at a steady level.

Grass alone, at one rainfall, starting from bare soil with a few seeds. Solved over time, grass
rises slowly at first, then quickly, and stops where its growth balances its loss: a steady
state.
"""

from functools import cache
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import GRASS_LABEL, PRM, TIME_LABEL, scale
from biome_bifurcations.settle import SEED, path

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAIN_MM = 350.0  # where grass grows from seeds
DURATION = 2500.0  # long enough to see grass settle


@cache
def grass() -> tuple[Array, Array]:
    """Times and grass along the run from bare soil with a few seeds."""
    times = np.linspace(0.0, DURATION, 500)
    start = np.array([0.0, 0.0, SEED, 0.0])  # no water, a few grass seeds, no trees
    return times, path(start, RAIN_MM / scale(), PRM, times)[2]


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    times, g = grass()
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.36))
    ax.plot(times, g, color=style.GRASS.mark, lw=medium.line)
    ax.text(
        times[-1],
        float(g[-1]) + 0.012,
        "steady state",
        ha="right",
        va="bottom",
        color=style.NEUTRAL.label,
        fontsize=medium.small,
    )
    ax.set_xlim(0.0, DURATION)
    ax.set_ylim(0.0, 0.3)
    ax.set_yticks([0.0, 0.1, 0.2, 0.3])
    ax.set_xlabel(TIME_LABEL)
    ax.set_ylabel(GRASS_LABEL)
    return fig
