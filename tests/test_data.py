# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Field data: loading, the quantile ceiling, its bootstrap band, and the rainfall scale."""

from typing import TYPE_CHECKING

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from biome_bifurcations.analysis import CEILING_GRID, ceiling
from biome_bifurcations.cli import DATA
from biome_bifurcations.data import (
    Sites,
    ceiling_band,
    fit_ceiling,
    fit_rainfall_scale,
    load_sites,
    pinball,
)
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def sites() -> Sites:
    """All field sites."""
    return load_sites(DATA)


def test_sites_load_and_ceiling_levels_off(sites: Sites) -> None:
    """All 854 sites load; the 99th percentile of cover levels off at 0.7 to 0.9."""
    assert sites.rain.shape == sites.woody.shape == (854,)
    fit = fit_ceiling(sites)
    assert 600.0 <= fit.knee <= 1000.0
    assert 0.7 <= fit(np.array([2000.0]))[0] <= 0.9


def test_altered_data_file_is_refused(tmp_path: Path) -> None:
    """A data file that differs from the original in a single bit is not loaded."""
    raw = bytearray(DATA.read_bytes())
    raw[-1] ^= 1
    altered = tmp_path / DATA.name
    altered.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="differs"):
        load_sites(altered)


def test_ceiling_band_is_reproducible(sites: Sites) -> None:
    """The same seed gives the same band; another seed gives another."""
    grid = np.linspace(100.0, 2500.0, 25)
    low, _, fits = ceiling_band(sites, grid, n_boot=4, seed=7)
    again, _, _ = ceiling_band(sites, grid, n_boot=4, seed=7)
    other, _, _ = ceiling_band(sites, grid, n_boot=4, seed=8)
    assert len(fits) == 4
    assert np.array_equal(low, again)
    assert not np.array_equal(low, other)


def test_rainfall_scale_is_unchanged(scale: float) -> None:
    """Regression: the one number the data set."""
    assert scale == pytest.approx(69.20824479756725, rel=1e-4)


def test_rainfall_scale_converges(scale: float, sites: Sites) -> None:
    """A model ceiling twice as finely resolved moves the scale by less than 0.2 percent."""
    fine = np.geomspace(CEILING_GRID[0], CEILING_GRID[-1], 2 * len(CEILING_GRID))
    refit = fit_rainfall_scale(fine, ceiling(Params(), fine), sites)
    assert refit == pytest.approx(scale, rel=2e-3)


@given(
    st.lists(st.floats(-10.0, 10.0), min_size=1, max_size=50),
    st.floats(0.01, 0.99),
    st.floats(-20.0, 20.0),
)
def test_pinball_is_least_at_the_quantile(values: list[float], q: float, c: float) -> None:
    """The q-th quantile minimizes the mean pinball loss."""
    x = np.array(values)
    best = np.quantile(x, q, method="inverted_cdf")
    assert pinball(x - best, q) <= pinball(x - c, q) + 1e-12
