// Small explanatory pictures, drawn in Typst so they share the documents' fonts and colors. Each
// shows one idea: a patch of land and what it holds, a store with flows in and out, drops that
// leave in proportion to their number, stability, the rain experiment, sharing between neighbors,
// loops that feed themselves, and patterns seen from the side. Names sit in pills tinted by their
// meaning.

#import "@preview/cetz:0.3.4": canvas, draw
#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node
#import "style.typ": neutral, role

// A name in a pill tinted by its meaning: the role's wash behind its ink. With no role, a white
// pill with a hairline edge, for steps that belong to no meaning.
#let pill(body, name: none, size: 9pt) = box(
  fill: if name == none { neutral("paper") } else { role(name, "wash") },
  stroke: if name == none { 0.7pt + neutral("hairline") } else { none },
  inset: (x: 0.55em, y: 0.3em),
  radius: 0.8em,
  text(size: size, fill: if name == none { neutral("text") } else { role(name, "ink") }, body),
)

// One patch of land in cross-section: rain, a puddle on the surface, the soil within reach of
// grass roots, the deep soil below it that only tree roots reach, grass, and a tree. Wide and low,
// so it fills a slide or a page width.
#let patch(unit: 1cm, size: 9pt) = canvas(length: unit, {
  import draw: *
  let water = role("water", "mark")
  let grass = role("grass", "mark")
  let trees = role("trees", "mark")
  let label(at, body, name, anchor: "center") = content(at, anchor: anchor, pill(body, name: name, size: size))
  // Ground: the soil within reach of grass roots above, the deep soil below, split at the roots.
  rect((0, 0), (20, 3), fill: role("soil", "wash"), stroke: none)
  line((0, 3), (20, 3), stroke: 1.2pt + role("soil", "mark"))
  line((0, 1.55), (20, 1.55), stroke: (paint: neutral("axis"), thickness: 0.8pt, dash: "dashed"))
  // Between the grass roots and the tree roots, where nothing else is drawn.
  content((12.75, 2.27), anchor: "center", align(center, text(size: calc.max(0.75 * size, 8pt), fill: neutral("label"))[reach of \ grass roots]))
  // Rain over the whole patch.
  for x in range(6, 200, step: 8) {
    let x = x / 10
    line((x, 6.55), (x - 0.15, 6.05), stroke: (paint: water, thickness: 1.2pt, cap: "round"))
  }
  // A puddle on the surface.
  circle((3.4, 3.0), radius: (1.7, 0.2), fill: role("water", "wash"), stroke: 1.1pt + water)
  // Grass: tufts above ground, short roots that end above the dashed line.
  for x in (8.2, 9.0, 9.8, 10.6) {
    for (dx, dy) in ((-0.32, 0.55), (-0.1, 0.8), (0.1, 0.8), (0.32, 0.55)) {
      line((x, 3.02), (x + dx, 3.02 + dy), stroke: (paint: grass, thickness: 1.7pt, cap: "round"))
    }
    for dx in (-0.2, 0, 0.2) {
      line((x, 2.98), (x + dx, 1.85), stroke: (paint: grass, thickness: 0.8pt, cap: "round"))
    }
  }
  // A tree: roots that reach the deep soil, trunk, and crown.
  for (dx, dy) in ((-1.1, 2.1), (-0.65, 0.7), (0, 0.3), (0.65, 0.7), (1.1, 2.1)) {
    line((15.4, 2.98), (15.4 + dx, dy), stroke: (paint: trees, thickness: 0.9pt, cap: "round"))
  }
  line((15.4, 3.0), (15.4, 4.55), stroke: (paint: role("trees", "ink"), thickness: 4pt, cap: "round"))
  circle((15.4, 5.05), radius: (1.75, 0.8), fill: role("trees", "wash"), stroke: 1.2pt + trees)
  // Names, each beside the thing it names.
  label((0.0, 7.15), [rain $p$], "water", anchor: "west")
  label((3.4, 3.75), [surface water $O$], "water")
  label((9.4, 4.4), [grass $G$], "grass")
  label((17.45, 5.05), [trees $T$], "trees", anchor: "west")
  label((3.4, 2.25), [soil water $w$], "water")
  label((3.4, 0.78), [deep water $d$], "water")
})

