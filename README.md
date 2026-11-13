# biome-bifurcations

A minimal model of tropical vegetation from desert to forest along rainfall, with the report and the talk built from it, "Why the same rain can grow grassland or forest" (EH-605 Modeling Earth System and Sustainability, IIT Gandhinagar, Fall 2026). Four quantities interact: surface water, soil water, grass, and trees. From a handful of physical facts, the model produces desert tipping, self-organized patterns, savannas held open by fire, the switch of tree shade from helping to hurting grass, and the jump between savanna and forest. Every figure and number in the report and the talk comes from this code.

## Model

The model follows one patch of land under yearly rain $`p`$. Its surface water $`O`$, soil water $`w`$, grass $`G`$, and trees $`T`$ change as

$$\frac{dO}{dt} = p - I O - O$$

$$\frac{dw}{dt} = (1 - \theta) I O - L w - u w (G + T)$$

$$\frac{dG}{dt} = m_g \left[ w G \left( 1 - \frac{G}{L} \right) - G \right]$$

$$\frac{dT}{dt} = m_t \left[ (w + d) L (1 - h F) T - T \right]$$

Rain soaks in at rate $`I`$, a share $`L`$ of the light reaches the ground, deep water $`d`$ (which only trees reach) sits at its balance, and fire burns a share $`F`$ of the patch.

$$I = \varepsilon + \beta (G + T), \qquad L = e^{-kT}, \qquad d = \frac{\theta I O}{1 + u T}, \qquad F = \frac{G^n}{G^n + g_c^n}$$

Time is measured in drying times of bare soil. In the pattern experiment, every equation gains a spreading term, $`D_O \nabla^2 O`$ for surface water and $`\nabla^2 X`$ for the others. Each term and constant is explained in `src/biome_bifurcations/model.py`. Grazing and browsing, zero by default, add extra losses to grass and trees.

## Usage

```bash
uv sync
uv run biome all
```

`biome all` runs three stages in order: `numbers` (every number the documents quote, in `build/numbers.json`), `figures` (`build/figures/`), and `documents` (`build/report.pdf` and `build/slides.pdf`, compiled by Typst). Stages write to `build/` (or `--build <dir>`) and log to `logs/` (or `--logs <dir>`). A stage skips its work only while the fingerprint stored in its artifact, a hash of the code, the data, and the stage's inputs, still matches, unless `--overwrite` is given. Figures need LuaLaTeX (TeX Live) with `fontspec` and `unicode-math`; documents need Typst, which fetches its packages (`cetz`, `fletcher`) into `cache/typst/` on first use. Costly simulations are kept in `cache/figures/` and rerun only when the model changes.

## Checks

```bash
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
```

Tests cover the physics (water budget, exact derivatives, analytic thresholds, shade rule), the solver against brute-force simulation, the simulator against linear theory, the data file against its recorded checksum, convergence of the rainfall scale, how features respond when each constant is halved or raised by half, and regressions of every reported number. Property tests draw their cases from a fixed seed, so every run is reproducible. Tool caches go to `cache/`.

## Layout

- `src/biome_bifurcations/model.py`: equations, parameters, exact derivatives
- `src/biome_bifurcations/steady.py`: exact steady states and their stability
- `src/biome_bifurcations/branches.py`: exact branches of steady states along rainfall
- `src/biome_bifurcations/settle.py`: the model run forward in time, to a steady state and along slowly changing rainfall
- `src/biome_bifurcations/patterns.py`: pattern test (growth of small ripples)
- `src/biome_bifurcations/simulate.py`: spatial simulation (semi-implicit spectral method)
- `src/biome_bifurcations/data.py`: field data and the tree-cover ceiling
- `src/biome_bifurcations/analysis.py`: regimes, their landmarks along rainfall, and the robustness check
- `src/biome_bifurcations/cli.py`: pipeline stages
- `src/biome_bifurcations/style.py`: shared figure style (palette, fonts, print sizes)
- `src/biome_bifurcations/figures/`: one module per figure
- `src/biome_bifurcations/parallel.py`: independent runs across all cores
- `tests/`: checks of physics, numerics, and results
- `report/`, `slides/`: the Typst report and talk
- `typst/`: the documents' shared style, the slide design (`deck.typ`), the model diagram, and the explanatory pictures
- `data/`: field data with provenance
- `assets/fonts/`: fonts used by all outputs
- `assets/palette.toml`: the locked figure palette, shared by Python and Typst

## License

The code is MIT licensed (`LICENSE`). The fonts keep the SIL Open Font License (`assets/fonts/OFL.txt`), and the data keep the terms of their source (`data/README.md`).
