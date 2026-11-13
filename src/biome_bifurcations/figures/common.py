# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""What the figures share: inputs computed once, the axes, and how sweeps and jumps are drawn."""

import hashlib
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from biome_bifurcations import model, settle, simulate, steady, style
from biome_bifurcations.analysis import rainfall_scale
from biome_bifurcations.data import DATA, Sites, load_sites
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from matplotlib.axes import Axes

    from biome_bifurcations.model import Array

PRM = Params()
STORE = Path(__file__).resolve().parents[3] / "cache" / "figures"  # costly results, kept
RAIN_LABEL = r"Rainfall (mm yr$^{-1}$)"
COVER_LABEL = r"Tree cover (\%)"
GRASS_LABEL = r"Grass biomass $G$"
TIME_LABEL = "Time (drying times of bare soil)"


@cache
def scale() -> float:
    """The rainfall scale the data set (mm/yr per model unit)."""
    return rainfall_scale(PRM, DATA)


@cache
def sites() -> Sites:
    """The field sites."""
    return load_sites(DATA)


def rain_axis(ax: Axes, high: float, step: float = 500.0) -> None:
    """A plain rainfall axis from zero, ticked every step mm/yr."""
    ax.set_xlim(0.0, high)
    ax.set_xticks(np.arange(0.0, high + 1.0, step))
    ax.set_xlabel(RAIN_LABEL)


def jump(ax: Axes, x: float, start: float, end: float, medium: style.Medium) -> None:
    """An arrow for a tipping point, from the state that vanishes to the one it falls into."""
    ax.annotate(
        "",
        xy=(x, end),
        xytext=(x, start),
        arrowprops={
            "arrowstyle": "-|>",
            "color": style.NEUTRAL.label,
            "lw": 0.6 * medium.line,
            "mutation_scale": 5 * medium.line,
            "shrinkA": 3,
            "shrinkB": 3,
        },
    )


def lines(
    ax: Axes, sweep: tuple[Array, Array], medium: style.Medium, color: str, jump_size: float
) -> list[tuple[float, float, float]]:
    """A rainfall sweep as lines, broken where it jumps.

    Args:
        ax: Where to draw.
        sweep: Rainfall (mm/yr) and the settled value there, in the order rainfall was visited.
        medium: The medium, for line widths.
        color: Line color.
        jump_size: Least change between neighboring rainfalls that counts as a jump.

    Returns:
        Each jump as (rainfall after the jump, value before, value after).
    """
    rain, value = sweep
    settled = ~np.isnan(value)  # a run still changing is no steady state: leave it out
    rain, value = rain[settled], value[settled]
    breaks = np.nonzero(np.abs(np.diff(value)) > jump_size)[0] + 1
    for part in np.split(np.arange(len(rain)), breaks):
        ax.plot(rain[part], value[part], color=color, lw=medium.line)
    return [(float(rain[i]), float(value[i - 1]), float(value[i])) for i in breaks]


def swept(
    ax: Axes, sweep: tuple[Array, Array], medium: style.Medium, color: str, jump_size: float
) -> list[tuple[float, float, float]]:
    """A rainfall sweep as lines, broken where it jumps, with an arrow across each jump.

    Arguments and result as for `lines`.
    """
    jumps = lines(ax, sweep, medium, color, jump_size)
    for x, start, end in jumps:
        jump(ax, x, start, end, medium)
    return jumps


MAPS_CODE = (model, simulate, steady)  # what the pattern maps depend on
SWEEP_CODE = (model, settle)  # what rainfall sweeps depend on


def stored(
    name: str, inputs: object, compute: Callable[[], Array], code: tuple[ModuleType, ...]
) -> Array:
    """A costly array, computed once for each version of its inputs and of the code it uses.

    The key hashes the modules the computation depends on, so figure edits never rerun it, while
    any change to that code does.
    """
    digest = hashlib.sha256(repr(inputs).encode())
    for module in code:
        digest.update(Path(str(module.__file__)).read_bytes())
    path = STORE / f"{name}-{digest.hexdigest()[:16]}.npy"
    if path.exists():
        return np.load(path)
    result = compute()
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, result)
    return result
