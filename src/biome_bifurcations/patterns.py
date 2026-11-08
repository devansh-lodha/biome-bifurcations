# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Pattern test: does a small ripple on a uniform steady state grow?

Linearizing the spatial model around a uniform state gives, for a ripple with wavenumber q,
growth rate = largest real eigenvalue of J - q^2 D, where J is the local Jacobian and
D = diag(d_o, d_w, 1, 1) holds the spreading rates (seed spreading sets the length unit).
A stable uniform state that is unstable to some q > 0 breaks into patterns with wavelength
2 pi / q.
"""

from typing import TYPE_CHECKING

import numpy as np

from biome_bifurcations.model import jacobian, spreading
from biome_bifurcations.steady import GROWTH_TOL

if TYPE_CHECKING:
    from biome_bifurcations.model import Array, Params
    from biome_bifurcations.steady import State

WAVENUMBERS = np.geomspace(1e-3, 3.0, 300)


def dispersion(state: State, prm: Params, q: Array = WAVENUMBERS) -> Array:
    """Growth rate of a ripple of each wavenumber q on a uniform steady state."""
    jac = jacobian(state.vector, state.p, prm)
    matrices = jac[None] - (q * q)[:, None, None] * np.diag(spreading(prm))[None]
    return np.linalg.eigvals(matrices).real.max(axis=1)


def pattern_wavelength(state: State, prm: Params) -> float | None:
    """Wavelength of the fastest-growing ripple if a stable uniform state forms patterns."""
    if not state.stable:
        return None
    rates = dispersion(state, prm)
    i = int(np.argmax(rates))
    if rates[i] <= GROWTH_TOL:
        return None
    return float(2.0 * np.pi / WAVENUMBERS[i])
