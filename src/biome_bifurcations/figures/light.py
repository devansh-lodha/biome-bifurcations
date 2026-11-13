# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Each layer of leaves lets through the same share of light, so shade deepens fast.

The share of sunlight that reaches the ground under a canopy, against the amount of trees: it
falls by the same fraction for every added layer of leaves, which makes an exponential decline.
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from biome_bifurcations import style
from biome_bifurcations.figures.common import PRM
from biome_bifurcations.model import light

if TYPE_CHECKING:
    from matplotlib.figure import Figure

TREES = np.linspace(0.0, 0.4, 200)  # tree biomass shown: up to almost closed canopy


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    fig, ax = plt.subplots(figsize=style.half_size(medium, 0.75))
    ax.plot(TREES, 100 * np.asarray(light(TREES, PRM)), color=style.TREES.mark, lw=medium.line)
    ax.set_xlim(0.0, float(TREES[-1]))
    ax.set_ylim(0, 100)
    ax.set_xticks([0.0, 0.2, 0.4])
    ax.set_yticks([0, 50, 100])
    ax.set_xlabel(r"Tree biomass $T$")
    # Two lines, so the label fits beside the short axis of a half-width figure.
    ax.set_ylabel("Light reaching\n" + r"the ground (\%)")
    return fig
