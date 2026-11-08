# Data

`woody_cover_20070206.csv` is the unmodified data file of ORNL DAAC dataset 850, "Characteristics of African Savanna Biomes for Determining Woody Cover" (DOI 10.3334/ORNLDAAC/850), downloaded by the user from the NASA Earthdata portal on 2026-11-07.

- 854 field sites across African savannas, compiled from many studies.
- Columns used: `MAP` (mean annual precipitation, mm/yr) and `Woody_cover` (percent of ground under woody crowns).
- Row 1 holds column names, row 2 holds units; data start at row 3. The file is Latin-1 encoded.
- SHA-256: `d6cdc5a47202d1ba0e76af33d6f8c05c1f71391cba61a2ed143e1c00f96ba07b`. The code refuses a file with any other hash.

Known limits that shape how the data are used:

- Woody cover was measured with five methods (densiometer, summed canopy area, Bitterlich sampling, line intercept, visual estimates), which are not directly comparable.
- Rainfall values come from mixed sources (stations, regional maps, gridded products).
- The upper tree-cover ceiling rests on few sites (about 9 above the 99th percentile), and its shape depends on the quantile chosen.

The data are therefore used only to check robust qualitative facts and to set the model's rainfall scale, never to select model terms.
