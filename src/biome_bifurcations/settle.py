# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""The model at one place, run forward in time: until it settles, or along changing rainfall.

There is no formula for where the model ends up, so SciPy's solve_ivp solves the equations from a
starting state for as long as it takes. Its BDF method is implicit and uses the exact Jacobian,
because water changes hundreds of times faster than trees.

A run comes to rest when every quantity changes by less than a tiny fraction of itself per unit
time. Rest alone does not prove a steady state: a run can idle beside a state that a plant, still
present only as a trace, will take over. So a run counts as settled only where it rests and is
stable, which the eigenvalues of the Jacobian decide. Seeds keep arriving: before each run, and
whenever a run rests where it is not stable, each plant is topped up to a trace of SEED, so a
plant returns wherever it can grow from rare.

A sweep changes rainfall in small steps, slowly enough that the model settles at each one, and
starts each run where the last one ended.
"""

from typing import TYPE_CHECKING

import numpy as np
from scipy.integrate import solve_ivp

from biome_bifurcations.model import jacobian, rhs
from biome_bifurcations.parallel import parallel_map

if TYPE_CHECKING:
    from biome_bifurcations.model import Array, Params

SEED = 1e-4  # biomass that arriving seeds keep up: enough to grow wherever a plant can
RESTING = 1e-9  # at rest: no quantity changes faster than this, relative to itself
LONGEST = 1e6  # longest run, in model time: thousands of times the slowest change, 1 / m_t
FLOOR = 1e-3  # changes of quantities below this are measured relative to it instead
TOLERANCE = (1e-11, 1e-11, 1e-16, 1e-16)  # absolute error allowed in O, w, G, T: tight for
# the plants, so that a trace of a plant never flips sign and grows as a negative amount
RESEEDS = 10  # most times seeds are added to one run before it counts as unsettled


def _change(y: Array, p: float, prm: Params) -> float:
    """Largest rate of change of any quantity, relative to the quantity (or FLOOR)."""
    return float((np.abs(rhs(y, p, prm)) / np.maximum(np.abs(y), FLOOR)).max())


class _Rests:
    """Solver event: crosses zero where the run comes to rest, which stops it."""

    terminal = True

    def __init__(self, p: float, prm: Params) -> None:
        self.p, self.prm = p, prm

    def __call__(self, _: float, y: Array) -> float:
        """Largest relative rate of change, minus the threshold of rest."""
        return _change(y, self.p, self.prm) - RESTING


def _solve(
    y: Array, p: float, prm: Params, until: float, times: Array | None = None
) -> tuple[Array, float, bool]:
    """Run from y at rainfall p: to `until`, reporting `times` if given, else stopping at rest.

    Returns:
        The states (one column per reported time), the time the run ended, and whether it
        stopped because it came to rest.
    """
    sol = solve_ivp(
        lambda _, x: rhs(x, p, prm),
        (0.0, until),
        y,
        method="BDF",
        jac=lambda _, x: jacobian(x, p, prm),
        t_eval=times,
        events=None if times is not None else _Rests(p, prm),
        rtol=1e-8,
        atol=TOLERANCE,
    )
    return sol.y, float(sol.t[-1]), sol.status == 1  # status 1: a stopping event fired


def _seeded(y: Array, *, trees: bool) -> Array:
    """The state with each plant topped up to a trace of seeds; trees only if they may grow."""
    y = np.maximum(y, 0.0)  # tolerances can leave a hair below zero; no amount is
    y[2] = max(y[2], SEED)
    if trees:
        y[3] = max(y[3], SEED)
    return y


def stable(y: Array, p: float, prm: Params, *, trees: bool = True) -> bool:
    """Whether every small disturbance of a state dies away.

    Without trees, only water and grass can respond, so trees, kept out, are left out of the test.
    """
    jac = jacobian(y, p, prm)
    if not trees:
        jac = jac[:3, :3]
    return bool(np.linalg.eigvals(jac).real.max() < 0.0)


def settle(y: Array, p: float, prm: Params, *, trees: bool = True) -> tuple[Array, bool]:
    """Where a run from the state y at rainfall p (model units) ends, and whether it settled.

    Args:
        y: Starting state (O, w, G, T).
        p: Rainfall in model units.
        prm: Model parameters.
        trees: Whether tree seeds arrive too; without them, trees stay absent.

    Returns:
        The state where the run ended, and whether it is a stable steady state. A run that has
        not settled within LONGEST is still changing: near a threshold, a plant that can just
        grow from rare takes over very slowly.
    """
    y = np.asarray(y, dtype=np.float64)
    elapsed = 0.0
    for _ in range(RESEEDS):
        states, ended, rested = _solve(_seeded(y, trees=trees), p, prm, LONGEST - elapsed)
        y, elapsed = np.maximum(states[:, -1], 0.0), elapsed + ended
        if not (rested or _change(y, p, prm) <= RESTING):
            return y, False  # time ran out while it was still changing
        if stable(y, p, prm, trees=trees):
            return y, True
        if elapsed >= LONGEST:
            break
    return y, False


def path(y: Array, p: float, prm: Params, times: Array) -> Array:
    """The state (rows O, w, G, T) at each of the given times, starting from y at time zero."""
    return _solve(np.asarray(y, dtype=np.float64), p, prm, float(times[-1]), times)[0]


def sweep(rains: Array, start: Array, prm: Params, *, trees: bool = True) -> Array:
    """Steady states along slowly changing rainfall, one row (O, w, G, T) per rainfall.

    Args:
        rains: Rainfall values in model units, in the order they are visited.
        start: The state before the first rainfall.
        prm: Model parameters.
        trees: Whether tree seeds arrive too; without them, trees stay absent.

    Returns:
        Where the model settles at each rainfall, starting from where the last run ended. A row
        is NaN where the run had not settled, so that it is never mistaken for a steady state.
    """
    y = np.asarray(start, dtype=np.float64)
    rows = []
    for p in rains:
        y, settled = settle(y, float(p), prm, trees=trees)
        rows.append(y if settled else np.full(4, np.nan))
    return np.array(rows)


def _sweep_job(job: tuple[Array, Array, Params, bool]) -> Array:
    """One sweep, as a single picklable task for a worker process."""
    rains, start, prm, trees = job
    return sweep(rains, start, prm, trees=trees)


def up_and_down(
    rains: Array, low: Array, high: Array, prm: Params, *, trees: bool = True
) -> tuple[Array, Array]:
    """Steady states while rainfall rises over `rains` from `low`, and falls back from `high`.

    The two sweeps are independent, so they run in parallel. Both are returned in the order of
    `rains`, so that row i of each holds the state at rains[i].
    """
    jobs = [(rains, low, prm, trees), (rains[::-1], high, prm, trees)]
    up, down = parallel_map(_sweep_job, jobs)
    return up, down[::-1]
