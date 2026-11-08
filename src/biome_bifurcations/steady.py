# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Exact steady states and their stability.

Water settles fast, so at steady state it is an explicit function of G and T (model.soil_water).
Steady states then solve grass_balance = 0 or G = 0, together with tree_balance = 0 or T = 0:

- bare soil: G = T = 0;
- grass only or trees only: one-dimensional roots, bracketed on a grid and refined with Brent's
  method;
- coexistence: crossings of the grass and tree nullclines, found by tracing the grass nullcline
  as a contour line, bracketing sign changes of tree_balance along it, and polishing with a
  quasi-Newton root finder.

No time stepping is involved, so unstable states (the thresholds between basins) are found too.
Stability comes from the eigenvalues of the exact four-variable Jacobian.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from contourpy import contour_generator
from scipy.optimize import brentq, fsolve

from biome_bifurcations.model import (
    Array,
    Params,
    cover,
    fire_spread,
    full_state,
    grass_balance,
    jacobian,
    soil_water,
    tree_balance,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from biome_bifurcations.model import Scalar

# Search grids. Light caps grass below 1; self-shaded trees can exceed 1.
G_GRID = np.unique(np.concatenate([np.geomspace(1e-5, 0.02, 40), np.linspace(0.02, 0.999, 400)]))
T_GRID = np.unique(np.concatenate([G_GRID, np.linspace(1.0, 8.0, 120)]))

# Tolerances. Roots are refined to near machine precision; the looser values below only tell
# genuine results apart from rounding noise.
ROOT_TOL = 1e-13  # Brent's method: width of the final bracket
POLISH_TOL = 1e-12  # polishing: relative size of the final step
RESIDUAL_TOL = 1e-9  # largest balance residual accepted at a polished crossing
SAME_STATE = 1e-7  # crossings closer than this in both G and T are one state
PRESENT = 1e-9  # least biomass of each plant type at an accepted crossing
GROWTH_TOL = 1e-12  # growth rates within this of zero count as zero
BARE = 1e-6  # biomass below which a state counts as bare soil


@dataclass(frozen=True)
class State:
    """One steady state at rainfall p."""

    p: float
    o: float
    w: float
    g: float
    t: float
    growth: float  # largest real part of the Jacobian eigenvalues
    cover: float  # tree canopy cover
    fire: float  # fire spread F(G)

    @property
    def vector(self) -> Array:
        """The state as an array (O, w, G, T)."""
        return np.array([self.o, self.w, self.g, self.t], dtype=np.float64)

    @property
    def stable(self) -> bool:
        """Whether every small disturbance decays."""
        return self.growth < -GROWTH_TOL

    @property
    def bare(self) -> bool:
        """Whether the state is bare soil."""
        return self.g < BARE and self.t < BARE


def _sign_changes(v: Array) -> Array:
    """Indices i at which v changes sign between v[i] and v[i + 1]."""
    return np.nonzero(np.sign(v[:-1]) * np.sign(v[1:]) < 0)[0]


def _roots(f: Callable[[Array], Scalar], grid: Array) -> list[float]:
    """All roots of f on the grid: bracket sign changes, refine each with Brent's method."""

    def scalar_f(x: float) -> float:
        return float(np.asarray(f(np.array([x])))[0])

    brackets = _sign_changes(np.asarray(f(grid)))
    return [float(brentq(scalar_f, grid[i], grid[i + 1], xtol=ROOT_TOL)) for i in brackets]


def _state(w: float, g: float, t: float, p: float, prm: Params) -> State:
    """Steady state with its stability, from soil water, grass, and trees."""
    y = full_state(w, g, t, p, prm)
    return State(
        p=p,
        o=float(y[0]),
        w=w,
        g=g,
        t=t,
        growth=float(np.linalg.eigvals(jacobian(y, p, prm)).real.max()),
        cover=float(cover(t, prm)),
        fire=float(fire_spread(g, prm)),
    )


def _polish(start: Array, p: float, prm: Params) -> tuple[float, float] | None:
    """Polish a nullcline crossing with a quasi-Newton root finder; None if it is not a root.

    Success is judged by the residuals themselves, not by the solver's progress flag, which can
    report failure near the steep fire threshold even after converging to machine precision.
    """

    def residual(z: Array) -> list[float]:
        return [float(grass_balance(z[0], z[1], p, prm)), float(tree_balance(z[0], z[1], p, prm))]

    # The full output makes the solver return its status instead of warning about it.
    sol = fsolve(residual, start, xtol=POLISH_TOL, full_output=True)[0]
    if max(abs(r) for r in residual(sol)) >= RESIDUAL_TOL:
        return None
    return float(sol[0]), float(sol[1])


def steady_states(p: float, prm: Params) -> list[State]:
    """Every steady state at rainfall p, stable or not."""

    def grass_only(g: Array) -> Scalar:
        return grass_balance(g, 0.0, p, prm)

    def trees_only(t: Array) -> Scalar:
        return tree_balance(0.0, t, p, prm)

    found: list[tuple[float, float]] = [(0.0, 0.0)]
    found += [(g, 0.0) for g in _roots(grass_only, G_GRID)]
    found += [(0.0, t) for t in _roots(trees_only, T_GRID)]
    gg, tt = np.meshgrid(G_GRID, T_GRID, indexing="xy")
    nullcline = contour_generator(x=G_GRID, y=T_GRID, z=grass_balance(gg, tt, p, prm)).lines(0.0)
    for piece in nullcline:
        line = np.asarray(piece)
        for i in _sign_changes(np.asarray(tree_balance(line[:, 0], line[:, 1], p, prm))):
            crossing = _polish(0.5 * (line[i] + line[i + 1]), p, prm)
            if crossing is None:
                continue
            g, t = crossing
            new = not any(abs(g - a) < SAME_STATE and abs(t - b) < SAME_STATE for a, b in found)
            if g > PRESENT and PRESENT < t < T_GRID[-1] and new:
                found.append((g, t))
    return [_state(float(soil_water(g, t, p, prm)), g, t, p, prm) for g, t in found]


def stable_states(p: float, prm: Params) -> list[State]:
    """Every stable steady state at rainfall p."""
    return [s for s in steady_states(p, prm) if s.stable]


def bare_soil_threshold(prm: Params) -> float:
    """Rainfall above which bare soil is unstable, because some plant can grow there from rare.

    On bare soil every water store is proportional to rainfall, so each plant's balance b is
    linear in p and turns positive at p = -b(0) / (b(1) - b(0)).
    """

    def threshold(balance: Callable[[float, float, float, Params], Scalar]) -> float:
        at_0, at_1 = float(balance(0.0, 0.0, 0.0, prm)), float(balance(0.0, 0.0, 1.0, prm))
        return -at_0 / (at_1 - at_0)

    return min(threshold(grass_balance), threshold(tree_balance))
