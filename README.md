# biome-bifurcations

A minimal model of tropical vegetation from desert to forest along rainfall. Four quantities interact: surface water, soil water, grass, and trees. From a handful of physical facts, the model produces desert tipping, self-organized patterns, savannas, fire, the switch of tree shade from helping to hurting grass, and the jump between savanna and forest.

## Model

```
dO/dt = p - (I + 1) O                                      surface water
dw/dt = (1 - theta) I O - L w - u w (G + T)                topsoil water
dG/dt = m_g [w G (1 - G / L) - (1 + graze) G]              grass
dT/dt = m_t [(w + d) T L (1 - h F(G)) - (1 + browse) T]    trees
d = theta I O / (1 + u T)                                  deep water, trees only
I = eps + beta (G + T),  L = exp(-k T),  F = G^n / (G^n + gc^n)
```

Each term and parameter is explained in `src/biome_bifurcations/model.py`. Grazing and browsing are zero by default.

## Usage

```bash
uv sync
uv run biome landmarks
```

`biome` stages write to `build/` (or `--build <dir>`) and log to `logs/` (or `--logs <dir>`). A stage skips its work only while the fingerprint stored in its artifact, a hash of the code, the data, and the stage's inputs, still matches, unless `--overwrite` is given.

## Checks

```bash
uv run ruff format --check
uv run ruff check
uv run ty check
uv run pytest
```

Tests cover the physics (water budget, exact derivatives, analytic thresholds, shade rule), the solver against brute-force simulation, the simulator against linear theory, the data file against its recorded checksum, convergence of the rainfall scale, and regressions of every reported number. Property tests draw their cases from a fixed seed, so every run is reproducible. Tool caches go to `cache/`.

## Layout

- `src/biome_bifurcations/model.py`: equations, parameters, exact derivatives
- `src/biome_bifurcations/steady.py`: exact steady states and their stability
- `src/biome_bifurcations/patterns.py`: pattern test (growth of small ripples)
- `src/biome_bifurcations/simulate.py`: spatial simulation (semi-implicit spectral method)
- `src/biome_bifurcations/data.py`: field data and the tree-cover ceiling
- `src/biome_bifurcations/analysis.py`: regimes and their landmarks along rainfall
- `src/biome_bifurcations/cli.py`: pipeline stages
- `tests/`: checks of physics, numerics, and results
- `data/`: field data with provenance
- `assets/fonts/`: fonts used by all outputs

## License

The code is MIT licensed (`LICENSE`). The fonts keep the SIL Open Font License (`assets/fonts/OFL.txt`), and the data keep the terms of their source (`data/README.md`).
