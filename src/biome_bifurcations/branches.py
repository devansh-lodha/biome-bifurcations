# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Branches of steady states along rainfall, traced exactly.

With vegetation held fixed, each plant breaks even at an explicit rainfall (steady.break_even).
So every branch of steady states can be followed along vegetation, with rainfall coming out as a
result instead of being stepped:

- grass only (T = 0): p = break_even(grass) as G runs over its grid;
- trees only (G = 0): p = break_even(trees) as T runs over its grid;
- grass and trees: where both break even at the same rainfall, the zero contour of
  ln p_grass - ln p_trees in the (G, T) plane, polished onto the exact curve;
- bare soil: G = T = 0 at every rainfall.

Folds, where two states merge and vanish, then appear as smooth turns of a curve, and no state is
lost between rainfall steps.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from contourpy import contour_generator

from biome_bifurcations.model import (
    COMPLEX_STEP,
    Array,
    Params,
    Scalar,
    grass_balance,
    tree_balance,
)
from biome_bifurcations.steady import G_GRID, T_GRID, bare_soil_threshold, break_even, state_at

if TYPE_CHECKING:
    from numpy.typing import NDArray

POLISH_STEPS = 6  # Newton projections onto the curve; each roughly squares the error
MISMATCH_TOL = 1e-10  # largest |ln p_grass - ln p_trees| accepted after polishing
BARE_POINTS = 400  # samples along the bare-soil branch


@dataclass(frozen=True)
class Branch:
    """Steady states along one branch, in order along it."""

    kind: str  # which plants are present: "bare", "grass", "trees", or "both"
    p: Array
    g: Array
    t: Array
    stable: NDArray[np.bool_]  # whether each state is stable


def _mismatch(g: Scalar, t: Scalar, prm: Params) -> Scalar:
    """Log ratio of the rainfalls at which grass and trees break even; zero where both do."""
    return np.log(break_even(grass_balance, g, t, prm) / break_even(tree_balance, g, t, prm))


def _polish(g: Array, t: Array, prm: Params) -> tuple[Array, Array]:
    """Move points onto the curve of zero mismatch, along its exact gradient."""
    for _ in range(POLISH_STEPS):
        miss = _mismatch(g, t, prm)
        # Complex steps give exact slopes; the model takes complex input (model.py).
        d_g = np.imag(_mismatch(np.add(g, 1j * COMPLEX_STEP), t, prm)) / COMPLEX_STEP
        d_t = np.imag(_mismatch(g, np.add(t, 1j * COMPLEX_STEP), prm)) / COMPLEX_STEP
        step = miss / (d_g * d_g + d_t * d_t)
        g, t = g - step * d_g, t - step * d_t
    return g, t


def _pieces(
    kind: str, curve: tuple[Array, Array, Array], prm: Params, p_range: tuple[float, float]
) -> list[Branch]:
    """The stretches of a curve (p, g, t) inside the rainfall range, with each state's stability."""
    p, g, t = curve
    inside = np.isfinite(p) & (p >= p_range[0]) & (p <= p_range[1])
    runs = np.split(np.arange(len(p)), np.nonzero(np.diff(inside.astype(np.int8)))[0] + 1)
    return [
        Branch(
            kind,
            p[run],
            g[run],
            t[run],
            np.array([state_at(float(g[i]), float(t[i]), float(p[i]), prm).stable for i in run]),
        )
        for run in runs
        if inside[run[0]] and len(run) > 1
    ]


def branches(prm: Params, p_range: tuple[float, float]) -> list[Branch]:
    """Every branch of steady states with rainfall in p_range (model units)."""
    none_g, none_t = np.zeros_like(T_GRID), np.zeros_like(G_GRID)
    with np.errstate(divide="ignore", invalid="ignore"):  # off a branch, p is no rainfall
        p_grass = break_even(grass_balance, G_GRID, 0.0, prm)
        p_trees = break_even(tree_balance, 0.0, T_GRID, prm)
        found = _pieces("grass", (np.asarray(p_grass), G_GRID, none_t), prm, p_range)
        found += _pieces("trees", (np.asarray(p_trees), none_g, T_GRID), prm, p_range)
        gg, tt = np.meshgrid(G_GRID, T_GRID)
        both = [np.asarray(break_even(b, gg, tt, prm)) for b in (grass_balance, tree_balance)]
        valid = (both[0] > 0) & (both[1] > 0)
        z = np.ma.masked_array(np.log(both[0] / both[1]), mask=~valid)
        for line in contour_generator(x=G_GRID, y=T_GRID, z=z).lines(0.0):
            g, t = _polish(*np.asarray(line).T, prm)
            on_curve = (np.abs(_mismatch(g, t, prm)) < MISMATCH_TOL) & (g > 0) & (t > 0)
            p = np.where(on_curve, break_even(grass_balance, g, t, prm), np.nan)
            found += _pieces("both", (p, g, t), prm, p_range)
    bare = np.unique(np.append(np.geomspace(*p_range, BARE_POINTS), bare_soil_threshold(prm)))
    zeros = np.zeros_like(bare)
    return [*found, *_pieces("bare", (bare, zeros, zeros), prm, p_range)]
