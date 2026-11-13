# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Shared figure style: the locked palette, the document fonts, print sizes, and saving.

Every figure is drawn through this module, so all of them share one look. LuaLaTeX sets all text through matplotlib's PGF backend in the
document's own fonts (Lato for text, Lete Sans Math for math), loaded from assets/fonts so that a
build does not depend on installed fonts. Figures are drawn at their final printed size, which the
document must not scale.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.rcsetup import cycler

if TYPE_CHECKING:
    from matplotlib.figure import Figure

ASSETS = Path(__file__).resolve().parents[2] / "assets"
CM = 1.0 / 2.54  # inches per centimeter


@dataclass(frozen=True)
class Shades:
    """One meaning in three shades: wash for areas, mark for lines and points, ink for text."""

    wash: str
    mark: str
    ink: str


@dataclass(frozen=True)
class Neutrals:
    """Colors without meaning: text, labels, axes, observations, guide lines, and paper."""

    text: str
    label: str
    axis: str
    data: str
    hairline: str
    paper: str


_PALETTE = tomllib.loads((ASSETS / "palette.toml").read_text(encoding="utf-8"))
WATER, GRASS, TREES, FIRE, SOIL = (
    Shades(**_PALETTE[name]) for name in ("water", "grass", "trees", "fire", "soil")
)
NEUTRAL = Neutrals(**_PALETTE["neutral"])

# Grass on a map, from bare soil through sparse to dense grass, darkening steadily.
BARE_TO_GRASS = LinearSegmentedColormap.from_list(
    "bare-to-grass", [SOIL.wash, GRASS.mark, GRASS.ink]
)


@dataclass(frozen=True)
class Medium:
    """Where figures appear: the widths they are drawn at (cm), type and line sizes (pt)."""

    full: float
    half: float
    text: float
    small: float
    line: float
    tallest: float = float("inf")  # cm: the most height a figure may take


# A4 with 2.5 cm margins; figures stay low enough that two fit on a page with text between.
# Half-width figures sit beside a paragraph, drawn at the width they are shown.
REPORT = Medium(full=16.0, half=6.0, text=9.0, small=8.0, line=1.2, tallest=5.6)
# 16:9 slides: figures span most of the slide, with text large enough to read from the back of a
# room, and stay low enough to leave room for a two-line headline and a two-line caption.
SLIDES = Medium(full=21.0, half=13.0, text=18.0, small=16.0, line=2.4, tallest=7.6)
# The most a figure may stretch its medium's height cap, when its page has room to spare.
MOST_ROOM = 1.2


def full_size(medium: Medium, aspect: float, room: float = 1.0) -> tuple[float, float]:
    """Size (inches) of a full-width figure: height over width is aspect, up to the medium's cap.

    A figure whose page or slide has room to spare may stretch the cap by `room`, at most
    MOST_ROOM.
    """
    stretch = min(room, MOST_ROOM)
    return size(medium.full, min(aspect * medium.full, stretch * medium.tallest))


def half_size(medium: Medium, aspect: float) -> tuple[float, float]:
    """Size (inches) of a half-width figure: height over width is aspect, up to the medium's cap."""
    return size(medium.half, min(aspect * medium.half, medium.tallest))


def size(width: float, height: float) -> tuple[float, float]:
    """Figure size in inches, as matplotlib takes it, from centimeters."""
    return width * CM, height * CM


def use(medium: Medium = REPORT) -> None:
    """Draw the figures that follow in the house style for a medium."""
    fonts = (ASSETS / "fonts").as_posix() + "/"
    lato = (
        f"[Path={fonts}, Extension=.ttf, UprightFont=*-Regular, BoldFont=*-Bold, "
        "ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]"
    )
    preamble = [
        r"\usepackage{fontspec}",
        r"\usepackage{unicode-math}",
        rf"\setmainfont{{Lato}}{lato}",
        rf"\setsansfont{{Lato}}{lato}",  # matplotlib sets its text in the sans family
        rf"\setmathfont{{LeteSansMath.otf}}[Path={fonts}]",
    ]
    mpl.use("pgf")  # LuaLaTeX measures text too, so the layout fits the typeset labels
    mpl.rcParams.update(
        {
            "pgf.texsystem": "lualatex",
            "pgf.rcfonts": False,
            "pgf.preamble": "\n".join(preamble),
            "figure.facecolor": NEUTRAL.paper,
            "savefig.facecolor": NEUTRAL.paper,
            "figure.constrained_layout.use": True,
            "font.size": medium.text,
            "axes.labelsize": medium.text,
            "axes.titlesize": medium.text,
            "xtick.labelsize": medium.small,
            "ytick.labelsize": medium.small,
            "legend.fontsize": medium.small,
            "legend.frameon": False,
            "text.color": NEUTRAL.text,
            "axes.labelcolor": NEUTRAL.label,
            "axes.edgecolor": NEUTRAL.axis,
            "axes.linewidth": 0.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "axes.labelpad": 6.0,  # axis names clear of the tick labels
            # Every color is chosen for its meaning, so an unstyled line stays neutral.
            "axes.prop_cycle": cycler(color=[NEUTRAL.label]),
            "xtick.color": NEUTRAL.axis,
            "ytick.color": NEUTRAL.axis,
            "xtick.labelcolor": NEUTRAL.label,
            "ytick.labelcolor": NEUTRAL.label,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "lines.linewidth": medium.line,
            "lines.solid_capstyle": "round",
            "lines.dash_capstyle": "round",
        }
    )


def _open_corner(fig: Figure) -> None:
    """Set the axes a little apart from the plot, so the two zero labels at a corner never touch.

    The gap grows with the tick labels of the medium being drawn.
    """
    gap = 0.4 * float(mpl.rcParams["xtick.labelsize"])
    for ax in fig.get_axes():
        for side in ("left", "bottom"):
            ax.spines[side].set_position(("outward", gap))


def save(fig: Figure, path: Path) -> Path:
    """Write a figure as vector PDF at exactly the size it was drawn, then close it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _open_corner(fig)
    fig.savefig(path)
    plt.close(fig)
    return path
