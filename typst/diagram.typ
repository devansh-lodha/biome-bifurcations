// The model as a picture, built one step at a time: (1) water, (2) grass, (3) the soaking loop,
// (4) trees, (5) fire. Water flows from rain down to the plants; trees and grass act on each other
// through shade and fire. Every step keeps the full layout, with the parts still to come hidden,
// so that the picture grows in place from one step to the next.

#import "@preview/fletcher:0.5.8" as fletcher: diagram, edge, node
#import "style.typ": neutral, role

#let model-diagram(size: 9pt, step: 5, tall: 1.0, wide: 1.0) = {
  set text(size: size, fill: neutral("label"))
  // Each store is a pill tinted by its meaning, like the names in the other pictures, its name a
  // size larger than the labels on the arrows.
  let store(pos, label, name, shown: true) = node(
    pos,
    text(size: 1.2 * size, fill: role(name, "ink"), if shown { label } else { hide(label) }),
    fill: if shown { role(name, "wash") } else { none },
    stroke: none,
    shape: fletcher.shapes.pill,
    inset: 0.5em,
  )
  let flow(from, to, label, side, at: 0.5) = edge(
    from,
    to,
    label: label,
    label-side: side,
    label-pos: at,
    stroke: 1pt + role("water", "mark"),
    marks: "-|>",
  )
  let act(from, to, label, name, side: left) = edge(
    from,
    to,
    label: label,
    label-side: side,
    stroke: 1pt + role(name, "mark"),
    marks: "-|>",
  )
  let grass = step >= 2
  let trees = step >= 4
  let fire = step >= 5
  let parts = (
    store((1, 0), [rain $p$], "water"),
    store((1, 1), [surface water $O$], "water"),
    store((1, 2), [soil water $w$], "water"),
    store((0, 3.4), [grass $G$], "grass", shown: grass),
    store((2.3, 2), [deep water $d$], "water", shown: trees),
    store((2.3, 3.4), [trees $T$], "trees", shown: trees),
    store((1.15, 4.5), [fire $F$], "fire", shown: fire),
    flow((1, 0), (1, 1), [falls], right),
    flow((1, 1), (-0.25, 1), [lost], right, at: 0.8),
    flow((1, 1), (1, 2), if step >= 3 [soaks in, faster under plants] else [soaks in], left),
    flow((1, 2), (-0.25, 2), if trees [dries, slower in shade] else [dries in the sun], right, at: 0.8),
    flow((1, 2), (2.3, 2), [trickles down], right, at: 0.55),  // below, clear of the soaking label
  )
  if grass {
    parts.push(flow((1, 2), (0, 3.4), [drunk by grass], center, at: 0.68))
  }
  if trees {
    parts += (
      flow((1, 2), (2.3, 3.4), [drunk by trees], center, at: 0.68),  // well below trickles down
      flow((2.3, 2), (2.3, 3.4), [], left),
      act((2.3, 3.4), (0, 3.4), [shade], "trees", side: right),
    )
  }
  if fire {
    parts += (
      act((0, 3.4), (1.15, 4.5), [fuel], "grass", side: center),
      act((1.15, 4.5), (2.3, 3.4), [kills young trees], "fire", side: center),
    )
  }
  // Spacing grows with the text; `tall` and `wide` reshape it for wide, low pages such as slides.
  diagram(spacing: (18mm * wide * (size / 9pt), 11mm * tall * (size / 9pt)), ..parts)
}
