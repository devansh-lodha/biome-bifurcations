# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Logging to the console and to logs/biome.log.

Modules log through `logging.getLogger(__name__)`; their records propagate to the package logger
configured here, so only the entry point decides where output goes.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

PACKAGE = "biome_bifurcations"


def setup_logging(log_dir: Path) -> logging.Logger:
    """Send the package's log records to the console and to log_dir/biome.log.

    Calling it again adds no duplicate handlers.
    """
    logger = logging.getLogger(PACKAGE)
    if logger.handlers:
        return logger
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file = logging.FileHandler(log_dir / "biome.log", encoding="utf-8")
    for handler in (logging.StreamHandler(), file):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger
