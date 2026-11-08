# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Model equations: surface water O, soil water w, grass G, trees T.

Every term follows from one physical fact:

1. Rain lands on the surface. It soaks in at rate I; the rest runs off or evaporates (rate 1).
2. Plants open crusted soil, so infiltration rises with plant cover: I = eps + beta (G + T).
3. A fraction theta of soaked-in water drains below grass roots; only trees reach it.
4. Soil dries at a rate set by sunlight reaching the ground, L = exp(-k T) (Beer-Lambert law).
5. Plants grow in proportion to the water they use. Light caps how much grass there can be
   (1 - G / L); tree seedlings need light (x L).
6. Fire spreads only through connected grass fuel, F(G), and blocks a fraction h of tree
   recruitment.
7. Water spreads fast over the surface; plants spread slowly by seed (`spreading`).

    dO/dt = p - (I + 1) O
    dw/dt = (1 - theta) I O - L w - u w (G + T)
    dG/dt = m_g [w G (1 - G / L) - (1 + graze) G]
    dT/dt = m_t [(w + d) T L (1 - h F(G)) - (1 + browse) T],   d = theta I O / (1 + u T)

Units: time is measured in units of 1 / (bare-soil drying rate). Soil water is scaled so that
grass breaks even at w = 1. G and T are dimensionless biomass. Rainfall p is relative to drying,
so it acts as an aridity index; p times a scale S (mm/yr per unit) gives annual rainfall.

Derivatives are exact. Every rate function also accepts complex input (the annotations name the
real case), so f'(x) = Im f(x + i h) / h. Unlike a finite difference this subtracts nothing, so
no digits cancel and the error, of order h^2, vanishes for a tiny step h.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

type Array = NDArray[np.float64]
type Scalar = float | Array

COMPLEX_STEP = 1e-30  # far below rounding error: the h^2 truncation error vanishes in float64


@dataclass(frozen=True)
class Params:
    """Model parameters. Defaults are the representative set used in the report."""

    u: float = 6.0  # water use per unit plant biomass, relative to bare-soil drying
    eps: float = 0.45  # infiltration rate on bare, crusted soil
    beta: float = 15.0  # extra infiltration per unit plant biomass
    theta: float = 0.23  # fraction of soaked-in water draining below grass roots
    k: float = 12.0  # light extinction per unit tree biomass (Beer-Lambert)
    h: float = 0.7  # fraction of tree recruitment blocked where fire spreads
    gc: float = 0.2  # grass fuel level at which fire spread switches on
    n: float = 8.0  # sharpness of the fire threshold
    m_g: float = 0.02  # grass turnover rate (grass is 50 times slower than soil drying)
    m_t: float = 0.002  # tree turnover rate (trees are 500 times slower than soil drying)
    d_o: float = 2.0e4  # surface water spreading relative to seed spreading
    d_w: float = 1.0  # soil water spreading relative to seed spreading
    graze: float = 0.0  # extra grass loss from grazing, relative to natural loss
    browse: float = 0.0  # extra tree loss from browsing or wood harvest, relative to natural loss
    # Mechanism switches: each fact can be removed to test what it causes.
    infiltration_feedback: bool = True  # fact 2: plants open the soil
    shade_evaporation: bool = True  # fact 4: shade slows drying
    shade_light: bool = True  # fact 5: light caps grass
    seedling_light: bool = True  # fact 5: tree seedlings need light
    fire: bool = True  # fact 6: fire spreads through grass
    fixed_cover: float = 0.5  # plant cover assumed when the infiltration feedback is off


def light(t: Scalar, prm: Params) -> Scalar:
    """Fraction of sunlight reaching the ground under tree biomass t."""
    return np.exp(-prm.k * t)


def cover(t: Scalar, prm: Params) -> Scalar:
    """Tree canopy cover: the fraction of sunlight the canopy intercepts."""
    return 1.0 - light(t, prm)


def infiltration(g: Scalar, t: Scalar, prm: Params) -> Scalar:
    """Rate at which surface water soaks in; higher where plants open the soil."""
    plants = g + t if prm.infiltration_feedback else prm.fixed_cover
    return prm.eps + prm.beta * plants


def fire_spread(g: Scalar, prm: Params) -> Scalar:
    """Measure of fire spread between 0 and 1: near 0 below the fuel threshold, near 1 above."""
    if not prm.fire:
        return 0.0
    # No grass, no fire. Root polishing can step to negative grass, so clip there, by the real
    # part only, so that complex steps pass through unchanged.
    fuel = np.where(np.real(g) > 0.0, g, 0.0) ** prm.n
    return fuel / (fuel + prm.gc**prm.n)


def soaked(g: Scalar, t: Scalar, p: float, prm: Params) -> Scalar:
    """Rain that infiltrates at steady state, p I / (I + 1); the rest runs off or evaporates."""
    i = infiltration(g, t, prm)
    return p * i / (i + 1.0)


