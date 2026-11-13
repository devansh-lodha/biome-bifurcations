# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Regimes along the rainfall gradient and their landmarks.

The data set one number only: the rainfall scale S (mm/yr per model unit), chosen so the model's
no-fire tree-cover ceiling sits on top of the observed sites. Everything else is model output.

The regime labels below only name kinds of model states for reporting; they never feed back into
the model.
"""

import itertools
from dataclasses import dataclass, replace
from functools import cache, partial
from typing import TYPE_CHECKING

import numpy as np
from scipy.optimize import minimize_scalar

from biome_bifurcations.data import fit_rainfall_scale, load_sites, rainfall_scale_range
from biome_bifurcations.model import grass_balance, shade_effect
from biome_bifurcations.parallel import parallel_map
from biome_bifurcations.patterns import pattern_wavelength
from biome_bifurcations.steady import (
    bare_soil_threshold,
    break_even,
    stable_states,
    steady_states,
)

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
WOODLAND_GRASS = 0.1  # open woodland: at least this much grass,
WOODLAND_COVER = (0.05, 0.45)  # and canopy cover in this range


def is_forest(s: State) -> bool:
    """Closed canopy where fire does not spread."""
    return s.cover > FOREST_COVER and s.fire < FIRE


def is_burning(s: State) -> bool:
    """Savanna or grassland where fire spreads."""
    return s.fire > FIRE


def is_open_woodland(s: State) -> bool:
    """Grass with scattered trees, where fire does not spread.

    Not savanna, which the documents define by fire: grass that carries fire beneath trees.
    """
    low, high = WOODLAND_COVER
    return s.g >= WOODLAND_GRASS and low <= s.cover <= high and s.fire < FIRE


def is_grassland(s: State) -> bool:
    """Grass without trees."""
    return s.t == 0.0 and not s.bare


KINDS = ("bare", "grassy", "burning", "forest")  # kinds of state, in the order rainfall brings them


def kind(s: State) -> str:
    """What a state looks like: bare soil, grassy without fire, burning, or forest."""
    if s.bare:
        return "bare"
    if is_forest(s):
        return "forest"
    return "burning" if is_burning(s) else "grassy"


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


def _most_cover(p: float, prm: Params) -> float:
    """Canopy cover of the most wooded stable state at rainfall p, or 0 if there is none."""
    return max((s.cover for s in stable_states(p, prm)), default=0.0)


def ceiling(prm: Params, p: Array) -> Array:
    """The model's tree-cover ceiling: the most wooded stable state without fire or herbivores."""
    free = replace(prm, fire=False, graze=0.0, browse=0.0)
    return np.array(parallel_map(partial(_most_cover, prm=free), [float(x) for x in p]))


@cache
def model_ceiling(prm: Params) -> Array:
    """The tree-cover ceiling on CEILING_GRID, computed once per model."""
    return ceiling(prm, CEILING_GRID)


@cache
def rainfall_scale(prm: Params, data_path: Path) -> float:
    """Rainfall scale S from the data: the only quantity the data set. Cached, as it is costly."""
    return fit_rainfall_scale(CEILING_GRID, model_ceiling(prm), load_sites(data_path))


def scale_range(prm: Params, data_path: Path) -> tuple[float, float]:
    """The scales that fit the data within 1 percent of the best fit."""
    return rainfall_scale_range(CEILING_GRID, model_ceiling(prm), load_sites(data_path))


def model_ceiling_at(prm: Params, scale: float, rain_mm: float) -> float:
    """The model's ceiling on tree cover at a rainfall (mm/yr), interpolated as in the fit."""
    ceiling = model_ceiling(prm)
    log_p = np.log(rain_mm / scale)
    return float(np.interp(log_p, np.log(CEILING_GRID), ceiling, left=0.0, right=ceiling[-1]))


def grass_alone(prm: Params, scale: float) -> dict[str, float]:
    """Grass without trees: where bare soil greens, and the fold where grassland first appears.

    Grass-only steady states form one curve, the rainfall at which each amount of grass breaks
    even. At no grass it is the rainfall at which bare soil greens; its least value is the fold.
    """

    def rain(g: float) -> float:
        return scale * float(break_even(grass_balance, g, 0.0, prm))

    fold = minimize_scalar(rain, bounds=(0.0, 0.99), method="bounded", options={"xatol": 1e-9})
    return {"greens_mm": rain(0.0), "fold_mm": float(fold.fun), "fold_grass": float(fold.x)}


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
    return parallel_map(task, [float(r) for r in rain])


@dataclass(frozen=True)
class Regime:
    """A stretch of rainfall (mm/yr) over which the same kinds of state are stable."""

    kinds: tuple[str, ...]  # in the order of KINDS
    low: float
    high: float


def regimes(points: list[Point]) -> list[Regime]:
    """The regimes along a scan. Boundaries lie midway, in log rainfall, between scan points."""
    kinds = [tuple(k for k in KINDS if any(kind(s) == k for s in pt.stable)) for pt in points]
    rain = np.array([pt.rain for pt in points])
    middle = np.sqrt(rain[:-1] * rain[1:])
    edges = [0, *(i + 1 for i in range(len(kinds) - 1) if kinds[i + 1] != kinds[i]), len(kinds)]
    return [
        Regime(
            kinds[a],
            float(rain[0] if a == 0 else middle[a - 1]),
            float(rain[-1] if b == len(kinds) else middle[b - 1]),
        )
        for a, b in itertools.pairwise(edges)
    ]


def _span(values: list[float]) -> tuple[float, float] | None:
    """Smallest and largest value, or None if there are none."""
    return (min(values), max(values)) if values else None


