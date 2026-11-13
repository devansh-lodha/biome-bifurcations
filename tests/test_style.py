# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Shared figure style: house settings, and exact-size output in the document fonts."""

import re
import shutil
import zlib
from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from biome_bifurcations import style

if TYPE_CHECKING:
    from pathlib import Path


def test_house_style_for_each_medium() -> None:
    """Each medium sets its own type size, and an unstyled line stays neutral."""
    for medium in (style.SLIDES, style.REPORT):
        style.use(medium)
        assert mpl.rcParams["font.size"] == medium.text
    assert mpl.rcParams["pgf.texsystem"] == "lualatex"
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == [style.NEUTRAL.label]


def expanded(pdf: bytes) -> bytes:
    """A PDF with its compressed streams appended in plain form, so names inside can be found."""
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.DOTALL)
    return pdf + b"".join(zlib.decompress(s) for s in streams if s.startswith(b"x"))


@pytest.mark.skipif(shutil.which("lualatex") is None, reason="LuaLaTeX is not installed")
def test_figures_keep_their_size_and_document_fonts(tmp_path: Path) -> None:
    """A saved figure is exactly as wide as drawn and embeds only Lato and Lete Sans Math."""
    style.use(style.REPORT)
    fig, ax = plt.subplots(figsize=style.size(style.REPORT.half, 5.0))
    ax.plot([0.0, 1.0], [0.0, 1.0], color=style.GRASS.mark)
    ax.set_xlabel(r"Grass biomass $G$")
    content = expanded(style.save(fig, tmp_path / "figure.pdf").read_bytes())
    assert set(re.findall(rb"/BaseFont\s*/[A-Z]{6}\+([\w-]+)", content)) == {
        b"Lato-Regular",
        b"LeteSansMath",
    }
    width = float(re.findall(rb"/MediaBox\s*\[\s*0 0 ([\d.]+)", content)[0])
    assert width == pytest.approx(style.REPORT.half * style.CM * 72.0, abs=0.01)
