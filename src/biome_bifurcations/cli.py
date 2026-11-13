# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Command line entry point: `uv run biome <stage> [--overwrite]`.

Stages write their artifacts to build/. Each artifact carries a fingerprint of the package source,
the data, and the stage's inputs, and a stage skips its work only when the fingerprint still
matches, unless --overwrite is given. Artifacts are written atomically, so an interrupted run
never leaves a partial file that a later run would mistake for finished work.

Paths are relative to the repository, as in the editable install that `uv sync` makes.
"""

import argparse
import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from biome_bifurcations import style
from biome_bifurcations.analysis import (
    features,
    grass_alone,
    landmarks,
    mechanisms,
    model_ceiling_at,
    rainfall_scale,
    robustness,
    scale_range,
    scan,
)
from biome_bifurcations.data import DATA, fit_ceiling, load_sites
from biome_bifurcations.data import spread as data_spread
from biome_bifurcations.figures import FIGURES, growth, maps, outcomes, spread
from biome_bifurcations.logs import setup_logging
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from collections.abc import Sequence

    from biome_bifurcations.model import Array

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
# Rainfall grid (mm/yr) for the landmarks and features. Some features span only a few mm, which
# 10 mm steps can miss; a grid four times finer than this one finds the same features in every
# version of the model, with boundaries that move by less than 3 mm.
RAIN = np.arange(50.0, 3001.0, 1.0)
DOCUMENTS = (ROOT / "report" / "report.typ", ROOT / "slides" / "slides.typ")

log = logging.getLogger(__name__)


def fingerprint(*inputs: object) -> str:
    """Hash of the package source, the data, the palette, and a stage's inputs."""
    digest = hashlib.sha256()
    for path in [*sorted(SOURCE.rglob("*.py")), DATA, style.ASSETS / "palette.toml"]:
        digest.update(path.read_bytes())
    for item in inputs:
        digest.update(item.tobytes() if isinstance(item, np.ndarray) else repr(item).encode())
    return digest.hexdigest()


def is_done(path: Path, stamp: str) -> bool:
    """Whether a JSON artifact exists and was made with the given fingerprint."""
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return False
    return isinstance(content, dict) and bool(content.get("fingerprint") == stamp)


