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
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from biome_bifurcations.analysis import landmarks, rainfall_scale, scan
from biome_bifurcations.logs import setup_logging
from biome_bifurcations.model import Params

if TYPE_CHECKING:
    from collections.abc import Sequence

    from biome_bifurcations.model import Array

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
DATA = ROOT / "data" / "woody_cover_20070206.csv"
RAIN = np.arange(50.0, 3001.0, 10.0)  # rainfall grid (mm/yr) for the regime landmarks

log = logging.getLogger(__name__)


def fingerprint(*inputs: object) -> str:
    """Hash of the package source, the data, and a stage's inputs: any change alters it."""
    digest = hashlib.sha256()
    for path in [*sorted(SOURCE.glob("*.py")), DATA]:
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


def stage_landmarks(build: Path, *, overwrite: bool = False, rain: Array = RAIN) -> Path:
    """Regime landmarks of the representative model, in mm/yr of rainfall."""
    out = build / "landmarks.json"
    prm = Params()
    stamp = fingerprint(prm, rain)
    if is_done(out, stamp) and not overwrite:
        log.info("landmarks are up to date, skipping (%s)", out)
        return out
    scale = rainfall_scale(prm, DATA)
    log.info("rainfall scale set by the data: %.2f mm/yr per model unit", scale)
    marks = landmarks(prm, scale, scan(prm, scale, rain))
    for key, value in marks.items():
        log.info("%-34s %s", key, value)
    write_json(out, {"fingerprint": stamp, **marks})
    return out


STAGES = {"landmarks": stage_landmarks}


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
