# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Field data: 854 African savanna sites (ORNL DAAC dataset 850), and the tree-cover ceiling.

The ceiling is the high quantile of tree cover as a function of rainfall, fitted as a line that
rises and then levels off at a knee ("segmented quantile regression"). For a fixed knee this is a
linear program; the knee is chosen on a grid. Bootstrap resampling of sites gives its
uncertainty.
"""

import csv
import hashlib
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from biome_bifurcations.parallel import parallel_map

if TYPE_CHECKING:
    from collections.abc import Callable

    from biome_bifurcations.model import Array

DATA = Path(__file__).resolve().parents[2] / "data" / "woody_cover_20070206.csv"

KNEES = np.arange(150.0, 1101.0, 25.0)  # candidate knees (mm/yr) of the ceiling
QUANTILE = 0.99  # the ceiling is this quantile of tree cover
SCALE_STEP = 1e-3  # step of the search for the rainfall scale, in log S
SHA256 = "d6cdc5a47202d1ba0e76af33d6f8c05c1f71391cba61a2ed143e1c00f96ba07b"  # data file


@dataclass(frozen=True)
class Sites:
    """Field sites: mean annual rainfall (mm/yr) and woody cover (fraction of ground)."""

    rain: Array
    woody: Array

    def resample(self, rng: np.random.Generator) -> Sites:
        """Bootstrap sample: as many sites as there are, drawn with replacement."""
        i = rng.integers(0, len(self.rain), len(self.rain))
        return Sites(self.rain[i], self.woody[i])


@dataclass(frozen=True)
class CeilingFit:
    """Tree-cover ceiling that rises linearly with rainfall up to a knee, then stays level."""

    knee: float  # rainfall (mm/yr) where the ceiling levels off
    intercept: float  # cover fraction
    slope: float  # cover fraction per mm/yr below the knee
    loss: float  # mean pinball loss

    def __call__(self, rain: Array) -> Array:
        """Ceiling cover at each rainfall (mm/yr)."""
        return np.clip(self.intercept + self.slope * np.minimum(rain, self.knee), 0.0, 1.0)


def load_sites(path: Path) -> Sites:
    """Mean annual rainfall and woody cover of all sites, from the unmodified data file.

    Raises:
        ValueError: If the file differs from the original recorded in data/README.md.
    """
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        msg = f"{path} differs from the original data file (see data/README.md)"
        raise ValueError(msg)
    with path.open(encoding="latin-1", newline="") as f:
        rows = list(csv.DictReader(f))[1:]  # the first data row holds units
    rain = np.array([float(r["MAP"]) for r in rows])
    woody = np.array([float(r["Woody_cover"]) for r in rows]) / 100.0
    return Sites(rain, woody)


def spread(sites: Sites, rain_mm: float, half_width: float = 25.0) -> tuple[float, float]:
    """Least and most tree cover (fractions) among sites within half_width mm/yr of a rainfall."""
    near = np.abs(sites.rain - rain_mm) <= half_width
    return float(sites.woody[near].min()), float(sites.woody[near].max())


def pinball(residual: Array, q: float) -> float:
    """Mean quantile (pinball) loss; minimized by the q-th quantile."""
    return float(np.mean(np.maximum(q * residual, (q - 1.0) * residual)))


def _fit_at(sites: Sites, knee: float, q: float) -> CeilingFit:
    """Exact quantile fit for a fixed knee, as a linear program.

    Unknowns: intercept, slope, and each site's positive and negative residual parts. The
    constraints are mostly identity blocks, so they are stored sparse.
    """
    x, n = np.minimum(sites.rain, knee), len(sites.woody)
    cost = np.concatenate([[0.0, 0.0], q * np.ones(n), (1.0 - q) * np.ones(n)])
    identity = sparse.eye_array(n)
    a_eq = sparse.hstack([np.ones((n, 1)), x[:, None], identity, -identity], format="csc")
    bounds = [(None, None), (None, None)] + [(0.0, None)] * (2 * n)
    res = linprog(cost, A_eq=a_eq, b_eq=sites.woody, bounds=bounds, method="highs")
    return CeilingFit(knee, float(res.x[0]), float(res.x[1]), float(res.fun) / n)


def fit_ceiling(sites: Sites, q: float = QUANTILE, knees: Array = KNEES) -> CeilingFit:
    """Best rise-then-level ceiling at quantile q over a grid of knees."""
    return min((_fit_at(sites, float(b), q) for b in knees), key=lambda f: f.loss)


def ceiling_band(
    sites: Sites, grid: Array, *, q: float = QUANTILE, n_boot: int = 300, seed: int = 0
) -> tuple[Array, Array, list[CeilingFit]]:
    """5th and 95th percentile of the bootstrapped ceiling on a rainfall grid, plus the fits."""
    rng = np.random.default_rng(seed)
    samples = [sites.resample(rng) for _ in range(n_boot)]  # drawn in order, so seeded
    fits = parallel_map(partial(fit_ceiling, q=q), samples)
    curves = np.array([f(grid) for f in fits])
    return np.percentile(curves, 5, axis=0), np.percentile(curves, 95, axis=0), fits


def _scale_loss(
    p_grid: Array, model_ceiling: Array, sites: Sites, q: float
) -> Callable[[float], float]:
    """Pinball loss of the sites under the model ceiling, as a function of log S."""
    log_p, log_rain = np.log(p_grid), np.log(sites.rain)

    def loss(log_s: float) -> float:
        c = np.interp(log_rain - log_s, log_p, model_ceiling, left=0.0, right=model_ceiling[-1])
        return pinball(sites.woody - c, q)

    return loss


def fit_rainfall_scale(
    p_grid: Array, model_ceiling: Array, sites: Sites, q: float = QUANTILE
) -> float:
    """Rainfall scale S (mm/yr per model unit) that best places the data under the model ceiling.

    The model ceiling is interpolated in log rainfall. The loss is flat near its minimum and has
    many kinks, so S is found by search rather than by a local optimizer: over every S from 1 to
    20000 in steps of 0.1 percent, then in steps of 0.001 percent around the best.
    """
    loss = _scale_loss(p_grid, model_ceiling, sites, q)
    coarse = np.arange(0.0, np.log(20000.0), SCALE_STEP)
    best = coarse[int(np.argmin([loss(s) for s in coarse]))]
    fine = np.linspace(best - SCALE_STEP, best + SCALE_STEP, 201)
    return float(np.exp(fine[int(np.argmin([loss(s) for s in fine]))]))


def rainfall_scale_range(
    p_grid: Array, model_ceiling: Array, sites: Sites, q: float = QUANTILE, within: float = 0.01
) -> tuple[float, float]:
    """The scales whose loss is within a fraction of the best: how tightly the data fix S."""
    loss = _scale_loss(p_grid, model_ceiling, sites, q)
    best = np.log(fit_rainfall_scale(p_grid, model_ceiling, sites, q))
    near = np.arange(best - 0.3, best + 0.3, SCALE_STEP)  # 26 percent below to 35 above
    kept = near[np.array([loss(s) for s in near]) <= (1.0 + within) * loss(best)]
    return float(np.exp(kept.min())), float(np.exp(kept.max()))