def write_json(path: Path, content: dict[str, object]) -> None:
    """Write JSON atomically: to a temporary file first, then rename it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(content, indent=1), encoding="utf-8")
    partial.replace(path)


def stage_numbers(build: Path, *, overwrite: bool = False, rain: Array = RAIN) -> Path:
    """Every number the report and the slides quote, from the model and the data."""
    out = build / "numbers.json"
    prm = Params()
    stamp = fingerprint(prm, rain)
    if is_done(out, stamp) and not overwrite:
        log.info("numbers are up to date, skipping (%s)", out)
        return out
    scale = rainfall_scale(prm, DATA)
    log.info("rainfall scale set by the data: %.2f mm/yr per model unit", scale)
    points = scan(prm, scale, rain)
    low, high = scale_range(prm, DATA)
    sites = load_sites(DATA)
    fit = fit_ceiling(sites)
    waves = [w for pt in points for w in pt.wavelengths.values()]
    numbers: dict[str, object] = {
        "fingerprint": stamp,
        "parameters": asdict(prm),
        "scale": {"best": scale, "low": low, "high": high},
        "landmarks": landmarks(prm, scale, points),
        "data": {
            "sites": len(sites.rain),
            "knee_mm": fit.knee,
            "plateau_percent": 100.0 * float(fit(np.array([fit.knee]))[0]),
            "spread_mm": spread.SPREAD_MM,  # where the data figure shows the spread
            "spread_percent": [
                100.0 * c for c in data_spread(sites, spread.SPREAD_MM, spread.WINDOW_MM)
            ],
            "spread_sites": int(np.sum(np.abs(sites.rain - spread.SPREAD_MM) <= spread.WINDOW_MM)),
        },
        "model_ceiling_at_knee_percent": 100.0 * model_ceiling_at(prm, scale, fit.knee),
        "grass_alone": grass_alone(prm, scale),
        "pattern_wavelength": float(np.median(waves)) if waves else None,
        "examples": {  # the settings of the example runs the figures show
            "growth_rain_mm": growth.RAIN_MM,
            "maps_rain_mm": list(maps.RAINS),
            "outcomes_rain_mm": outcomes.RAIN_MM,
            "outcomes_start_cover_percent": list(outcomes.START_COVER),
            "outcomes_end_cover_percent": [float(c[-1]) for c in outcomes.runs()[1]],
        },
        "features": features(prm, scale, rain),
        "mechanisms": [asdict(m) for m in mechanisms(prm, scale, rain)],
        "robustness": [asdict(v) for v in robustness(prm, scale, rain)],
    }
    for key, value in numbers.items():
        log.info("%-12s %s", key, value)
    write_json(out, numbers)
    return out


def stage_figures(build: Path, *, overwrite: bool = False) -> Path:
    """Every figure, drawn once for the report and once for the slides."""
    out = build / "figures.json"
    stamp = fingerprint(sorted(FIGURES))
    if is_done(out, stamp) and not overwrite:
        log.info("figures are up to date, skipping (%s)", out)
        return out
    files = []
    for name, draw in FIGURES.items():
        for medium_name, medium in (("report", style.REPORT), ("slides", style.SLIDES)):
            style.use(medium)
            path = style.save(draw(medium), build / "figures" / medium_name / f"{name}.pdf")
            log.info("drew %s", path.relative_to(build))
            files.append(path.relative_to(build).as_posix())
    write_json(out, {"fingerprint": stamp, "files": files})
    return out


def _compile(source: Path, target: Path, build: Path) -> None:
    """Compile one Typst document with the repository's fonts and a project-local package cache."""
    typst = shutil.which("typst")
    if typst is None:
        msg = "Typst is not installed"
        raise RuntimeError(msg)
    command = [
        typst,
        "compile",
        "--root",
        str(ROOT),
        "--font-path",
        str(style.ASSETS / "fonts"),
        "--ignore-system-fonts",
        "--package-cache-path",
        str(ROOT / "cache" / "typst"),
        "--input",
        f"build=/{build.resolve().relative_to(ROOT).as_posix()}",
        str(source),
        str(target),
    ]
    subprocess.run(command, check=True)  # noqa: S603 (fixed command, paths from the repository)


def stage_documents(build: Path, *, overwrite: bool = False) -> Path:
    """The report and the slides, compiled from their sources, the numbers, and the figures."""
    out = build / "documents.json"
    inputs = [*DOCUMENTS, *sorted((ROOT / "typst").glob("*.typ")), build / "numbers.json"]
    inputs += sorted((build / "figures").rglob("*.pdf"))
    stamp = fingerprint(*(hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs))
    if is_done(out, stamp) and not overwrite:
        log.info("documents are up to date, skipping (%s)", out)
        return out
    files = []
    for source in DOCUMENTS:
        target = build / f"{source.stem}.pdf"
        _compile(source, target, build)
        log.info("compiled %s", target.relative_to(build))
        files.append(target.name)
    write_json(out, {"fingerprint": stamp, "files": files})
    return out


STAGES = {"numbers": stage_numbers, "figures": stage_figures, "documents": stage_documents}


def main(argv: Sequence[str] | None = None) -> None:
    """Run the stages named on the command line."""
    parser = argparse.ArgumentParser(prog="biome", description=__doc__)
    parser.add_argument("stage", choices=[*STAGES, "all"])
    parser.add_argument("--overwrite", action="store_true", help="recompute finished artifacts")
    parser.add_argument("--build", type=Path, default=ROOT / "build", help="artifact directory")
    parser.add_argument("--logs", type=Path, default=ROOT / "logs", help="log directory")
    args = parser.parse_args(argv)
    setup_logging(args.logs)
    for name in STAGES if args.stage == "all" else [args.stage]:
        STAGES[name](args.build, overwrite=args.overwrite)
