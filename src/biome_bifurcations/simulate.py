# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Spatial simulation on a periodic line or square, by a semi-implicit spectral method.

Every rate is a gain minus a per-capita loss, dy/dt = gain - loss y + D lap(y) (model.py). Each
step takes spreading implicitly and local rates explicitly. Spreading has constant rates, so it
is diagonal in Fourier space:

    (1 + dt sigma + dt D q^2) FFT(y_new) = FFT(y + dt (gain + (sigma - loss) y)).

The uniform rate sigma = max(0, max(loss) - 1/dt) moves the part of each variable's loss that an
explicit step cannot take to the implicit side; at the default dt it is zero for every variable. Two
properties hold for any dt. At a fixed point the sigma terms cancel, so steady states, and the
onset of patterns where a real eigenvalue crosses zero, are exactly those of the equations. And
since dt (loss - sigma) <= 1, the right side stays positive. Disturbances decay as they should
only for steps well below the slowest time scale, 1 / m_t; the default dt is far below it.
Accuracy is first order in dt.

FFTs run on one thread by default. Parallelize independent runs across processes, or wrap a
single large run in `scipy.fft.set_workers`.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scipy import fft

from biome_bifurcations.model import gains_losses, spreading

if TYPE_CHECKING:
    from biome_bifurcations.model import Array, Params


@dataclass(frozen=True)
class Grid:
    """Periodic domain of side `length` with n points per side, and the time step dt."""

    length: float
    n: int
    dims: int = 1  # 1: line, 2: square
    dt: float = 0.02

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of one field."""
        return (self.n,) * self.dims

    def wavenumbers_squared(self) -> Array:
        """|q|^2 on the real-FFT grid, whose last axis holds only non-negative frequencies."""
        spacing = self.length / self.n
        full = 2.0 * np.pi * fft.fftfreq(self.n, d=spacing)
        half = 2.0 * np.pi * fft.rfftfreq(self.n, d=spacing)
        mesh = np.meshgrid(*[full] * (self.dims - 1), half, indexing="ij")
        return np.sum([q * q for q in mesh], axis=0)


def run(y: Array, p: float, prm: Params, grid: Grid, t_end: float) -> Array:
    """Advance fields y, of shape (4, *grid.shape), at rainfall p for t_end / dt steps, rounded."""
    axes = tuple(range(1, y.ndim))
    per_variable = (4,) + (1,) * grid.dims
    spread = grid.dt * spreading(prm).reshape(per_variable) * grid.wavenumbers_squared()
    for _ in range(round(t_end / grid.dt)):
        gain, loss = gains_losses(y, p, prm)
        sigma = np.maximum(loss.reshape(4, -1).max(axis=1) - 1.0 / grid.dt, 0.0)
        sigma = sigma.reshape(per_variable)
        explicit = y + grid.dt * (gain + (sigma - loss) * y)
        implicit = fft.rfftn(explicit, axes=axes) / (1.0 + grid.dt * sigma + spread)
        # Transforms can round a value a hair below zero; no field can be negative.
        y = np.maximum(fft.irfftn(implicit, s=grid.shape, axes=axes), 0.0)
    return y


def seeded(uniform: Array, grid: Grid, noise: float, seed: int) -> Array:
    """Uniform fields (one value per variable) with small random grass perturbations."""
    y = np.broadcast_to(uniform.reshape((4,) + (1,) * grid.dims), (4, *grid.shape)).copy()
    rng = np.random.default_rng(seed)
    y[2] *= 1.0 + noise * rng.standard_normal(grid.shape)
    return y
