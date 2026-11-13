// The shared look of the report and the slides: fonts, the locked palette, colored symbols, and
// the numbers the text quotes. Colors come only from assets/palette.toml (locked).

#let palette = toml("/assets/palette.toml")
#let role(name, shade) = rgb(palette.at(name).at(shade))
#let neutral(name) = rgb(palette.neutral.at(name))

#let text-font = "Lato"
#let math-font = "Lete Sans Math"

// State variables in their meaning's ink, as in every figure.
#let O = text(fill: role("water", "ink"), $O$)
#let w = text(fill: role("water", "ink"), $w$)
#let d = text(fill: role("water", "ink"), $d$)
#let p = text(fill: role("water", "ink"), $p$)
#let G = text(fill: role("grass", "ink"), $G$)
#let T = text(fill: role("trees", "ink"), $T$)
#let F = text(fill: role("fire", "ink"), $F$)

// Everything the text quotes comes from the model and the data (`uv run biome numbers`).
#let build = sys.inputs.at("build", default: "/build")
#let numbers = json(build + "/numbers.json")
#let marks = numbers.landmarks
#let figure-file(medium, name) = build + "/figures/" + medium + "/" + name + ".pdf"

// A rainfall in mm/yr, rounded to 10 mm: the fitted rainfall scale is no more precise than that.
#let mm(x) = str(int(calc.round(x / 10) * 10))
// A number with a fixed count of decimals.
#let fixed(x, digits) = str(calc.round(x, digits: digits))

// A small circled fact number.
#let fact(n) = box(baseline: 15%, circle(
  radius: 0.62em,
  stroke: 0.5pt + neutral("axis"),
  inset: 0pt,
  align(center + horizon, text(size: 0.68em, fill: neutral("label"), str(n))),
))
