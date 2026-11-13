# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""The figures. Each module draws one figure for a medium (report or slides) in the shared style.

Every number drawn comes from the model or the data.
"""

from biome_bifurcations.figures import (
    balance,
    ceiling,
    fire,
    fit,
    greening,
    growth,
    light,
    maps,
    outcomes,
    sequence,
    smooth,
    spread,
)

FIGURES = {  # in the order the story shows them
    "ceiling": ceiling.draw,
    "spread": spread.draw,
    "light": light.draw,
    "fire": fire.draw,
    "growth": growth.draw,
    "smooth": smooth.draw,
    "greening": greening.draw,
    "balance": balance.draw,
    "jump": balance.draw_jump,
    "memory": balance.draw_memory,
    "fit": fit.draw,
    "outcomes": outcomes.draw,
    "sequence": sequence.draw,
    "maps": maps.draw,
    "windows": sequence.draw_windows,
    "versus": sequence.draw_versus,
}
