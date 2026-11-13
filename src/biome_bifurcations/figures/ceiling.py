# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Tree cover rises with rainfall up to a ceiling near 80 percent.

The data: each site's tree cover against its rainfall, under the 99th-percentile ceiling. The
companion figure `spread` adds the spread of tree cover at one rainfall.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.data import fit_ceiling
from biome_bifurcations.figures.common import COVER_LABEL, rain_axis, sites

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def data_axes(medium: style.Medium) -> tuple[Figure, Axes]:
    """The sites and their ceiling, on the axes both data figures share."""
    data = sites()
    rain = np.linspace(data.rain.min(), data.rain.max(), 200)
    ceiling = 100 * fit_ceiling(data)(rain)
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.4))
    ax.scatter(data.rain, 100 * data.woody, s=1.5 * medium.line**2, color=style.NEUTRAL.data, lw=0)
    ax.plot(rain, ceiling, color=style.NEUTRAL.text, lw=medium.line)
    # Under the level end of the line no site comes close, so the label hides no data there, and
    # the space above stays free for the spread figure's label.
    ax.text(
        rain[-1],
        ceiling[-1] - 4,
        "ceiling",
        ha="right",
        va="top",
        color=style.NEUTRAL.text,
        fontsize=medium.small,
    )
    rain_axis(ax, 1500.0)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 50, 100])
    ax.set_ylabel(COVER_LABEL)
    return fig, ax


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    return data_axes(medium)[0]
