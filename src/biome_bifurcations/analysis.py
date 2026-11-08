# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Regimes along the rainfall gradient and their landmarks.

The data set one number only: the rainfall scale S (mm/yr per model unit), chosen so the model's
no-fire tree-cover ceiling sits on top of the observed sites. Everything else is model output.

The regime labels below only name kinds of model states for reporting; they never feed back into
the model.
"""

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from functools import cache, partial
from typing import TYPE_CHECKING

import numpy as np

from biome_bifurcations.data import fit_rainfall_scale, load_sites
from biome_bifurcations.model import shade_effect
from biome_bifurcations.patterns import pattern_wavelength
from biome_bifurcations.steady import bare_soil_threshold, stable_states, steady_states

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from biome_bifurcations.model import Array, Params
    from biome_bifurcations.steady import State

# Rainfall (model units) at which the ceiling is computed. The ceiling jumps where vegetation
# first appears, and S is fitted across that jump, so the grid must be fine: refining it further
# changes S by less than 0.2 percent (a test checks).
CEILING_GRID = np.geomspace(0.05, 300.0, 1600)

# Regime labels. Fire spreads where F(G) > 1/2, which is exactly where grass exceeds its fuel
# threshold gc. The other cutoffs are round values that only name kinds of states.
FIRE = 0.5
FOREST_COVER = 0.7  # forest: closed canopy with more cover than this
DRY_SAVANNA_GRASS = 0.1  # dry savanna: at least this much grass,
DRY_SAVANNA_COVER = (0.05, 0.45)  # and canopy cover in this range


def is_forest(s: State) -> bool:
    """Closed canopy where fire does not spread."""
    return s.cover > FOREST_COVER and s.fire < FIRE


def is_burning(s: State) -> bool:
    """Savanna or grassland where fire spreads."""
    return s.fire > FIRE


def is_dry_savanna(s: State) -> bool:
    """Grass with scattered trees, where fire does not spread."""
    low, high = DRY_SAVANNA_COVER
    return s.g >= DRY_SAVANNA_GRASS and low <= s.cover <= high and s.fire < FIRE


def is_grassland(s: State) -> bool:
    """Grass without trees."""
    return s.t == 0.0 and not s.bare


@dataclass(frozen=True)
class Point:
    """Steady states at one rainfall, with the wavelength of any pattern a state would form."""

    rain: float  # mm/yr
    states: list[State]  # all steady states, stable or not
    wavelengths: dict[int, float]  # index into states -> wavelength of the patterns it forms

    @property
    def stable(self) -> list[State]:
        """The stable steady states."""
        return [s for s in self.states if s.stable]


def _parallel[T, R](task: Callable[[T], R], items: list[T]) -> list[R]:
    """The task applied to each item, in order, spread across all cores."""
    # About four chunks per core balance the load against the cost of sending work.
    chunk = max(1, len(items) // (4 * (os.process_cpu_count() or 1)))
    with ProcessPoolExecutor() as pool:
        return list(pool.map(task, items, chunksize=chunk))


def _most_cover(p: float, prm: Params) -> float:
    """Canopy cover of the most wooded stable state at rainfall p, or 0 if there is none."""
    return max((s.cover for s in stable_states(p, prm)), default=0.0)


def ceiling(prm: Params, p: Array) -> Array:
    """The model's tree-cover ceiling: the most wooded stable state without fire or herbivores."""
    free = replace(prm, fire=False, graze=0.0, browse=0.0)
    return np.array(_parallel(partial(_most_cover, prm=free), [float(x) for x in p]))


@cache
def rainfall_scale(prm: Params, data_path: Path) -> float:
    """Rainfall scale S from the data: the only quantity the data set. Cached, as it is costly."""
    return fit_rainfall_scale(CEILING_GRID, ceiling(prm, CEILING_GRID), load_sites(data_path))


def _point(rain: float, *, scale: float, prm: Params, patterns: bool) -> Point:
    """Steady states at one rainfall (mm/yr), with pattern wavelengths if asked."""
    states = steady_states(rain / scale, prm)
    waves: dict[int, float] = {}
    if patterns:
        for i, s in enumerate(states):
            lam = pattern_wavelength(s, prm)
            if lam is not None:
                waves[i] = lam
    return Point(rain, states, waves)


def scan(prm: Params, scale: float, rain: Array, *, patterns: bool = True) -> list[Point]:
    """Steady states at each rainfall value (mm/yr), computed in parallel across cores."""
    task = partial(_point, scale=scale, prm=prm, patterns=patterns)
    return _parallel(task, [float(r) for r in rain])


def _span(values: list[float]) -> tuple[float, float] | None:
    """Smallest and largest value, or None if there are none."""
    return (min(values), max(values)) if values else None


def _shade_switch(prm: Params, scale: float, points: list[Point]) -> float | None:
    """Least rainfall at which shade hurts the densest tree-free grassland.

    Tree-free grassland is the unshaded reference, whether or not trees could invade it.
    """
    for pt in points:
        grass = [s.g for s in pt.states if is_grassland(s)]
        if grass and shade_effect(max(grass), pt.rain / scale, prm) < 0:
            return pt.rain
    return None


def landmarks(prm: Params, scale: float, points: list[Point]) -> dict[str, object]:
    """Where each regime boundary falls along the rainfall gradient (mm/yr)."""

    def where(test: Callable[[Point], bool]) -> list[float]:
        return [pt.rain for pt in points if test(pt)]

    vegetated = where(lambda pt: any(not s.bare for s in pt.stable))
    bistable_desert = where(
        lambda pt: any(s.bare for s in pt.stable) and any(not s.bare for s in pt.stable)
    )
    patterned = where(lambda pt: bool(pt.wavelengths))
    dry = where(lambda pt: any(is_dry_savanna(s) for s in pt.stable))
    burning = where(lambda pt: any(is_burning(s) for s in pt.stable))
    two_states = where(
        lambda pt: any(is_burning(s) for s in pt.stable) and any(is_forest(s) for s in pt.stable)
    )
    forest_only = where(lambda pt: bool(pt.stable) and all(is_forest(s) for s in pt.stable))
    return {
        "rainfall_scale_mm_per_unit": scale,
        "vegetation_from_mm": min(vegetated, default=None),
        "bare_soil_greens_above_mm": scale * bare_soil_threshold(prm),
        "desert_or_vegetation_mm": _span(bistable_desert),
        "patterns_mm": _span(patterned),
        "fire_free_dry_savanna_mm": _span(dry),
        "shade_switch_mm": _shade_switch(prm, scale, points),
        "fire_onset_mm": min(burning, default=None),
        "savanna_or_forest_mm": _span(two_states),
        "forest_only_from_mm": min(forest_only, default=None),
    }