// A store: an amount that rises with what flows in and falls with what flows out.
#let store(unit: 1cm, size: 9pt) = canvas(length: unit, {
  import draw: *
  let water = role("water", "mark")
  rect((0, 0), (3.2, 1.3), fill: role("water", "wash"), stroke: none)
  line((0, 2.2), (0, 0), (3.2, 0), (3.2, 2.2), stroke: 1pt + neutral("axis"))
  line((1.1, 3.0), (1.1, 1.45), stroke: 1.8pt + water, mark: (end: ">", fill: water))
  content((1.35, 2.45), anchor: "west", text(size: size, fill: neutral("label"))[in])
  line((3.2, 0.45), (4.5, 0.45), stroke: 1.8pt + water, mark: (end: ">", fill: water))
  content((4.6, 0.45), anchor: "west", text(size: size, fill: neutral("label"))[out])
  content((1.6, 0.65), text(size: size, fill: role("water", "ink"))[amount])
})

// n drops in rows of at most ten, of which k are filled, spread evenly over the rows: each row
// starts with its share of the filled ones.
#let drops(n, k, size: 0.34cm, gap: 0.1cm) = {
  let water = role("water", "mark")
  let rows = calc.ceil(n / 10)
  let row(i) = stack(dir: ltr, spacing: gap, ..range(calc.min(10, n - 10 * i)).map(j => circle(
    radius: size / 2,
    fill: if j < k / rows { water } else { none },
    stroke: 0.9pt + water,
  )))
  box(stack(dir: ttb, spacing: gap, ..range(rows).map(row)))
}

// Rows of drops with a label before each: (label, total, filled).
#let drop-rows(size: 9pt, drop: 0.34cm, ..rows) = grid(
  columns: (auto, auto),
  column-gutter: 0.5cm,
  row-gutter: 0.4cm,
  align: (right + horizon, left + horizon),
  ..rows.pos().map(r => (text(size: size, fill: neutral("label"), r.at(0)), drops(r.at(1), r.at(2), size: drop))).flatten(),
)

// Stability: a ball in a bowl rolls back when nudged; a ball on a hill rolls away.
#let stability(unit: 1cm, size: 9pt) = canvas(length: unit, {
  import draw: *
  let edge = 1.2pt + neutral("axis")
  let ball = neutral("text")
  let says(body) = align(center, text(size: size, fill: neutral("label"), body))
  bezier((0, 1.6), (3, 1.6), (1, -0.5), (2, -0.5), stroke: edge)
  circle((1.5, 0.25), radius: 0.22, fill: ball, stroke: none)
  content((1.5, -0.85), says[*stable* \ nudged, it rolls back])
  bezier((5.6, 0), (8.6, 0), (6.6, 2.1), (7.6, 2.1), stroke: edge)
  circle((7.1, 1.8), radius: 0.22, fill: ball, stroke: none)
  content((7.1, -0.85), says[*unstable* \ nudged, it rolls away])
})

// Neighbors share water: a wetter patch sends water to each of its four neighbors, in proportion
// to the difference between them. With `alike`, every patch holds the same water, so each pair
// trades equal flows both ways and nothing changes; the caption says so, so no label is drawn.
#let neighbors(unit: 1cm, size: 9pt, alike: false) = canvas(length: unit, {
  import draw: *
  for i in range(3) {
    for j in range(3) {
      let wetter = i == 1 and j == 1 and not alike
      rect(
        (i, j),
        (i + 1, j + 1),
        fill: if wetter { role("water", "mark") } else { role("water", "wash") },
        stroke: 1.5pt + neutral("paper"),
      )
    }
  }
  let flow = role("water", "ink")
  let arrow = (stroke: 1.4pt + flow, mark: (end: ">", fill: flow))
  for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)) {
    if alike {
      // A pair of equal flows across each shared edge, one each way, side by side.
      let (sx, sy) = (0.14 * dy, 0.14 * dx)
      line((1.5 + 0.3 * dx + sx, 1.5 + 0.3 * dy + sy), (1.5 + 0.95 * dx + sx, 1.5 + 0.95 * dy + sy), ..arrow)
      line((1.5 + 0.95 * dx - sx, 1.5 + 0.95 * dy - sy), (1.5 + 0.3 * dx - sx, 1.5 + 0.3 * dy - sy), ..arrow)
    } else {
      // Out of the wetter patch, starting at its edge so each arrow sits on a pale neighbor.
      line((1.5 + 0.55 * dx, 1.5 + 0.55 * dy), (1.5 + 0.95 * dx, 1.5 + 0.95 * dy), ..arrow)
    }
  }
  if not alike {
    content((1.5, -0.45), text(size: size, fill: neutral("label"))[wetter patch, drier neighbors])
  }
})

