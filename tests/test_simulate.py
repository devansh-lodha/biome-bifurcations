# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Spatial model: linear theory against simulation, exact fixed points, stability for any step."""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from biome_bifurcations.model import Params, jacobian, spreading
from biome_bifurcations.patterns import WAVENUMBERS, dispersion, pattern_wavelength
from biome_bifurcations.simulate import Grid, run, seeded
from biome_bifurcations.steady import State, stable_states

PRM = Params()
PATTERNS, SAVANNA, DESERT = 2.776, 13.54, 2.0  # rainfall (model units) in three regimes


def densest(p: float) -> State:
    """The stable state with the most grass at rainfall p."""
    return max(stable_states(p, PRM), key=lambda s: s.g)


def test_ripple_growth_matches_linear_theory() -> None:
    """A small ripple on a pattern-forming state grows at the rate the dispersion relation gives."""
    s = densest(PATTERNS)
    rates = dispersion(s, PRM)
    q = WAVENUMBERS[int(np.argmax(rates))]
    ev, vec = np.linalg.eig(jacobian(s.vector, s.p, PRM) - q * q * np.diag(spreading(PRM)))
    k = int(np.argmax(ev.real))
    grid = Grid(length=2.0 * np.pi / q, n=16)
    x = np.arange(grid.n) * grid.length / grid.n
    y0 = s.vector[:, None] + 1e-7 * vec[:, k].real[:, None] * np.cos(q * x)[None]
    t_end = 200.0
    y = run(y0, s.p, PRM, grid, t_end)
    growth = np.log(np.abs(np.fft.rfft(y[2])[1]) / np.abs(np.fft.rfft(y0[2])[1])) / t_end
    assert growth == pytest.approx(ev[k].real, rel=1e-4)


@given(st.floats(0.01, 5.0))
def test_uniform_steady_state_is_kept_for_any_step(dt: float) -> None:
    """Fixed points of the scheme are exactly the steady states, whatever the time step."""
    s = densest(SAVANNA)
    grid = Grid(length=100.0, n=8, dims=2, dt=dt)
    y0 = seeded(s.vector, grid, noise=0.0, seed=0)
    y = run(y0, s.p, PRM, grid, 20 * dt)
    assert y == pytest.approx(y0, rel=1e-12)


@given(st.floats(0.01, 5.0), st.integers(0, 2**32 - 1), st.floats(1.0, 40.0))
def test_surface_water_stays_bounded_for_any_step(dt: float, seed: int, p: float) -> None:
    """Surface water never exceeds its start or rain over the least loss rate, for any dt."""
    grid = Grid(length=500.0, n=32, dt=dt)
    y0 = np.random.default_rng(seed).uniform(0.0, 1.0, (4, grid.n)) * [[3.0 * p], [5.0], [1], [1]]
    y = run(y0, p, PRM, grid, 30 * dt)
    bound = max(y0[0].max(), p / (PRM.eps + 1.0))
    assert np.all(np.isfinite(y))
    assert y[0].max() <= bound * (1.0 + 1e-12)


def test_wavenumbers_on_real_fft_grid() -> None:
    """The last axis holds only non-negative frequencies; |q|^2 sums over axes."""
    q2 = Grid(length=2.0 * np.pi, n=8, dims=2).wavenumbers_squared()
    assert q2.shape == (8, 5)
    assert q2[3, 4] == pytest.approx(3**2 + 4**2)
    assert q2[5, 2] == pytest.approx(3**2 + 2**2)


def test_patterns_only_in_dry_grass() -> None:
    """Uniform grass breaks into bands near the desert edge (about 221 seed lengths), not later."""
    assert pattern_wavelength(densest(PATTERNS), PRM) == pytest.approx(221.1, abs=0.1)
    assert pattern_wavelength(densest(SAVANNA), PRM) is None
    bare = next(s for s in stable_states(DESERT, PRM) if s.bare)
    assert pattern_wavelength(bare, PRM) is None