def _shade_switch(prm: Params, scale: float, points: list[Point]) -> float | None:
    """Least rainfall at which shade, after helping the densest tree-free grassland, hurts it.

    Tree-free grassland is the unshaded reference, whether or not trees could invade it. If shade
    never helps, or never hurts, there is no switch.
    """
    helped = False
    for pt in points:
        grass = [s.g for s in pt.states if is_grassland(s)]
        if grass:
            effect = shade_effect(max(grass), pt.rain / scale, prm)
            if effect < 0 and helped:
                return pt.rain
            helped = helped or effect > 0
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
    woodland = where(lambda pt: any(is_open_woodland(s) for s in pt.stable))
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
        "open_woodland_mm": _span(woodland),
        "shade_switch_mm": _shade_switch(prm, scale, points),
        "fire_onset_mm": min(burning, default=None),
        "savanna_or_forest_mm": _span(two_states),
        "forest_only_from_mm": min(forest_only, default=None),
    }


# Each mechanism switched off, with the fact (model.py) it comes from.
SWITCHES: tuple[tuple[str, str, Callable[[Params], Params]], ...] = (
    ("2", "plants open the soil to rain", lambda prm: replace(prm, infiltration_feedback=False)),
    ("4", "only trees reach deep water", lambda prm: replace(prm, theta=0.0)),
    ("5", "shade slows drying", lambda prm: replace(prm, shade_evaporation=False)),
    ("5", "shade caps grass", lambda prm: replace(prm, shade_light=False)),
    ("5", "tree seedlings need light", lambda prm: replace(prm, seedling_light=False)),
    ("6", "fire spreads through grass", lambda prm: replace(prm, fire=False)),
    ("7", "water spreads faster than seeds", lambda prm: replace(prm, d_o=1.0, d_w=1.0)),
)
FEATURES = (  # what the gradient shows, in the order rainfall brings it
    "desert",
    "desert tipping",
    "patterns",
    "open woodland",
    "shade switch",
    "grassland",
    "savanna",
    "savanna-forest tipping",
    "forest",
)


def _where(points: list[Point], test: Callable[[Point], bool]) -> tuple[float, float] | None:
    """The span of rainfall (mm/yr) over which a test holds, or None if it never does."""
    return _span([pt.rain for pt in points if test(pt)])


def features(prm: Params, scale: float, rain: Array) -> dict[str, tuple[float, float]]:
    """Where (mm/yr) a version of the model shows each feature of the gradient.

    The regimes are those of the main figure: desert, open woodland (trees and grass, no fire),
    grassland (no trees), savanna (trees under fire), forest. A switch is a single rainfall.
    """
    points = scan(prm, scale, rain)
    marks = landmarks(prm, scale, points)
    spans = {
        "desert": _where(points, lambda pt: bool(pt.stable) and all(s.bare for s in pt.stable)),
        "desert tipping": _where(
            points,
            lambda pt: any(s.bare for s in pt.stable) and any(not s.bare for s in pt.stable),
        ),
        "patterns": marks["patterns_mm"],
        "open woodland": _where(
            points,
            lambda pt: any(kind(s) == "grassy" and s.t > 0 and s.g > 0 for s in pt.stable),
        ),
        "shade switch": (marks["shade_switch_mm"],) * 2 if marks["shade_switch_mm"] else None,
        "grassland": _where(points, lambda pt: any(s.t == 0 and not s.bare for s in pt.stable)),
        "savanna": _where(points, lambda pt: any(is_burning(s) and s.t > 0 for s in pt.stable)),
        "savanna-forest tipping": _where(
            points,
            lambda pt: (
                any(is_burning(s) for s in pt.stable) and any(is_forest(s) for s in pt.stable)
            ),
        ),
        "forest": _where(points, lambda pt: any(is_forest(s) for s in pt.stable)),
    }
    return {name: span for name in FEATURES if isinstance(span := spans[name], tuple)}


@dataclass(frozen=True)
class Mechanism:
    """What switching off one mechanism does to the gradient."""

    fact: str  # the fact it comes from (model.py)
    mechanism: str
    lost: list[str]  # features of the full model that disappear
    features: dict[str, tuple[float, float]]  # where each remaining feature lies (mm/yr)


def mechanisms(prm: Params, scale: float, rain: Array) -> list[Mechanism]:
    """For each mechanism switched off: what disappears, and where each feature now lies."""
    full = features(prm, scale, rain)
    rows = []
    for fact, name, switch_off in SWITCHES:
        found = features(switch_off(prm), scale, rain)
        rows.append(Mechanism(fact, name, [f for f in full if f not in found], found))
    return rows


# Robustness: every constant of the model halved, then raised by half, one at a time. Shares stay
# at most 1. The rainfall scale stays the one fitted to the representative model, so the check
# asks only whether each feature still appears, not where.
ROBUST_FACTORS = (0.5, 1.5)
ROBUST_CONSTANTS = ("eps", "beta", "theta", "u", "k", "gc", "n", "h", "m_g", "m_t", "d_o")
SHARES = frozenset({"theta", "h"})  # fractions of a whole, which cannot exceed 1


@dataclass(frozen=True)
class Variation:
    """What changing one constant does to the gradient."""

    constant: str
    factor: float
    value: float  # the changed value, capped at 1 for a share
    lost: list[str]  # features of the representative model that disappear


def robustness(prm: Params, scale: float, rain: Array) -> list[Variation]:
    """Which features survive when each constant is halved or raised by half, one at a time."""
    full = features(prm, scale, rain)
    rows = []
    for name in ROBUST_CONSTANTS:
        for factor in ROBUST_FACTORS:
            value = getattr(prm, name) * factor
            if name in SHARES:
                value = min(value, 1.0)
            found = features(replace(prm, **{name: value}), scale, rain)
            rows.append(Variation(name, factor, value, [f for f in full if f not in found]))
    return rows
