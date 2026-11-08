# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""The equations: water budget, sign structure, exact derivatives, shade rule, switches."""

from dataclasses import replace

import numpy as np
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from biome_bifurcations.model import (
    Params,
    deep_water,
    evaporation_share,
    fire_spread,
    full_state,
    gains_losses,
    infiltration,
    jacobian,
    light,
    rhs,
    shade_effect,
    soil_water,
    tree_balance,
)

PRM = Params()
grass = st.floats(0.0, 0.99)
trees = st.floats(0.0, 3.0)
rain = st.floats(0.1, 50.0)


@given(grass, trees, rain)
def test_water_budget_closes(g: float, t: float, p: float) -> None:
    """At steady water, rain = runoff + drying + plant uptake + deep uptake and drainage."""
    o, w, _, _ = full_state(float(soil_water(g, t, p, PRM)), g, t, p, PRM)
    d = deep_water(g, t, p, PRM)
    out = o + light(t, PRM) * w + PRM.u * w * (g + t) + d * (1.0 + PRM.u * t)
    assert out == pytest.approx(p, rel=1e-12)
    assert np.allclose(rhs(np.array([o, w, g, t]), p, PRM)[:2], 0.0, atol=1e-12 * p)


@given(st.lists(st.floats(0.0, 10.0), min_size=4, max_size=4), rain)
def test_gains_and_losses_are_non_negative(y: list[float], p: float) -> None:
    """Every gain and per-capita loss is non-negative, so the simulation keeps fields positive."""
    gain, loss = gains_losses(np.array(y), p, PRM)
    assert np.all(gain >= 0.0)
    assert np.all(loss >= 0.0)


def test_jacobian_is_exact() -> None:
    """The surface-water row, known in closed form, comes out exact to rounding."""
    g, t, p = 0.3, 0.1, 5.0
    y = full_state(float(soil_water(g, t, p, PRM)), g, t, p, PRM)
    row = [-(infiltration(g, t, PRM) + 1.0), 0.0, -PRM.beta * y[0], -PRM.beta * y[0]]
    assert jacobian(y, p, PRM)[0] == pytest.approx(row, rel=1e-15, abs=1e-15)


@given(grass, trees, rain, st.floats(0.0, 5.0))
def test_jacobian_matches_finite_differences(g: float, t: float, p: float, o: float) -> None:
    """Exact derivatives agree with central differences to the accuracy of the latter."""
    y = np.array([o, float(soil_water(g, t, p, PRM)), g, t])
    exact = jacobian(y, p, PRM)
    step = 1e-6
    for j in range(4):
        up, down = y.copy(), y.copy()
        up[j] += step
        down[j] -= step
        approx = (rhs(up, p, PRM) - rhs(down, p, PRM)) / (2.0 * step)
        assert approx == pytest.approx(exact[:, j], rel=1e-5, abs=1e-6)


@given(st.floats(1e-3, 0.99), rain)
def test_shade_rule(g: float, p: float) -> None:
    """Shade helps tree-free grass exactly when e (1 - G) > G, e being the evaporation share."""
    margin = evaporation_share(g, PRM) * (1.0 - g) - g
    assume(abs(margin) > 1e-9)
    assert (shade_effect(g, p, PRM) > 0.0) == (margin > 0.0)


def test_shade_acts_only_through_drying_and_light() -> None:
    """Without the light cap shade only saves water; without saved water it only costs light."""
    g, p = 0.4, 5.0
    assert shade_effect(g, p, replace(PRM, shade_light=False)) > 0.0
    assert shade_effect(g, p, replace(PRM, shade_evaporation=False)) < 0.0
    off = replace(PRM, shade_light=False, shade_evaporation=False)
    assert shade_effect(g, p, off) == 0.0


def test_switches_remove_mechanisms() -> None:
    """Switched-off mechanisms leave infiltration fixed, fire absent, and seedlings unshaded."""
    g = np.array([0.0, 0.5, 0.9])
    fixed = infiltration(g, 0.2, replace(PRM, infiltration_feedback=False))
    assert np.all(fixed == PRM.eps + PRM.beta * PRM.fixed_cover)
    assert np.all(fire_spread(g, replace(PRM, fire=False)) == 0.0)
    assert fire_spread(0.9, PRM) > 0.99
    assert fire_spread(0.1, PRM) < 0.01
    unshaded = replace(PRM, seedling_light=False, fire=False)
    water = soil_water(0.3, 0.2, 5.0, unshaded) + deep_water(0.3, 0.2, 5.0, unshaded)
    assert tree_balance(0.3, 0.2, 5.0, unshaded) == pytest.approx(water - 1.0)
