# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Where neighboring patches share water, grass at the desert edge forms regular patterns.

Each map is one run at a fixed rainfall on a square of 128 by 128 patches. Every patch starts at
the even steady state of a single patch at that rainfall, with its grass nudged by about 1
percent at random. The run lasts long enough for the mean grass and the kind of pattern to
settle, though single spots and stripes still drift slowly (run twice as long, the maps look much
the same). As rainfall rises, spots give way to a maze and then to gaps. The bar is 200 units of
length, where one unit is about how far plants spread by seed in one unit of time; the square is
1100 units across.
"""

from functools import cache
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.layout_engine import ConstrainedLayoutEngine

from biome_bifurcations import style
from biome_bifurcations.figures.common import MAPS_CODE, PRM, scale, stored
from biome_bifurcations.parallel import parallel_map
from biome_bifurcations.simulate import Grid, run, seeded
from biome_bifurcations.steady import State, stable_states

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from biome_bifurcations.model import Array

RAINS = (183.0, 190.0, 198.0)  # mm/yr
KINDS = ("spots", "a maze", "gaps")  # the pattern each rainfall forms
GRID = Grid(length=1100.0, n=128, dims=2, dt=0.05)  # about five pattern spacings across
DURATION = 30000.0  # the kind of pattern is set by 20000; spots drift slowly after
NOISE, SEED = 0.01, 1
SCALE_BAR = 200.0  # length of the scale bar, in units of seed spreading


def _vegetated(rain: float) -> State:
    """The uniform vegetated state at a rainfall (mm/yr)."""
    return max(stable_states(rain / scale(), PRM), key=lambda s: s.g)


def _simulate(rain: float) -> Array:
    """Grass after DURATION, from the uniform state with slight unevenness."""
    state = _vegetated(rain)
    return run(seeded(state.vector, GRID, NOISE, SEED), state.p, PRM, GRID, DURATION)[2]


@cache
def _maps() -> Array:
    """The three grass maps, simulated in parallel once and then kept."""

    def simulate() -> Array:
        return np.array(parallel_map(_simulate, list(RAINS)))

    return stored("maps", (RAINS, GRID, DURATION, NOISE, SEED, scale()), simulate, MAPS_CODE)


def draw(medium: style.Medium) -> Figure:
    """Draw the figure for a medium."""
    maps = _maps()
    # Square maps need height to be seen; their slide has room to spare, so they take it.
    fig, axes = plt.subplots(1, len(RAINS), figsize=style.full_size(medium, 0.37, room=1.2))
    for ax, rain, kind, grass in zip(axes, RAINS, KINDS, maps, strict=True):
        ax.imshow(
            grass,
            cmap=style.BARE_TO_GRASS,
            vmin=0.0,
            vmax=float(maps.max()),
            interpolation="none",
            origin="lower",
            extent=(0, GRID.length, 0, GRID.length),
        )
        ax.set_axis_off()
        ax.set_title(
            f"{kind} at {rain:.0f} mm yr$^{{-1}}$", color=style.NEUTRAL.label, fontsize=medium.small
        )
    # The scale bar sits in a strip kept below the maps, so it cannot shrink the first one.
    engine = fig.get_layout_engine()
    if isinstance(engine, ConstrainedLayoutEngine):
        engine.set(rect=(0.0, 0.14, 1.0, 0.86))
    line = axes[0].plot(
        [40, 40 + SCALE_BAR],
        [-70, -70],
        color=style.NEUTRAL.text,
        lw=medium.line,
        solid_capstyle="butt",
        clip_on=False,
        scalex=False,  # the bar must not stretch the map's limits
        scaley=False,
    )[0]
    label = axes[0].text(
        40,
        -100,
        f"{SCALE_BAR:.0f} units of length",
        ha="left",
        va="top",
        color=style.NEUTRAL.label,
        fontsize=medium.small,
        clip_on=False,
    )
    for artist in (line, label):
        artist.set_in_layout(False)
    return fig
