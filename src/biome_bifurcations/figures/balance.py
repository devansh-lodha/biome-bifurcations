# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Why grass jumps: with the soaking loop, a little grass can shrink while a lot of grass grows.

Grass alone, with soil water at its balance for each amount of grass. The curve is how fast each
unit of grass grows minus how fast it dies: above zero grass increases, below zero it decreases,
and where the curve crosses zero grass stays put. Filled dots are states grass returns to; the
open dot is a threshold it moves away from. At 300 mm the curve is above zero from bare ground
all the way to thick grass, so a few seeds grow without stopping: the jump. At 260 mm it starts
below zero, so a few seeds die, yet thick grass keeps itself going: the memory.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import GRASS_LABEL, PRM, scale
from biome_bifurcations.model import grass_balance

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAINS = (260.0, 300.0)  # mm/yr: inside the memory window, and above where grass appears
GRASS = np.linspace(0.0, 0.3, 601)


def net_growth(rain_mm: float) -> Array:
    """Growth minus death per unit of grass, with no trees and soil water at its balance."""
    return np.asarray(grass_balance(GRASS, 0.0, rain_mm / scale(), PRM))


def crossings(values: Array) -> list[tuple[float, bool]]:
    """Where a curve crosses zero, and whether grass returns there (it falls through zero)."""
    found = []
    for i in np.nonzero(np.sign(values[:-1]) * np.sign(values[1:]) < 0)[0]:
        g = GRASS[i] - values[i] * (GRASS[i + 1] - GRASS[i]) / (values[i + 1] - values[i])
        found.append((float(g), bool(values[i] > values[i + 1])))
    return found


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium: both rainfalls."""
    return draw_rains(medium, RAINS)


def draw_jump(medium: style.Medium) -> Figure:
    """Only the wetter rainfall, where a few seeds grow all the way to thick grass."""
    return draw_rains(medium, RAINS[1:])


def draw_memory(medium: style.Medium) -> Figure:
    """Only the drier rainfall, where a little grass dies but a lot keeps itself going."""
    return draw_rains(medium, RAINS[:1])


def draw_rains(medium: style.Medium, rains: tuple[float, ...]) -> Figure:
    """The growth-minus-death curves at the given rainfalls (mm/yr), on shared axes."""
    fig, ax = plt.subplots(figsize=style.full_size(medium, 0.4))
    ax.axhline(0.0, color=style.NEUTRAL.hairline, lw=0.6 * medium.line)
    for rain in rains:
        values = net_growth(rain)
        ax.plot(GRASS, values, color=style.GRASS.mark, lw=medium.line)
        ax.text(
            float(GRASS[-1]) + 0.004,
            float(values[-1]),
            f"{rain:.0f} mm",
            ha="left",
            va="center",
            color=style.NEUTRAL.label,
            fontsize=medium.small,
        )
        for g, returns in crossings(values):
            ax.plot(
                [g],
                [0.0],
                "o",
                ms=3.2 * medium.line,
                mfc=style.GRASS.mark if returns else style.NEUTRAL.paper,
                mec=style.GRASS.mark,
                mew=0.8 * medium.line,
            )
    for y, text, va in ((0.025, "grass grows", "bottom"), (-0.025, "grass shrinks", "top")):
        ax.text(0.295, y, text, ha="right", va=va, color=style.NEUTRAL.label, fontsize=medium.small)
    ax.set_xlim(0.0, float(GRASS[-1]))
    # The same vertical range in every version, so they compare at a glance.
    low = min(float(net_growth(r).min()) for r in RAINS)
    high = max(float(net_growth(r).max()) for r in RAINS)
    ax.set_ylim(1.1 * low, 1.1 * high)
    ax.set_xticks([0.0, 0.1, 0.2, 0.3])
    ax.set_yticks([0.0])
    ax.set_xlabel(GRASS_LABEL)
    ax.set_ylabel("Growth\nminus death")  # two lines, to fit beside the low axis
    return fig
