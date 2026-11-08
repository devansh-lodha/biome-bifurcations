# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Shared test setup.

Hypothesis keeps its files in the project cache, and derives its examples from a fixed seed per
test, so every run checks the same cases and any failure reproduces exactly.
"""

from pathlib import Path

import pytest
from hypothesis import configuration, settings

from biome_bifurcations.analysis import rainfall_scale
from biome_bifurcations.cli import DATA
from biome_bifurcations.model import Params

configuration.set_hypothesis_home_dir(Path(__file__).parents[1] / "cache" / "hypothesis")
settings.register_profile("repo", derandomize=True, deadline=None)
settings.load_profile("repo")


@pytest.fixture(scope="session")
def scale() -> float:
    """Rainfall scale that the data set (mm/yr per model unit)."""
    return rainfall_scale(Params(), DATA)