// The rain experiment: rain raised in small steps, the land settling at each one (a point in the
// middle of each step, on the level it belongs to), then lowered the same way.
#let staircase(unit: 1cm, size: 9pt, steps: 5) = canvas(length: unit, {
  import draw: *
  let water = role("water", "mark")
  let axis = (stroke: 0.9pt + neutral("axis"), mark: (end: ">", fill: neutral("axis")))
  let (tread, riser, low) = (2.1, 0.7, 0.45)
  let top = low + steps * riser
  let right = 2 * steps * tread + tread
  line((0, 0), (0, top + 1.2), ..axis)
  line((0, 0), (right + 0.6, 0), ..axis)
  content((-0.2, top + 1.2), anchor: "north-east", text(size: size, fill: neutral("label"))[rain])
  content((right + 0.6, -0.25), anchor: "north-east", text(size: size, fill: neutral("label"))[time])
  // Up the steps, then down: rain is held at each tread while the land settles.
  let points = ()
  let settled = ()
  let (x, y) = (0.0, low)
  for k in range(2 * steps + 1) {
    points.push((x, y))
    settled.push((x + tread / 2, y))
    x += tread
    points.push((x, y))
    if k < steps { y += riser } else if k < 2 * steps { y -= riser }
  }
  line(..points, stroke: (paint: water, thickness: 2pt, join: "round", cap: "round"))
  for at in settled {
    circle(at, radius: 0.13, fill: neutral("text"), stroke: none)
  }
  // Each half named above its own steps.
  content(((steps + 0.5) * tread / 2, top + 0.85), pill([raise it 1 to 2 mm a step], name: "water", size: size))
  content((right - (steps + 0.5) * tread / 2, top + 0.85), pill([then lower it the same way], name: "water", size: size))
})

// A loop of causes that feeds itself: each item leads to the next, and the last leads back to the
// first. Items sit evenly on a circle, the first at the top, going clockwise. An item is its words,
// or (words, meaning) to tint its pill. Each item is a pill-shaped node, so the arrows meet its
// rounded outline, stopping just short of it.
#let loop(..items, color: neutral("label"), size: 9pt, radius: 1.5) = {
  let n = items.pos().len()
  let at(i) = {
    let angle = 90deg - i * 360deg / n
    (radius * calc.cos(angle), -radius * calc.sin(angle))
  }
  let item-node(i, item) = {
    let (body, name) = if type(item) == array { (item.at(0), item.at(1)) } else { (item, none) }
    node(
      at(i),
      text(size: size, fill: if name == none { neutral("text") } else { role(name, "ink") }, body),
      fill: if name == none { neutral("paper") } else { role(name, "wash") },
      stroke: if name == none { 0.7pt + neutral("hairline") } else { none },
      shape: fletcher.shapes.pill,
      inset: 0.45 * size,
      outset: 0.3 * size,
    )
  }
  diagram(
    spacing: 9mm * (size / 9pt),
    ..items.pos().enumerate().map(((i, item)) => item-node(i, item)),
    // Straight arrows, each aimed at the center of the next pill.
    ..range(n).map(i => edge(at(i), at(calc.rem(i + 1, n)), stroke: 1.3pt + color, marks: "-|>")),
  )
}

// Patterns, seen from the side: bare ground sheds rain toward a patch of grass, where it soaks in.
#let sideways(unit: 1cm, size: 9pt) = canvas(length: unit, {
  import draw: *
  let water = role("water", "mark")
  rect((0, 0), (3, 0.7), fill: role("soil", "wash"), stroke: none)
  rect((3, 0), (5.4, 0.7), fill: role("grass", "wash"), stroke: none)
  rect((5.4, 0), (8.4, 0.7), fill: role("soil", "wash"), stroke: none)
  content((1.5, 0.35), text(size: size, fill: role("soil", "ink"))[bare])
  content((4.2, 0.35), text(size: size, fill: role("grass", "ink"))[grass])
  content((6.9, 0.35), text(size: size, fill: role("soil", "ink"))[bare])
  for x in (0.6, 1.5, 2.4, 3.6, 4.8, 6.0, 6.9, 7.8) {
    line((x, 2.0), (x, 1.25), stroke: 1.1pt + water, mark: (end: ">", fill: water))
  }
  line((0.6, 0.95), (2.85, 0.95), stroke: 1.7pt + water, mark: (end: ">", fill: water))
  line((7.8, 0.95), (5.55, 0.95), stroke: 1.7pt + water, mark: (end: ">", fill: water))
  line((4.2, 1.15), (4.2, 0.72), stroke: 1.7pt + water, mark: (end: ">", fill: water))
  content((1.5, -0.45), text(size: size, fill: neutral("label"))[rain runs off])
  content((4.2, -0.45), text(size: size, fill: neutral("label"))[and soaks in here])
  content((6.9, -0.45), text(size: size, fill: neutral("label"))[rain runs off])
})
