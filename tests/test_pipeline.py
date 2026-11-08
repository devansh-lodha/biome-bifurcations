# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Regime landmarks and the command line stages."""

import json
import logging
from dataclasses import replace
from typing import TYPE_CHECKING

import numpy as np
import pytest

from biome_bifurcations.analysis import ceiling, landmarks, scan
from biome_bifurcations.cli import RAIN, fingerprint, is_done, main, stage_landmarks, write_json
from biome_bifurcations.logs import PACKAGE, setup_logging
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

PRM = Params()
COARSE = np.array([150.0, 190.0, 300.0, 450.0, 1000.0, 1700.0])  # one rainfall per regime


@pytest.fixture
def log_dir(tmp_path: Path) -> Iterator[Path]:
    """A log directory for one test; the handlers attached for it are closed afterwards."""
    yield tmp_path / "logs"
    logger = logging.getLogger(PACKAGE)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def test_landmarks_on_a_coarse_gradient(scale: float) -> None:
    """Each regime appears where the full 10 mm scan puts it."""
    marks = landmarks(PRM, scale, scan(PRM, scale, COARSE))
    assert marks == {
        "rainfall_scale_mm_per_unit": scale,
        "vegetation_from_mm": 190.0,
        "bare_soil_greens_above_mm": pytest.approx(scale * (PRM.eps + 1.0) / PRM.eps),
        "desert_or_vegetation_mm": (190.0, 190.0),
        "patterns_mm": (190.0, 190.0),
        "fire_free_dry_savanna_mm": (300.0, 300.0),
        "shade_switch_mm": 450.0,
        "fire_onset_mm": 450.0,
        "savanna_or_forest_mm": (1000.0, 1000.0),
        "forest_only_from_mm": 1700.0,
    }


def test_desert_has_no_landmarks(scale: float) -> None:
    """With bare soil only, every regime landmark is absent."""
    marks = landmarks(PRM, scale, scan(PRM, scale, np.array([150.0]), patterns=False))
    absent = {
        k: v for k, v in marks.items() if k.endswith("_mm") and k != "bare_soil_greens_above_mm"
    }
    assert all(v is None for v in absent.values())


def test_ceiling_rises_with_rain(scale: float) -> None:
    """Without fire, the most tree cover a climate allows is zero in deserts and rises with rain."""
    cover = ceiling(PRM, np.arange(100.0, 3001.0, 100.0) / scale)
    assert cover[0] == 0.0
    assert np.all(np.diff(cover) >= 0.0)
    assert cover[-1] < 1.0


def test_stage_writes_once_then_skips(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A finished artifact is reused; new inputs or --overwrite recompute it."""
    caplog.set_level("INFO")
    out = stage_landmarks(tmp_path, rain=COARSE)
    assert json.loads(out.read_text(encoding="utf-8"))["forest_only_from_mm"] == 1700.0
    stage_landmarks(tmp_path, rain=COARSE)
    assert "skipping" in caplog.text
    caplog.clear()
    stage_landmarks(tmp_path, rain=COARSE[:-1])
    assert "rainfall scale" in caplog.text
    caplog.clear()
    stage_landmarks(tmp_path, overwrite=True, rain=COARSE[:-1])
    assert "rainfall scale" in caplog.text


def test_only_matching_artifacts_are_done(tmp_path: Path) -> None:
    """Missing, truncated, or differently made artifacts do not count as finished work."""
    path = tmp_path / "landmarks.json"
    stamp = fingerprint(PRM, COARSE)
    assert fingerprint(replace(PRM, eps=0.46), COARSE) != stamp
    assert not is_done(path, stamp)
    path.write_text('{"fingerprint": "', encoding="utf-8")
    assert not is_done(path, stamp)
    write_json(path, {"fingerprint": fingerprint(PRM, COARSE[:-1])})
    assert not is_done(path, stamp)
    write_json(path, {"fingerprint": stamp})
    assert is_done(path, stamp)


@pytest.mark.parametrize("stage", ["landmarks", "all"])
def test_main_runs_stages(
    stage: str, tmp_path: Path, log_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The command line dispatches to the named stage, or to every stage under "all"."""
    caplog.set_level("INFO")
    write_json(tmp_path / "landmarks.json", {"fingerprint": fingerprint(PRM, RAIN)})
    main([stage, "--build", str(tmp_path), "--logs", str(log_dir)])
    assert "skipping" in caplog.text
    assert (log_dir / "biome.log").exists()


def test_logging_setup_is_idempotent(log_dir: Path) -> None:
    """Setting up logging twice adds no duplicate handlers."""
    first = len(setup_logging(log_dir).handlers)
    assert len(setup_logging(log_dir).handlers) == first
