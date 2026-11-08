# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Steady states: fixed points, analytic threshold, brute-force agreement, regressions."""

from dataclasses import replace

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from scipy.integrate import solve_ivp

from biome_bifurcations.model import Params, jacobian, rhs
from biome_bifurcations.steady import (
    State,
    _polish,
    bare_soil_threshold,
    stable_states,
    steady_states,
)

PRM = Params()
switches = st.builds(
    Params,
    infiltration_feedback=st.booleans(),
    shade_evaporation=st.booleans(),
    shade_light=st.booleans(),
    seedling_light=st.booleans(),
    fire=st.booleans(),
)


@given(st.floats(0.5, 45.0), switches)
def test_steady_states_are_fixed_points(p: float, prm: Params) -> None:
    """Every state found makes all four rates vanish, whatever mechanisms are switched off."""
    for s in steady_states(p, prm):
        assert np.allclose(rhs(s.vector, p, prm), 0.0, atol=1e-9)


@given(
    st.builds(
        Params,
        eps=st.floats(0.1, 2.0),
        infiltration_feedback=st.booleans(),
        browse=st.floats(0.0, 1.0),
    )
)
def test_bare_soil_loses_stability_at_threshold(prm: Params) -> None:
    """Bare soil turns unstable at the computed threshold, whichever plant can invade first."""
    p_star = bare_soil_threshold(prm)

    def bare(p: float) -> State:
        return next(s for s in steady_states(p, prm) if s.bare)

    assert bare(0.99 * p_star).stable
    assert not bare(1.01 * p_star).stable


def test_trees_green_bare_soil_first() -> None:
    """Trees also reach deep water, so they break even on bare soil first, at (eps + 1) / eps."""
    assert bare_soil_threshold(PRM) == pytest.approx((PRM.eps + 1.0) / PRM.eps, rel=1e-12)


@pytest.mark.parametrize("p", [2.0, 5.0, 12.0, 30.0])
def test_solver_matches_brute_force(p: float) -> None:
    """Simulations from many starts settle only in stable states that the solver finds."""
    fast = replace(PRM, m_g=0.5, m_t=0.05)  # faster plants only to shorten simulations
    exact = stable_states(p, fast)
    for g0 in (1e-6, 0.05, 0.4, 0.8):
        for t0 in (1e-6, 0.05, 0.3):
            sol = solve_ivp(
                lambda _, y: rhs(y, p, fast),
                (0.0, 30000.0),
                [p, 1.0, g0, t0],
                method="LSODA",
                rtol=1e-9,
                atol=1e-12,
            )
            g, t = sol.y[2:, -1]
            assert any(abs(g - s.g) < 1e-6 and abs(t - s.t) < 1e-6 for s in exact), (g0, t0)


def test_stability_is_never_lost_to_oscillations() -> None:
    """No steady state is an unstable spiral, so no growing oscillation escapes the analysis."""
    for p in np.linspace(0.5, 45.0, 90):
        for s in steady_states(p, PRM):
            ev = np.linalg.eigvals(jacobian(s.vector, p, PRM))
            lead = ev[np.argmax(ev.real)]
            assert lead.real < 0.0 or lead.imag == 0.0, (p, s)


def test_polishing_rejects_points_that_are_not_states() -> None:
    """In a desert no grass-tree crossing exists, so polishing returns none, not a false state."""
    assert _polish(np.array([0.3, 0.1]), 1.0, PRM) is None


def test_no_states_lost_near_fire_threshold() -> None:
    """Regression: a savanna was dropped here when the solver flag reported no progress."""
    states = steady_states(17.4686, PRM)
    assert any(s.stable and 0.3 < s.g < 0.45 and 0.4 < s.cover < 0.6 for s in states)


def test_state_count_has_no_isolated_dropouts() -> None:
    """Along a fine rainfall sweep, the number of steady states never dips at a single point."""
    counts = [len(steady_states(p, PRM)) for p in np.linspace(14.0, 22.0, 161)]
    for a, b, c in zip(counts, counts[1:], counts[2:], strict=False):
        assert not (b < a and b < c)
