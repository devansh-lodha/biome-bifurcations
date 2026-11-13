# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""With one fitted number, the model's ceiling on tree cover bounds the sites.

Tree cover at each site against its rainfall, under the most wooded stable state of the model
without fire. The data set only the rainfall scale, which stretches the model's rainfall axis
until its ceiling sits on the sites.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from biome_bifurcations import style
from biome_bifurcations.analysis import CEILING_GRID, model_ceiling
from biome_bifurcations.figures.common import COVER_LABEL, PRM, rain_axis, scale, sites

if TYPE_CHECKING:
    from matplotlib.figure import Figure

RAIN_MAX = 1500.0  # mm/yr, as in the figure of the data alone


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    data = sites()
    rain, ceiling = scale() * CEILING_GRID, 100 * model_ceiling(PRM)
    shown = rain <= RAIN_MAX
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.4))
    ax.scatter(data.rain, 100 * data.woody, s=1.5 * medium.line**2, color=style.NEUTRAL.data, lw=0)
    ax.plot(rain[shown], ceiling[shown], color=style.TREES.mark)
    ax.text(
        RAIN_MAX,
        float(ceiling[shown][-1]) + 3,
        "model ceiling",
        ha="right",
        va="bottom",
        color=style.NEUTRAL.label,
        fontsize=medium.small,
    )
    rain_axis(ax, RAIN_MAX)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 50, 100])
    ax.set_ylabel(COVER_LABEL)
    return fig
