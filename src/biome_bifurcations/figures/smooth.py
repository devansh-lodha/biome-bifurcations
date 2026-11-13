# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""If plants did not open the soil, more rain would simply mean more grass.

Grass alone, with water soaking in everywhere as on bare soil, run to a steady state while
rainfall rises slowly and then falls back. Grass appears where a few seeds can just grow and
thickens gradually, and the falling sweep retraces the rising one exactly. The same axes as the
figure with the soaking loop, so the two compare at a glance.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from biome_bifurcations import style
from biome_bifurcations.figures import greening

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    _, _, up, down = greening.sweeps()
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.4))
    for g in (up, down):  # the two sweeps lie on top of each other
        ax.plot(greening.RAINS, g, color=style.GRASS.mark, lw=medium.line)
    ax.text(
        greening.RAINS[-1],
        float(up[-1]) + 0.012,
        "rain rising or falling: the same path",
        ha="right",
        va="bottom",
        color=style.NEUTRAL.label,
        fontsize=medium.small,
    )
    greening.grass_axes(ax)
    return fig
