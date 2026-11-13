# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Exact branches: every point is a steady state, and every steady state lies on a branch."""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from biome_bifurcations.branches import Branch, branches
from biome_bifurcations.model import Params, grass_balance, rhs, tree_balance
from biome_bifurcations.steady import break_even, state_at, steady_states

PRM = Params()
RANGE = (1.4, 45.0)  # model rainfall, about 100 to 3100 mm/yr


@pytest.fixture(scope="module")
def found() -> list[Branch]:
    """All branches over the rainfall range."""
    return branches(PRM, RANGE)


@given(st.floats(0.0, 0.9), st.floats(0.0, 0.3))
def test_break_even_zeroes_the_balance(g: float, t: float) -> None:
    """At its break-even rainfall a plant's balance is zero, since water is linear in rain."""
    for balance in (grass_balance, tree_balance):
        p = float(break_even(balance, g, t, PRM))
        if p > 0.0:
            assert float(balance(g, t, p, PRM)) == pytest.approx(0.0, abs=1e-12)


def test_branch_points_are_steady_states(found: list[Branch]) -> None:
    """At every traced point all four rates vanish."""
    for b in found:
        for i in range(0, len(b.p), 5):
            s = state_at(float(b.g[i]), float(b.t[i]), float(b.p[i]), PRM)
            assert np.allclose(rhs(s.vector, s.p, PRM), 0.0, atol=1e-10)


@pytest.mark.parametrize("p", [2.8, 4.0, 8.0, 14.0, 20.0, 30.0])
def test_every_steady_state_lies_on_a_branch(found: list[Branch], p: float) -> None:
    """Each state the solver finds is on a traced branch, with the same stability."""
    for s in steady_states(p, PRM):
        gaps = [np.abs(np.log(b.p / p)) + np.abs(b.g - s.g) + np.abs(b.t - s.t) for b in found]
        nearest = min(range(len(found)), key=lambda k: float(gaps[k].min()))
        assert float(gaps[nearest].min()) < 0.02
        assert bool(found[nearest].stable[int(np.argmin(gaps[nearest]))]) == s.stable
