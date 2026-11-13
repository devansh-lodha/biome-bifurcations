# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Regime landmarks and the command line stages."""

import itertools
import json
import logging
from dataclasses import replace
from typing import TYPE_CHECKING

import numpy as np
import pytest

from biome_bifurcations import cli
from biome_bifurcations.analysis import (
    Mechanism,
    ceiling,
    features,
    grass_alone,
    landmarks,
    mechanisms,
    model_ceiling_at,
    regimes,
    robustness,
    scan,
)
from biome_bifurcations.cli import fingerprint, is_done, main, stage_numbers, write_json
from biome_bifurcations.logs import PACKAGE, setup_logging
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

PRM = Params()
COARSE = np.array([150.0, 190.0, 300.0, 450.0, 1000.0, 1700.0])  # one rainfall per regime
GRADIENT = np.arange(50.0, 3001.0, 25.0)  # coarse enough to switch every fact off quickly


@pytest.fixture
def log_dir(tmp_path: Path) -> Iterator[Path]:
    """A log directory for one test; the handlers attached for it are closed afterwards."""
    yield tmp_path / "logs"
    logger = logging.getLogger(PACKAGE)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def test_landmarks_on_a_coarse_gradient(scale: float) -> None:
    """Each regime appears at the one coarse rainfall inside the range the full scan finds."""
    marks = landmarks(PRM, scale, scan(PRM, scale, COARSE))
    assert marks == {
        "rainfall_scale_mm_per_unit": scale,
        "vegetation_from_mm": 190.0,
        "bare_soil_greens_above_mm": pytest.approx(scale * (PRM.eps + 1.0) / PRM.eps),
        "desert_or_vegetation_mm": (190.0, 190.0),
        "patterns_mm": (190.0, 190.0),
        "open_woodland_mm": (300.0, 300.0),
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
    out = stage_numbers(tmp_path, rain=COARSE)
    numbers = json.loads(out.read_text(encoding="utf-8"))
    assert numbers["landmarks"]["forest_only_from_mm"] == 1700.0
    assert numbers["data"]["sites"] == 854
    stage_numbers(tmp_path, rain=COARSE)
    assert "skipping" in caplog.text
    caplog.clear()
    stage_numbers(tmp_path, rain=COARSE[:-1])
    assert "rainfall scale" in caplog.text
    caplog.clear()
    stage_numbers(tmp_path, overwrite=True, rain=COARSE[:-1])
    assert "rainfall scale" in caplog.text


def test_only_matching_artifacts_are_done(tmp_path: Path) -> None:
    """Missing, truncated, or differently made artifacts do not count as finished work."""
    path = tmp_path / "numbers.json"
    stamp = fingerprint(PRM, COARSE)
    assert fingerprint(replace(PRM, eps=0.46), COARSE) != stamp
    assert not is_done(path, stamp)
    path.write_text('{"fingerprint": "', encoding="utf-8")
    assert not is_done(path, stamp)
    write_json(path, {"fingerprint": fingerprint(PRM, COARSE[:-1])})
    assert not is_done(path, stamp)
    write_json(path, {"fingerprint": stamp})
    assert is_done(path, stamp)


@pytest.mark.parametrize(("stage", "expected"), [("numbers", ["numbers"]), ("all", None)])
def test_main_runs_stages(
    stage: str,
    expected: list[str] | None,
    tmp_path: Path,
    log_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command line dispatches to the named stage, or to every stage under "all"."""
    calls: list[str] = []

    def record(name: str) -> Callable[..., None]:
        return lambda build, *, overwrite: calls.append(name)  # noqa: ARG005

    monkeypatch.setattr(cli, "STAGES", {name: record(name) for name in cli.STAGES})
    main([stage, "--build", str(tmp_path), "--logs", str(log_dir)])
    assert calls == (expected or list(cli.STAGES))
    assert (log_dir / "biome.log").exists()


def test_logging_setup_is_idempotent(log_dir: Path) -> None:
    """Setting up logging twice adds no duplicate handlers."""
    first = len(setup_logging(log_dir).handlers)
    assert len(setup_logging(log_dir).handlers) == first


def test_regimes_run_from_desert_to_forest(scale: float) -> None:
    """Along rainfall the stable states pass through every regime in order, without gaps."""
    points = scan(PRM, scale, np.geomspace(100.0, 3000.0, 120), patterns=False)
    found = regimes(points)
    assert [r.kinds for r in found] == [
        ("bare",),
        ("bare", "grassy"),
        ("grassy",),
        ("burning",),
        ("burning", "forest"),
        ("forest",),
    ]
    assert all(a.high == b.low for a, b in itertools.pairwise(found))


@pytest.fixture(scope="module")
def switched(scale: float) -> tuple[dict[str, tuple[float, float]], dict[str, Mechanism]]:
    """The features of the full model, and what switching off each fact does to them."""
    rows = mechanisms(PRM, scale, GRADIENT)
    return features(PRM, scale, GRADIENT), {row.mechanism: row for row in rows}


def test_every_mechanism_changes_the_gradient(
    switched: tuple[dict[str, tuple[float, float]], dict[str, Mechanism]],
) -> None:
    """Switching off any one fact removes a feature or moves one by more than 50 mm."""
    full, rows = switched
    for row in rows.values():
        moved = any(
            abs(a - b) > 50.0
            for name, span in row.features.items()
            if name in full
            for a, b in zip(span, full[name], strict=True)
        )
        assert row.lost or moved, row.mechanism


def test_two_facts_mostly_move_the_sequence(
    switched: tuple[dict[str, tuple[float, float]], dict[str, Mechanism]],
) -> None:
    """Two facts move part of the sequence far, as the report says.

    Without deep water for trees, grassland reaches far wetter places; without the light that
    seedlings need, forest reaches far drier ones.
    """
    full, rows = switched
    deep = rows["only trees reach deep water"].features
    assert deep["grassland"][1] > full["grassland"][1] + 500.0
    seedlings = rows["tree seedlings need light"].features
    assert seedlings["forest"][0] < full["forest"][0] - 500.0


def test_plants_opening_the_soil_bend_the_grass_curve_back(scale: float) -> None:
    """Grass alone folds back below where bare soil greens, because plants open the soil.

    With fixed soaking, its curve rises from bare soil without turning, so there is no fold.
    """
    bent = grass_alone(PRM, scale)
    assert bent["fold_mm"] < bent["greens_mm"]
    assert bent["fold_grass"] > 0.01
    straight = grass_alone(replace(PRM, infiltration_feedback=False), scale)
    assert straight["fold_grass"] == pytest.approx(0.0, abs=1e-6)
    assert straight["fold_mm"] == pytest.approx(straight["greens_mm"])


def test_model_ceiling_at_a_rainfall_matches_the_ceiling(scale: float) -> None:
    """The ceiling read off its fine grid agrees with the ceiling computed at that rainfall."""
    rains = np.array([300.0, 750.0, 1200.0])
    direct = ceiling(PRM, rains / scale)
    read = [model_ceiling_at(PRM, scale, float(r)) for r in rains]
    assert read == pytest.approx(direct, abs=0.01)


def test_each_constant_is_halved_and_raised_by_half(scale: float) -> None:
    """Every constant is halved and raised by half, with shares kept at most 1.

    The speeds of grass and trees set how fast the land changes, not where it settles, so they
    lose nothing. Raising the fuel level grass must reach by half leaves grass too thin to carry
    fire anywhere, so savanna, which fire defines, disappears.
    """
    rows = {(row.constant, row.factor): row for row in robustness(PRM, scale, COARSE)}
    assert len(rows) == 22
    assert rows["h", 1.5].value == 1.0
    full = features(PRM, scale, COARSE)
    assert all(set(row.lost) <= set(full) for row in rows.values())
    assert not any(rows[speed, factor].lost for speed in ("m_g", "m_t") for factor in (0.5, 1.5))
    assert "savanna" in rows["gc", 1.5].lost
