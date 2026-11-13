# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Below the ceiling, places with the same rainfall range from no trees to the ceiling.

The data figure again, with an arrow spanning the sites that get about the same rain, from the
barest to the most wooded. Its label sits beside the arrow's tip, where no site lies, so it hides
no data.
"""

from typing import TYPE_CHECKING

from biome_bifurcations import style
from biome_bifurcations.data import spread
from biome_bifurcations.figures.ceiling import data_axes
from biome_bifurcations.figures.common import sites

if TYPE_CHECKING:
    from matplotlib.figure import Figure

SPREAD_MM = 800.0  # where the spread is shown: past the knee, with many sites
WINDOW_MM = 25.0  # sites within this much of SPREAD_MM count as getting the same rain


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    fig, ax = data_axes(medium)
    low, high = (100 * c for c in spread(sites(), SPREAD_MM, WINDOW_MM))
    ax.annotate(
        "",
        xy=(SPREAD_MM, high),
        xytext=(SPREAD_MM, low),
        arrowprops={
            "arrowstyle": "<|-|>",
            "color": style.NEUTRAL.text,
            "lw": 0.8 * medium.line,
            "mutation_scale": 6 * medium.line,
            "shrinkA": 0,
            "shrinkB": 0,
        },
    )
    # Above the tip and to its right, every site has less cover than the label's lower edge.
    ax.text(
        SPREAD_MM + 15.0,
        high + 13.0,
        f"same rain, {SPREAD_MM:.0f} mm a year",
        ha="left",
        va="center",
        color=style.NEUTRAL.text,
        fontsize=medium.small,
    )
    return fig