def soil_water(g: Scalar, t: Scalar, p: float, prm: Params) -> Scalar:
    """Steady topsoil water: inflow divided by losses to drying and plant uptake."""
    dry = light(t, prm) if prm.shade_evaporation else 1.0
    return (1.0 - prm.theta) * soaked(g, t, p, prm) / (dry + prm.u * (g + t))


def deep_water(g: Scalar, t: Scalar, p: float, prm: Params) -> Scalar:
    """Steady deep water: drainage below grass roots, lost to deeper drainage or tree uptake."""
    return prm.theta * soaked(g, t, p, prm) / (1.0 + prm.u * t)


def grass_balance(g: Scalar, t: Scalar, p: float, prm: Params) -> Scalar:
    """Grass per-capita growth minus loss at steady water; zero on the grass nullcline."""
    cap = light(t, prm) if prm.shade_light else 1.0
    return soil_water(g, t, p, prm) * (1.0 - g / cap) - (1.0 + prm.graze)


def tree_balance(g: Scalar, t: Scalar, p: float, prm: Params) -> Scalar:
    """Tree per-capita growth minus loss at steady water; zero on the tree nullcline."""
    water = soil_water(g, t, p, prm) + deep_water(g, t, p, prm)
    seedling = light(t, prm) if prm.seedling_light else 1.0
    recruits = 1.0 - prm.h * fire_spread(g, prm)
    return water * seedling * recruits - (1.0 + prm.browse)


def gains_losses(y: Array, p: float, prm: Params) -> tuple[Array, Array]:
    """Gains and per-capita loss rates of y = (O, w, G, T), so that dy/dt = gain - loss y.

    The split lets the simulation move part of each loss to its implicit side, which keeps
    fields positive for any time step (simulate.py).

    Args:
        y: State with the four variables along the first axis; each may be a field of any shape.
        p: Rainfall relative to bare-soil drying.
        prm: Model parameters.

    Returns:
        Gains and losses, each with the same shape as y.
    """
    o, w, g, t = y
    lit = light(t, prm)
    dry = lit if prm.shade_evaporation else 1.0
    cap = lit if prm.shade_light else 1.0
    seedling = lit if prm.seedling_light else 1.0
    i = infiltration(g, t, prm)
    deep = prm.theta * i * o / (1.0 + prm.u * t)  # the deep store is fast, so it follows inflow
    recruits = 1.0 - prm.h * fire_spread(g, prm)
    gain = np.broadcast_arrays(
        p,
        (1.0 - prm.theta) * i * o,
        prm.m_g * w * g,
        prm.m_t * (w + deep) * seedling * recruits * t,
    )
    loss = np.broadcast_arrays(
        i + 1.0,  # infiltration, plus runoff and evaporation
        dry + prm.u * (g + t),  # drying, plus uptake by plants
        prm.m_g * (w * g / cap + 1.0 + prm.graze),  # crowding under the light cap, plus death
        prm.m_t * (1.0 + prm.browse),  # death
    )
    return np.stack(gain), np.stack(loss)


def rhs(y: Array, p: float, prm: Params) -> Array:
    """Local rates of change of y = (O, w, G, T), with the same shape as y."""
    gain, loss = gains_losses(y, p, prm)
    return gain - loss * y


def jacobian(y: Array, p: float, prm: Params) -> Array:
    """Exact Jacobian of the local rates at y = (O, w, G, T).

    Column j of the probe matrix is y + i h e_j, so one vectorized call of rhs returns, in its
    imaginary part, h times every derivative with respect to y_j.
    """
    probes = y[:, None] + 1j * COMPLEX_STEP * np.eye(len(y))
    return np.imag(rhs(probes, p, prm)) / COMPLEX_STEP


def spreading(prm: Params) -> Array:
    """Spreading rates of (O, w, G, T), relative to seed spreading, which sets the length unit."""
    return np.array([prm.d_o, prm.d_w, 1.0, 1.0])


def full_state(w: float, g: float, t: float, p: float, prm: Params) -> Array:
    """Complete a steady state (w, G, T) with its surface water O = p / (I + 1)."""
    return np.array([p / (infiltration(g, t, prm) + 1.0), w, g, t], dtype=np.float64)


def evaporation_share(g: float, prm: Params) -> float:
    """Share of topsoil water lost to evaporation (not plants) on tree-free grassland."""
    return 1.0 / (1.0 + prm.u * g)


def shade_effect(g: float, p: float, prm: Params) -> float:
    """Effect of pure shade on grass growth on tree-free grassland; positive means shade helps.

    Shade lowers the light L reaching the ground. It saves soil water (less drying) and lowers
    the grass cap. The effect is -d(growth)/dL at L = 1, taken exactly by a complex step.
    Analytically, shade helps when e (1 - G) > G, where e is the evaporation share of water loss.
    """
    inflow = (1.0 - prm.theta) * float(soaked(g, 0.0, p, prm))
    lit = 1.0 + 1j * COMPLEX_STEP
    dry = lit if prm.shade_evaporation else 1.0
    cap = lit if prm.shade_light else 1.0
    growth = inflow / (dry + prm.u * g) * (1.0 - g / cap)
    return -growth.imag / COMPLEX_STEP
