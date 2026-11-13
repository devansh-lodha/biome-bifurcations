# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""A minimal water-grass-tree-fire model of tropical biomes from desert to forest along rainfall.

Importing the package keeps the caches of the tools it drives inside the project: matplotlib
reads MPLCONFIGDIR when it is first imported, and LuaLaTeX reads TEXMFVAR and TEXMFCACHE when it
runs.
"""

import os
from pathlib import Path

_CACHE = Path(__file__).resolve().parents[2] / "cache"
for _variable, _folder in (
    ("MPLCONFIGDIR", "matplotlib"),
    ("TEXMFVAR", "texmf-var"),
    ("TEXMFCACHE", "texmf-var"),
):
    os.environ.setdefault(_variable, str(_CACHE / _folder))
