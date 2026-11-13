# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Fire spreads only once grass is thick enough to carry it.

How readily fire spreads, against the amount of grass: near zero while grass is too patchy for
flames to jump from clump to clump, then rising steeply to near one around the fuel level.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import GRASS_LABEL, PRM
from biome_bifurcations.model import fire_spread

if TYPE_CHECKING:
    from matplotlib.figure import Figure

GRASS = np.linspace(0.0, 0.5, 300)  # grass shown: well past the fuel level


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    fig, ax = plt.subplots(figsize=style.half_size(medium, 0.75))
    ax.plot(GRASS, np.asarray(fire_spread(GRASS, PRM)), color=style.FIRE.mark, lw=medium.line)
    for x, y, text, ha in (
        (0.02, 0.45, "fire dies out", "left"),
        (0.48, 0.85, "fire spreads", "right"),
    ):
        ax.text(x, y, text, ha=ha, va="center", color=style.NEUTRAL.label, fontsize=medium.small)
    ax.set_xlim(0.0, float(GRASS[-1]))
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks([0.0, PRM.gc, 0.4])
    ax.set_xticklabels(["0", r"$g_c$", "0.4"])
    ax.set_yticks([0.0, 1.0])
    ax.spines["left"].set_bounds(0.0, 1.0)
    ax.set_xlabel(GRASS_LABEL)
    ax.set_ylabel(r"Fire spread $F$")
    return fig
