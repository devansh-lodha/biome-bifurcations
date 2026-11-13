# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Running the model forward: where runs settle, and where slow sweeps of rainfall jump."""

import numpy as np
import pytest

from biome_bifurcations import settle as forward
from biome_bifurcations.analysis import grass_alone, landmarks, scan
from biome_bifurcations.model import Params, cover, grass_balance
from biome_bifurcations.settle import path, settle, sweep, up_and_down
from biome_bifurcations.steady import break_even, stable_states

PRM = Params()
FOREST = np.array([0.0, 0.0, 0.05, 0.3])  # little grass, many trees
GRASSLAND = np.array([0.0, 0.0, 0.5, 0.0])  # thick grass, no trees


@pytest.mark.parametrize("rain", [150.0, 250.0, 450.0, 1100.0, 2000.0])
def test_runs_settle_in_states_the_solver_finds(rain: float, scale: float) -> None:
    """From bare soil with seeds, a run settles in one of the exact stable states."""
    p = rain / scale
    y, settled = settle(np.zeros(4), p, PRM)
    assert settled
    exact = stable_states(p, PRM)
    assert any(abs(y[2] - s.g) < 1e-6 and abs(y[3] - s.t) < 1e-6 for s in exact)


def test_a_run_cut_short_does_not_count(monkeypatch: pytest.MonkeyPatch, scale: float) -> None:
    """A run still changing when time runs out is no steady state, and a sweep says so."""
    monkeypatch.setattr(forward, "LONGEST", 10.0)
    p = 450.0 / scale
    assert not settle(np.zeros(4), p, PRM)[1]
    assert np.isnan(sweep(np.array([p]), np.zeros(4), PRM)).all()


def test_grass_grows_from_seeds_to_its_steady_state(scale: float) -> None:
    """Run long enough, grass alone ends where its growth balances its loss."""
    p = 350.0 / scale
    g = path(np.array([0.0, 0.0, forward.SEED, 0.0]), p, PRM, np.linspace(0.0, 4000.0, 5))[2]
    assert g[0] == forward.SEED
    assert break_even(grass_balance, g[-1], 0.0, PRM) == pytest.approx(p, rel=1e-6)


def test_grass_alone_jumps_where_the_steady_states_say(scale: float) -> None:
    """Rising rain greens bare soil where seeds can just grow; falling rain loses it at the fold."""
    marks = grass_alone(PRM, scale)
    rains = np.arange(200.0, 320.0, 1.0)
    up, down = up_and_down(rains / scale, np.zeros(4), GRASSLAND, PRM, trees=False)
    greened = rains[np.argmax(up[:, 2] > 0.01)]
    held = rains[np.argmax(down[:, 2] > 0.01)]  # the driest rainfall where grass held on
    assert marks["greens_mm"] < greened <= marks["greens_mm"] + 1.0
    assert marks["fold_mm"] < held <= marks["fold_mm"] + 1.0


@pytest.mark.parametrize(
    ("window", "start", "landmark"),
    [
        ((150.0, 260.0), np.zeros(4), ("bare_soil_greens_above_mm", None)),  # bare soil greens
        ((260.0, 150.0), FOREST, ("vegetation_from_mm", None)),  # vegetation collapses
        ((1450.0, 1600.0), np.zeros(4), ("savanna_or_forest_mm", 1)),  # savanna tips to forest
        ((900.0, 760.0), FOREST, ("savanna_or_forest_mm", 0)),  # forest tips back to savanna
    ],
)
def test_sweeps_jump_where_the_steady_states_say(
    window: tuple[float, float],
    start: np.ndarray,
    landmark: tuple[str, int | None],
    scale: float,
) -> None:
    """Each jump of a slow sweep falls within a step of where the exact stable states end."""
    step = 2.0 if window[1] > window[0] else -2.0
    rains = np.arange(window[0], window[1], step)
    states = sweep(rains / scale, settle(start, rains[0] / scale, PRM)[0], PRM)
    covers = 100 * np.asarray(cover(states[:, 3], PRM))
    i = int(np.nanargmax(np.abs(np.diff(covers)))) + 1  # the step that jumps
    scan_rains = np.arange(min(window), max(window) + 1.0, 1.0)
    key, index = landmark
    mark = landmarks(PRM, scale, scan(PRM, scale, scan_rains, patterns=False))[key]
    if index is not None:
        assert isinstance(mark, tuple)
        mark = mark[index]
    assert isinstance(mark, float)
    assert abs(rains[i] - mark) <= 2.0 + 1.0  # one sweep step plus one scan step
