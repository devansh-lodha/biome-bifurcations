# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Figures and documents: print widths, the store for costly results, and the build stages."""

import shutil
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pytest

from biome_bifurcations import cli, model, style
from biome_bifurcations.figures import FIGURES, common, greening, maps, sequence

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.figure import Figure


@pytest.fixture
def quick_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Small stand-ins for the long runs, so drawing a figure needs no long simulation.

    The sweeps jump where the real ones do: grass once each way; trees at the desert edge and
    between savanna and forest, with fire-cleared grassland between. So every arrow, window, and
    label gets drawn.
    """
    rng = np.random.default_rng(0)
    monkeypatch.setattr(maps, "_maps", lambda: rng.uniform(0.0, 0.15, (len(maps.RAINS), 8, 8)))
    rains = greening.RAINS
    jumps = [np.where(rains < r, 0.0, 0.2) for r in (290.0, 226.0)]  # with the loop
    smooth = [np.clip((rains - 290.0) / 2000.0, 0.0, None)] * 2  # without it, both ways
    grass = np.array(jumps + smooth)
    monkeypatch.setattr(greening, "sweeps", lambda: grass)
    rains = sequence.RAINS
    # Tree cover (percent) at corners of each sweep; straight lines between, steep only at jumps.
    rising = (
        [50, 222, 223, 330, 360, 575, 700, 1535, 1536, 2500],
        [0, 0, 30, 45, 0, 0, 20, 60, 90, 92],
    )
    falling = (
        [50, 180, 181, 330, 360, 575, 700, 815, 816, 2500],
        [0, 0, 28, 45, 0, 0, 20, 40, 78, 92],
    )
    trees = np.array([np.interp(rains, *corners) for corners in (rising, falling)])
    monkeypatch.setattr(sequence, "sweeps", lambda: trees)


@pytest.mark.usefixtures("quick_runs")
@pytest.mark.parametrize("name", sorted(FIGURES))
def test_figure_draws_at_print_width(name: str) -> None:
    """Every figure is drawn exactly full or half the report's width."""
    style.use(style.REPORT)
    fig = FIGURES[name](style.REPORT)
    width = fig.get_size_inches()[0] / style.CM
    plt.close(fig)
    assert width == pytest.approx(style.REPORT.full) or width == pytest.approx(style.REPORT.half)


@pytest.mark.usefixtures("quick_runs")
@pytest.mark.parametrize("name", sorted(FIGURES))
def test_slide_figure_fits_its_slide(name: str) -> None:
    """Every slide figure is full or half the slide's width, and no taller than a slide allows."""
    style.use(style.SLIDES)
    fig = FIGURES[name](style.SLIDES)
    width, height = fig.get_size_inches() / style.CM
    plt.close(fig)
    assert width == pytest.approx(style.SLIDES.full) or width == pytest.approx(style.SLIDES.half)
    assert height <= style.MOST_ROOM * style.SLIDES.tallest + 1e-9


def test_costly_results_are_computed_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The store computes a result the first time and reads it back after."""
    monkeypatch.setattr(common, "STORE", tmp_path)
    calls: list[int] = []

    def compute() -> np.ndarray:
        calls.append(1)
        return np.arange(3.0)

    first = common.stored("test", ("inputs",), compute, (model,))
    again = common.stored("test", ("inputs",), compute, (model,))
    assert calls == [1]
    assert np.array_equal(first, again)


def tiny(medium: style.Medium) -> Figure:
    """A minimal figure, to exercise the stage quickly."""
    fig, ax = plt.subplots(figsize=style.size(medium.half, 2.0))
    ax.plot([0.0, 1.0], [0.0, 1.0])
    return fig


@pytest.mark.skipif(shutil.which("lualatex") is None, reason="LuaLaTeX is not installed")
def test_stage_draws_each_medium_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The figures stage writes a report and a slides version, then skips while current."""
    monkeypatch.setattr(cli, "FIGURES", {"tiny": tiny})
    caplog.set_level("INFO")
    cli.stage_figures(tmp_path)
    assert (tmp_path / "figures" / "report" / "tiny.pdf").exists()
    assert (tmp_path / "figures" / "slides" / "tiny.pdf").exists()
    cli.stage_figures(tmp_path)
    assert "up to date" in caplog.text


def test_documents_compile_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The documents stage compiles the report and the slides, then skips while current."""
    compiled: list[str] = []

    def record(source: Path, *_: Path) -> None:
        compiled.append(source.stem)

    monkeypatch.setattr(cli, "_compile", record)
    (tmp_path / "numbers.json").write_text("{}", encoding="utf-8")
    caplog.set_level("INFO")
    cli.stage_documents(tmp_path)
    cli.stage_documents(tmp_path)
    assert compiled == ["report", "slides"]
    assert "up to date" in caplog.text
