# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""The locked palette: unchanged, distinct for every reader, and legible on paper."""

import hashlib
import itertools

import numpy as np
import pytest

from biome_bifurcations.style import (
    ASSETS,
    BARE_TO_GRASS,
    FIRE,
    GRASS,
    NEUTRAL,
    SOIL,
    TREES,
    WATER,
)

LOCK = "74470fae9a65816af2d0d0efcac18359f3f202a542487d3ea66420aa600c71c7"  # assets/palette.toml
MARKS = {"water": WATER.mark, "grass": GRASS.mark, "trees": TREES.mark, "fire": FIRE.mark}

# How red-blind (protan) and green-blind (deutan) readers see a color, at full severity: the
# standard linear-RGB transforms that the palette was checked with.
VISION = {
    "protan": np.array(
        [
            [0.152286, 1.052583, -0.204868],
            [0.114503, 0.786281, 0.099216],
            [-0.003882, -0.048116, 1.051998],
        ]
    ),
    "deutan": np.array(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ]
    ),
}
TO_LMS = np.array(
    [
        [0.4122214708, 0.5363325363, 0.0514459929],
        [0.2119034982, 0.6806995451, 0.1073969566],
        [0.0883024619, 0.2817188376, 0.6299787005],
    ]
)
TO_OKLAB = np.array(
    [
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660],
    ]
)


def linear(color: str) -> np.ndarray:
    """Linear RGB of a hex color."""
    srgb = np.array([int(color[i : i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def oklab(rgb: np.ndarray) -> np.ndarray:
    """Perceptual coordinates (lightness, green-red, blue-yellow) of linear RGB."""
    return TO_OKLAB @ np.cbrt(TO_LMS @ rgb)


def difference(a: str, b: str, vision: str | None = None) -> float:
    """How different two colors look (OKLab distance x 100), to full or deficient vision."""

    def seen(color: str) -> np.ndarray:
        rgb = linear(color)
        return oklab(np.clip(VISION[vision] @ rgb, 0.0, 1.0) if vision is not None else rgb)

    return 100.0 * float(np.linalg.norm(seen(a) - seen(b)))


def contrast(a: str, b: str) -> float:
    """Luminance contrast ratio of two colors, as accessibility guidelines define it."""
    luminance = sorted((float([0.2126, 0.7152, 0.0722] @ linear(c)) for c in (a, b)), reverse=True)
    return (luminance[0] + 0.05) / (luminance[1] + 0.05)


def test_palette_is_locked() -> None:
    """The author locked the palette; a change needs their approval and a new lock."""
    assert hashlib.sha256((ASSETS / "palette.toml").read_bytes()).hexdigest() == LOCK


@pytest.mark.parametrize(("a", "b"), list(itertools.combinations(MARKS, 2)))
def test_marks_are_distinct_for_every_reader(a: str, b: str) -> None:
    """Any two marks look different with full color vision and with red-green deficiency."""
    assert difference(MARKS[a], MARKS[b]) >= 15.0
    for vision in VISION:
        assert difference(MARKS[a], MARKS[b], vision) >= 8.0


def test_shades_are_legible_on_paper() -> None:
    """Marks stand out, inks read as text on paper and on their washes, and washes stay pale."""
    for role in (WATER, GRASS, TREES, FIRE, SOIL):
        assert contrast(role.mark, NEUTRAL.paper) >= 3.0
        assert contrast(role.ink, NEUTRAL.paper) >= 4.5
        assert contrast(role.ink, role.wash) >= 4.5
        assert oklab(linear(role.wash))[0] >= 0.94
    for text in (NEUTRAL.text, NEUTRAL.label):
        assert contrast(text, NEUTRAL.paper) >= 4.5


def test_grass_map_darkens_steadily() -> None:
    """On the bare-to-grass map more grass always looks darker, so density reads by eye."""
    steps = BARE_TO_GRASS(np.linspace(0.0, 1.0, 64))[:, :3]
    rgb = np.where(steps <= 0.04045, steps / 12.92, ((steps + 0.055) / 1.055) ** 2.4)
    lightness = [oklab(c)[0] for c in rgb]
    assert np.all(np.diff(lightness) < 0.0)
