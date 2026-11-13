// The report. Every number comes from build/numbers.json and every figure from build/figures,
// both written by the code (`uv run biome all`).

#import "/typst/style.typ": *
#import "/typst/diagram.typ": model-diagram
#import "/typst/pictures.typ": drop-rows, loop, neighbors, patch, stability, store

#let prm = numbers.parameters
#let percent(x) = str(int(calc.round(x)))
#let alone = numbers.grass_alone
#let example = numbers.examples
#let switched(name) = numbers.mechanisms.find(row => row.mechanism == name).features
// How wide the desert edge's memory is without shade slowing drying.
#let shrunk = {
  let edge = switched("shade slows drying").at("desert tipping")
  if edge.at(1) - edge.at(0) < 10 [a few millimeters] else [#rain(edge.at(0)) to #rain(edge.at(1)) millimeters]
}
// Rainfall written out for reading: rounded to 10 mm, thousands with a comma.
#let rain(x) = {
  let s = mm(x)
  if s.len() > 3 { s.slice(0, s.len() - 3) + "," + s.slice(s.len() - 3) } else { s }
}
#let feature(name, i) = rain(numbers.features.at(name).at(i))
// A whole number with its thousands marked by a comma.
#let grouped(n) = {
  let s = str(int(n))
  if s.len() > 3 { s.slice(0, s.len() - 3) + "," + s.slice(s.len() - 3) } else { s }
}
// Of ten drops landing on the ground, how many soak in, for a soaking number I.
#let soak(i) = 10 * i / (i + 1)
#let bare-soak = int(calc.round(soak(prm.eps)))
#let full-soak = int(calc.floor(soak(prm.eps + prm.beta)))

#set document(title: "Why the same rain can grow grassland or forest", author: "Devansh Lodha")
#set page(
  paper: "a4",
  margin: 2.5cm,
  footer: context align(center, text(size: 8pt, fill: neutral("axis"), counter(page).display())),
)
#set text(font: text-font, size: 11pt, fill: neutral("text"), lang: "en")
#set par(justify: true, leading: 0.7em, spacing: 1.2em)
#show math.equation: set text(font: math-font)
#set heading(numbering: "1.1")
#show heading: set text(size: 11pt, weight: "bold")
#show heading.where(level: 1): set text(size: 13pt)
#show heading: set block(above: 1.6em, below: 0.9em)
#set figure(gap: 0.8em, placement: auto)
#show figure.caption: set text(size: 9pt, fill: neutral("label"))
#set figure.caption(separator: [. ])
// A caption that fits on one line is centered under its figure; a longer one is set flush left,
// unjustified, so its last line is not stranded in the middle.
#show figure.caption: it => layout(room => {
  set par(justify: false)
  if measure(it).width > room.width { align(left, it) } else { it }
})
#show figure.where(kind: table): set figure.caption(position: top)
#set table(stroke: none, inset: (x: 6pt, y: 4pt))
#show table: set par(justify: false)
#set list(indent: 0.6em, spacing: 0.9em)

// A grey note under a term of an equation; math shrinks it, so it is set large.
#let note(body) = text(font: text-font, size: 12pt, fill: neutral("label"), body)
// Added to every braced term: a box of no width reaching a little deeper than any term does,
// even one in parentheses, so all the braces of an equation sit at one depth.
#let strut = box(width: 0pt, height: 1em, baseline: 0.5em)
// What the robustness check calls each feature and constant, in the words of the text.
#let feature-name = (
  "desert": [desert],
  "desert tipping": [the desert edge's memory],
  "patterns": [patterns],
  "open woodland": [open woodland],
  "shade switch": [the shade switch],
  "grassland": [fire-cleared grassland],
  "savanna": [savanna],
  "savanna-forest tipping": [the savanna-forest jump],
  "forest": [forest],
)
#let constant-name = (
  eps: $epsilon$, beta: $beta$, theta: $theta$, u: $u$, k: $k$, gc: $g_c$, n: $n$, h: $h$,
  m_g: $m_g$, m_t: $m_t$, d_o: $D_O$,
)
#let tests = numbers.robustness.len()
#let kept = numbers.robustness.filter(row => row.lost.len() == 0).len()
#let treeless = numbers.features.grassland
// A grey name beside an equation.
#let name(body) = text(font: text-font, size: 9pt, fill: neutral("label"), body)
// Text with a small picture beside it, kept whole on one page.
#let beside(body, picture, width: 5.6cm) = block(breakable: false, grid(
  columns: (1fr, width),
  gutter: 0.7cm,
  align: (left + top, center + horizon),
  body, picture,
))

// Title
#text(size: 22pt, weight: "bold")[Why the same rain can grow grassland or forest]
#v(0.2em)
#text(size: 12.5pt, fill: neutral("label"))[A simple model of water, light, and fire]
#v(0.6em)
#block({
  set par(justify: false, leading: 0.55em)
  text(size: 10pt, weight: "bold")[Devansh Lodha]
  text(size: 10pt, fill: neutral("label"))[ #h(0.2em) 23110091]
  linebreak()
  text(size: 9.5pt, fill: neutral("label"))[EH-605 Modeling Earth System and Sustainability
    #h(0.5em)·#h(0.5em) IIT Gandhinagar #h(0.5em)·#h(0.5em) Fall 2026]
})
#v(1.2em)

#block(inset: (x: 1.2em))[
  #text(size: 9pt, fill: neutral("label"))[Abstract]
  #v(0.3em)
  #text(size: 9.5pt)[
    More rain generally means more trees. Yet across Africa, places that get the same rain can
    look completely different, one an open grassland and another a dense woodland, and
    landscapes sometimes flip from one to the other with little warning. To understand why, we
    build a small model of a patch of land from a few physical facts about water, light, and
    fire, and add the facts one at a time to see what each one does. Solving the model
    numerically, we find three things. Water alone sets a ceiling on how wooded a place can be,
    and once we fit a single number, that ceiling rises and levels off much as it does across
    #numbers.data.sites field sites. Because plants help rain soak into the ground, vegetation at
    the edge of the desert appears suddenly and, once established, holds on with less rain than
    it needed to start. And because grass fuels fire while trees starve it of fuel, the same rain
    can sustain either savanna or forest, so a place's history decides which one it has. The
    model's clearest miss is that between about #rain(treeless.at(0)) and #rain(treeless.at(1))
    millimeters a year its fire keeps out every tree, where many real places have some.
  ]
]

= Background

== A ceiling, and a spread below it

Head south from the Sahara and the land changes from sand to grassland, then to grassland dotted
with trees, then to closed forest. The obvious explanation is rain, and it is only partly right.

@fig:data shows #numbers.data.sites places across Africa. For each one we know how much rain
falls in an average year and how much of the ground lies under tree crowns, which we call tree
cover. Two patterns stand out. The most wooded places get more wooded as rain
increases, up to about #rain(numbers.data.knee_mm) millimeters a year, and then level off near
#percent(numbers.data.plateau_percent) percent cover. That upper edge is a ceiling. Below it,
though, rain tells you surprisingly little. Among the #numbers.data.spread_sites places that get
about #rain(numbers.data.spread_mm) millimeters a year, some have #if numbers.data.spread_percent.at(0) < 1 [no trees at all] else [hardly any trees], and others are
#percent(numbers.data.spread_percent.at(1)) percent covered.

These measurements come from a published collection of field surveys, "Characteristics of
African Savanna Biomes for Determining Woody Cover", archived by NASA's Oak Ridge National
Laboratory Distributed Active Archive Center (doi:10.3334/ORNLDAAC/850).

#figure(
  image(figure-file("report", "spread")),
  caption: [More rain allows more trees, up to a ceiling, but the same rain can mean very
    different tree cover. Each point is one site. The line traces the ceiling, the 99th percentile
    of tree cover at each rainfall. The arrow spans the #numbers.data.spread_sites sites within
    #int(25) millimeters of #rain(numbers.data.spread_mm) millimeters a year.],
) <fig:data>

== Why it matters

If landscapes can flip, then a run of dry years, heavy grazing, or a change in how often fires
burn could turn grassland into desert or forest into savanna. Worse, the change might not undo
itself once the cause is gone. Knowing when and why that happens matters for keeping land
habitable for the plants, animals, and people that depend on it.

= Problem

We set out to answer three questions.

- What sets the ceiling on tree cover?
- Why do places with the same rain look so different?
- Why does land sometimes change suddenly instead of gradually?

Our approach is to build the simplest model that could answer them. We start from a handful of
physical facts, turn each one into a piece of math, and add them one at a time, so that we can
see exactly what each fact does. We solve the model numerically, and we use the data for only
one thing, to convert the model's rainfall into millimeters.

= Mathematical formulation

== One patch of land

The model describes one patch of land, an area large enough to hold many clumps of grass and
many trees, and small enough that rain falls evenly across it. We use a patch rather than a single
point because grass cover, tree cover, and fire only make sense over an area. A single point is
either under a tree or not, but a patch can be partly covered. Every quantity is an average over the patch, and
we track five of them (@fig:patch).

- Surface water, #O, is rain lying on the ground, not yet soaked in.
- Soil water, #w, is water in the top layer of soil, within reach of grass roots.
- Deep water, #d, is water below the reach of grass roots, which only tree roots reach.
- Grass, #G, and trees, #T, are the amount of each plant on each unit of ground.

Rain falls on the patch at a rate #p, its yearly average. We first treat every patch as alike, so
whatever flows out of a patch sideways is matched by what flows in from its neighbors.
@sec:spreading lets them differ.

#figure(
  patch(unit: 0.78cm, size: 9pt),
  caption: [One patch of land and the five quantities the model follows. Grass roots reach only
    the upper soil, while tree roots also reach the deep soil below it.],
) <fig:patch>

== Budgets

#beside[
  Each quantity changes only through what flows in and what flows out (@fig:store). Its rate of
  change is the difference:
  $ (dif X) / (dif t) = "in" - "out". $
  Building the model means listing, for each quantity, every way it gains and every way it
  loses, and how fast each happens.
][
  #figure(
    store(unit: 0.62cm, size: 8.5pt),
    placement: none,
    caption: [Each quantity is a store that changes by what flows in minus what flows out.],
  ) <fig:store>
]

One rule settles most of the outflows. Suppose every drop of water in the soil has the same small
chance of drying out in the next hour. Then twice the water means twice as many drops leaving, so
the outflow is proportional to the amount, a constant rate times $X$. The same holds for water
draining away and for plants dying of old age.

== Water

Rain lands on the surface at a rate #p. A drop on the surface can go two ways. It can soak into
the soil, or it can be lost, by evaporating or by running off into streams. Each happens at a
rate proportional to the surface water:
$
  (dif #O) / (dif t) = underbrace(#p#strut, #note[rain]) - underbrace(I #O#strut, #note[soaks in])
  - underbrace(#O#strut, #note[lost]).
$
The number $I$ says how fast water soaks in compared with how fast it is lost, so a share
#box($I \/ (I + 1)$) of the rain soaks in. On bare, crusted soil, about #bare-soak drops in 10 do.

Water also flows sideways between patches, but while every patch is alike, each sends out as
much as it receives, so these flows cancel and do not appear here.

Water that soaks in becomes soil water, but each drop has the same chance, $theta$, of trickling
on below the roots of grass to become deep water. So a fixed share $theta$ goes deep, and the rest
stays within reach of grass roots. Soil water also dries in the sun, and it does not need to
pool on the surface first. Water seeps up through the soil's tiny pores and evaporates at the top,
at a rate proportional to how much there is:
$
  (dif #w) / (dif t) = underbrace((1 - theta) I #O#strut, #note[soaks in, stays])
  - underbrace(#w#strut, #note[dries]).
$

Why do the two losses, #O and #w, carry no constant? Every loss is a rate times an amount, and
the number that measures a rate depends on the unit of time, since the same drying is one number
per hour and another per day. We pick the unit that makes drying in bare, sunny soil run at exactly
rate 1. One unit of time, a drying time, is then how long a drop of soil water lasts there, on
average, and every other rate in the model is measured against it.

Surface water needs a loss rate of its own, and we take it to be the same, so puddles are lost
about as fast as bare soil dries. This choice does not change where the land settles. When surface
water is steady, the
share of rain that soaks in is #box($I \/ (I + 1)$), and we set $I$ so that this share matches real
soil, about #bare-soak drops in 10 on bare, crusted soil. With another loss rate, $I$ would change with
it to keep the same share, and the soil and the plants would settle exactly where they do now.
Only how quickly a puddle empties would change, and puddles empty far faster than plants grow
either way.

== Grass

Grass drinks, grows, and dies.

It drinks soil water at a rate $u #w #G$. Twice the roots drink twice as much, and wetter soil
gives each root more to drink, so drinking is proportional to both. This water leaves the soil,
which gains a new outflow:
$
  (dif #w) / (dif t) = (1 - theta) I #O - #w - underbrace(u #w #G#strut, #note[drunk by grass]).
$

It grows from what it drinks, so its growth is proportional to the same product, $#w #G$. Growth
slows as grass fills the ground, because once the ground is fully covered, new leaves only shade
old ones.
So we multiply growth by $1 - #G$, which is 1 on bare ground and 0 when the ground is full. We
measure grass so that full cover is 1, and soil water so that sparse grass in full sun only just
survives when $#w = 1$.

It dies at a steady rate. Each blade has the same small chance of dying on any day, so grass dies
in proportion to how much there is. Grass grows and dies about #int(1 / prm.m_g) times more
slowly than soil water dries, so both terms carry a small constant, $m_g$:
$
  (dif #G) / (dif t) = underbrace(m_g #w #G (1 - #G)#strut, #note[grows])
  - underbrace(m_g #G#strut, #note[dies]).
$

== Plants open the soil

#beside[
  Bare desert soil forms a crust that sheds rain. Plant roots and fallen leaves break it open, so
  rain soaks in faster where plants grow. We let the soaking number rise in step with the
  plants:
  $ I = epsilon + beta #G. $
  With no grass, $I = epsilon$ and #bare-soak drops in 10 soak in. Under full grass cover, more
  than #full-soak in 10 do (@fig:soak). The share #box($I \/ (I + 1)$) can never exceed 1, so this
  simple rule never lets more water soak in than falls.
][
  #figure(
    drop-rows(
      ([bare soil], 10, bare-soak),
      ([full grass], 10, full-soak),
      size: 8.5pt,
      drop: 0.3cm,
    ),
    placement: none,
    caption: [Of ten drops landing on the ground, how many soak in.],
  ) <fig:soak>
]

#beside[
  This closes a loop (@fig:soak-loop). More grass lets more rain soak in, wetter soil grows more
  grass, and more grass lets in more rain still. Loops like this one, where a change feeds itself,
  are what make land change suddenly, as later sections show.
][
  #figure(
    loop(
      ([more grass], "grass"),
      ([more rain soaks in], "water"),
      ([wetter soil], "water"),
      color: role("grass", "mark"),
      size: 8.5pt,
      radius: 1.25,
    ),
    placement: none,
    caption: [Plants help rain soak in, which helps plants.],
  ) <fig:soak-loop>
]

== Trees

Trees follow the same rules as grass, with three differences. They reach deeper, they cast
shade, and they are slower.

They reach deeper. The water that trickles below the roots of grass collects as deep water, with a
budget of its own. It fills from above, drains further down out of reach of all roots, and is
drunk by trees:
$
  (dif #d) / (dif t) = underbrace(theta I #O#strut, #note[trickles down])
  - underbrace(#d#strut, #note[drains away]) - underbrace(u #T #d#strut, #note[drunk by trees]).
$
We have no separate measure of how fast deep water drains, so it drains at the same unit rate as
drying, and trees drink deep water just as grass drinks soil water. Deep water fills and empties
far faster than trees grow, so it always sits close to the level where inflow equals outflow,
#box($theta I #O = (1 + u #T) #d$). And since it never flows between patches, we can use that level
directly, instead of giving deep water an equation of its own:
$ #d = (theta I #O) / (1 + u #T), $
what flows in, divided by the total rate at which it leaves. Surface and soil water change fast
too, but they flow between patches, which the patterns in @sec:patterns need, so they keep
equations of their own.

#beside(width: 6cm)[
  They cast shade. Light passing through a canopy behaves like light passing through stacked
  sheets of tinted glass, where each layer lets through the same share of the light reaching it.
  So the share of sunlight that reaches the ground falls exponentially as trees thicken
  (@fig:light):
  $ L = e^(-k #T). $
  Tree cover, the quantity in @fig:data, is the share of light the crowns catch, $1 - L$.
][
  #figure(
    image(figure-file("report", "light"), width: 100%),
    placement: none,
    caption: [Shade deepens fast as trees thicken.],
  ) <fig:light>
]

Shade changes three things. Soil in shade dries more slowly, so drying becomes $L #w$. Grass in
shade gets less light, so its cap drops from full cover to $L$, and its growth becomes
$#w #G (1 - #G \/ L)$. Young trees need light too, so tree growth is multiplied by $L$. The model
does not follow young and old trees separately, so a tree's growth means young trees joining the
stand, and what stops young trees stops growth. This is what limits trees, since a closed canopy
shades out its own seedlings.

They are slow. Trees grow and die about #int(1 / prm.m_t) times more slowly than soil water
dries:
$
  (dif #T) / (dif t) = underbrace(m_t (#w + #d) L #T#strut, #note[grows])
  - underbrace(m_t #T#strut, #note[dies]).
$
Trees also drink soil water, so the drinking term in the soil water budget becomes
$u #w (#G + #T)$, and their roots open the soil like grass, so soaking becomes
$I = epsilon + beta (#G + #T)$.

== Fire

Fire needs fuel, and in a savanna the fuel is grass. Within a patch, fire can only spread if the
grass is continuous enough for flames to pass from one clump to the next. In a sparse patch,
fires stay small and die out, while in a dense one they run across it.

#beside(width: 6cm)[
  So the share of the patch that burns rises steeply once grass passes a certain amount
  (@fig:fire):
  $ #F = #G^n / (#G^n + g_c^n). $
  #F is the share of the patch that burns. It is close to 0 below the fuel level $g_c$ and close
  to 1 above it, and $n$ sets how sharp the switch is.
][
  #figure(
    image(figure-file("report", "fire"), width: 100%),
    placement: none,
    caption: [Fire runs only through thick grass.],
  ) <fig:fire>
]

Where fire burns, it kills a share $h$ of the young trees, so a share $h #F$ of new trees dies
across the patch, and tree growth is multiplied by $1 - h #F$. Fires do not burn every year, and
$h$ also folds in how often they return.

Fire burns grass too, so why is there no fire term in the grass equation? A fire burns the leaves
of grass, but the roots survive underground, and the grass sprouts again soon after. So over the
years this model follows, fire leaves the amount of grass unchanged. Young trees cannot recover that fast, so the lasting effect of fire
falls on trees.

== The whole model

Together, four budgets make the whole model. Deep water needs none of its own, since it sits at
its balance:
$
  (dif #O) / (dif t) & = #p - I #O - #O && quad #name[surface water] \
  (dif #w) / (dif t) & = (1 - theta) I #O - L #w - u #w (#G + #T) && quad #name[soil water] \
  (dif #G) / (dif t) & = m_g [#w #G (1 - #G \/ L) - #G] && quad #name[grass] \
  (dif #T) / (dif t) & = m_t [(#w + #d) L (1 - h #F) #T - #T] && quad #name[trees]
$
with $I = epsilon + beta (#G + #T)$, $L = e^(-k #T)$, $#d = theta I #O \/ (1 + u #T)$, and
$#F = #G^n \/ (#G^n + g_c^n)$. @fig:diagram shows how the parts connect, and @tab:constants lists
the constants. They are one representative set in the model's own units, set from simple
physical facts. Bare, crusted soil lets about #bare-soak drops in 10 soak in, plants change far
more slowly than water and trees more slowly still, and fire needs fairly thick grass to spread.
@sec:facts shows that each feature we report disappears or moves when the fact
behind it is switched off, and @sec:robust that the features do not hang on these exact values.

#figure(
  model-diagram(size: 8.5pt),
  placement: none,
  caption: [The whole model. Water flows from rain down to the plants, and trees and grass act
    on each other through shade and fire.],
) <fig:diagram>

#figure(
  table(
    columns: (auto, 1fr, auto),
    align: (left, left, right),
    table.hline(stroke: 0.5pt + neutral("axis")),
    table.header[*Symbol*][*Meaning*][*Value*],
    table.hline(stroke: 0.4pt + neutral("hairline")),
    $epsilon$, [how readily rain soaks into bare soil], [#prm.eps],
    $beta$, [how much plants speed up soaking], [#prm.beta],
    $theta$, [share of soaked water that trickles below grass roots], [#prm.theta],
    $u$, [how fast plants drink], [#prm.u],
    $k$, [how much shade each unit of trees casts], [#prm.k],
    $g_c$, [grass needed for fire to spread], [#prm.gc],
    $n$, [how sharp the fire switch is], [#int(prm.n)],
    $h$, [share of young trees that fire kills], [#prm.h],
    $m_g$, [speed of grass compared with soil water], [#prm.m_g],
    $m_t$, [speed of trees compared with soil water], [#prm.m_t],
    $D_O$, [how fast surface water spreads, compared with seeds], [#grouped(prm.d_o)],
    table.hline(stroke: 0.5pt + neutral("axis")),
  ),
  caption: [The constants of the model, in its own units.],
) <tab:constants>

== Many patches <sec:spreading>

So far every patch has been alike, so the flows between them cancelled. Patterns need patches
that differ, and then water and seeds move between neighbors.

#beside[
  Surface water flows from a wetter patch to a drier one, as ink spreads in water, and the flow
  between two neighbors is proportional to the difference between them (@fig:neighbors). Seeds
  spread the same way, far more slowly.
][
  #figure(
    neighbors(unit: 0.85cm, size: 8.5pt),
    placement: none,
    caption: [A wetter patch shares water with each neighbor, in proportion to the difference.],
  ) <fig:neighbors>
]

On a grid of patches, the net flow into a patch is the sum of these flows from its four neighbors.
For a smooth landscape this sum becomes the spreading term $D nabla^2 X$, where $nabla^2 X$
measures how much more of $X$ the neighbors hold, on average, than the patch itself, and $D$ sets
how fast $X$ spreads. Each budget gains one such term:
$
  (partial #O) / (partial t) & = #p - I #O - #O + D_O nabla^2 #O \
  (partial #w) / (partial t) & = (1 - theta) I #O - L #w - u #w (#G + #T) + nabla^2 #w \
  (partial #G) / (partial t) & = m_g [#w #G (1 - #G \/ L) - #G] + nabla^2 #G \
  (partial #T) / (partial t) & = m_t [(#w + #d) L (1 - h #F) #T - #T] + nabla^2 #T
$
We measure length so that plants spread at rate 1, which makes one unit of length about how far
plants spread by seed in one unit of time. Soil water spreads as slowly as seeds, and surface water
#grouped(prm.d_o) times faster. Deep water lies too deep to flow sideways over these distances, so it
stays put. Only the patterns in @sec:patterns use these terms.

== Assumptions

@tab:assumptions lists every simplification the model makes and why it is reasonable.

#figure(
  table(
    columns: (1fr, 1.25fr),
    align: (left, left),
    row-gutter: 0.35em,
    table.hline(stroke: 0.5pt + neutral("axis")),
    table.header[*Assumption*][*Why it is reasonable*],
    table.hline(stroke: 0.4pt + neutral("hairline")),
    [Rain is steady, at its yearly average],
    [We ask where land settles over many years, over which wet and dry seasons average out.],
    [Neighboring patches are alike, except in the pattern experiment],
    [Sideways flows between alike patches cancel, so one patch can be followed on its own.],
    [Every loss is proportional to the amount],
    [Each drop or plant has the same chance of leaving or dying in a given time.],
    [Surface and deep water are lost at the same unit rate as soil dries],
    [For surface water this does not change where the land settles, since $I$ is set from the
      share of rain that soaks in. For deep water we have no separate measure.],
    [Deep water sits at its balance level],
    [It fills and drains far faster than trees grow, and it does not flow between patches.],
    [A tree's growth means young trees joining the stand],
    [The model does not follow young and old trees separately.],
    [Grass and trees drink, grow, and die by the same rules],
    [Every difference between them then comes from what sets them apart, namely deep roots,
      shade, fire, and speed.],
    [Fire does not reduce grass],
    [Grass sprouts again from its surviving roots, but young trees die.],
    [No grazing or browsing],
    [Leaving them out isolates water, light, and fire, and the code can switch both on.],
    [Deep water does not move sideways],
    [It lies below the roots of grass, out of the way of the flows that make patterns.],
    [Grass and trees spread equally fast, and soil water as fast as seeds],
    [No data set them apart, and the patterns come from surface water spreading far faster than
      all three.],
    [A trace of seed before each step of the rain experiment],
    [Real land always receives seeds, and the trace changes no state where plants already
      grow.],
    table.hline(stroke: 0.5pt + neutral("axis")),
  ),
  caption: [What the model assumes, and why.],
) <tab:assumptions>

= Methods of solution

== Solving the equations

We solve the four equations numerically with `solve_ivp` from the SciPy library, using its BDF
method, which is built for equations whose parts change at very different speeds, like water and
trees here. Each solution runs until every quantity has stopped changing, which we call a steady
state. @fig:growth shows grass growing from a few seeds at #rain(example.growth_rain_mm)
millimeters of rain a year. It grows slowly at first, then fast, then not at all, once growth
balances death.

#figure(
  image(figure-file("report", "growth")),
  caption: [Solved over time, a few seeds grow into a steady grassland. Grass alone, at
    #rain(example.growth_rain_mm) millimeters of rain a year.],
) <fig:growth>

#beside[
  A steady state can be stable or unstable, like a ball in a bowl or on a hill (@fig:stability).
  Nudge the first and it rolls back. Nudge the second and it rolls away. Only stable states last
  on real land, so we keep only those. We check by computing how every small nudge grows or
  shrinks (from the eigenvalues of the equations' Jacobian matrix).
][
  #figure(
    stability(unit: 0.62cm, size: 8.5pt),
    placement: none,
    caption: [Stable and unstable states.],
  ) <fig:stability>
]

== Every steady state, directly

Running the equations forward shows where the land settles from one start. To be sure of every
rainfall we quote, we also find the steady states directly, as the points where all four rates
are zero, at every millimeter of rain from 50 to 3,000 a year. With water at its balance, this
leaves two equations in grass and trees, which root finders from SciPy solve. Unlike runs forward
in time, this also finds the unstable states, such as the open circle in @fig:balance that
divides bare ground from grassland. The stability of each state comes from the eigenvalues of the
Jacobian, computed exactly. Patterns get one more test. At each even, stable state we ask
whether a small ripple in space would grow, using the same Jacobian with the spreading terms
included. The runs forward in time confirm it all, and a test checks that each slow sweep jumps
exactly where the steady states say it should.

== The rain experiment

To see how the land depends on rain, we change the rain very slowly. Starting from bare ground, we
raise the rain in steps of 1 to 2 millimeters a year, find the steady state at each step, and
start each step from the previous one's state. Then we lower the rain the same way. If the land
follows the same path down as up, rain alone decides what grows. If not, the land remembers its
past.

One addition is needed. In the equations, a plant that is absent stays absent, because every
growth term is proportional to the plant itself. Real land always receives some seeds from
elsewhere. So before each step, any plant that has died out is topped up to a trace, one
ten-thousandth of full cover. This is part of the experiment, not of the equations. The trace is
too small to change any state where plants already grow. It only lets a plant return where it
can grow from very little.

== The pattern experiment

For patterns, we solve the equations with spreading on a square of 128 by 128 patches, 1,100 units
of length across, with each edge joined to the opposite one so that the square has no borders.
Rain is held fixed. Every patch starts at the even steady state of a single patch at that
rainfall, and its grass is then nudged up or down by about 1 percent at random, since real land is
never perfectly even. The equations are then solved for 30,000 units of time. Well before then,
the average amount of grass is steady and the kind of pattern no longer changes, though single
spots and stripes still drift slowly. Run twice as long, the maps look much the same. For this we
use our own solver. It computes the spreading between patches with fast Fourier transforms from
SciPy, which are exact on a grid with joined edges, and takes time steps of 0.05.

== One number from the data

The model measures rain in its own units, and one number, $S$, converts them to millimeters a
year. We find it from the ceiling. Fire, grazing, and people can only thin trees, so the most
wooded places at each rainfall show the most that water allows. So we switch fire off and record
the most tree cover the model reaches at each rainfall, which gives the model's ceiling. Changing
$S$ stretches or squeezes this curve along the rainfall axis, and we choose the $S$ that lays it
along the top of the data, so that, like the ceiling line in @fig:data, it has just 1 site in 100
above it. The best choice is
#box($S = #int(calc.round(numbers.scale.best))$) millimeters a year per model unit. Anything from
#int(calc.round(numbers.scale.low)) to #int(calc.round(numbers.scale.high)) fits nearly as well
and would simply shift every rainfall in this report by a few percent. This is the only number we
fit.

== Checking our work

Everything is written in Python with NumPy and SciPy, and every figure and number in this report
comes straight from the code. The code and the data are at
#link("https://github.com/devansh-lodha/biome-bifurcations")[github.com/devansh-lodha/biome-bifurcations],
where one command rebuilds every figure, every number, and this report. Automated tests check, among other things, that no water is created
or lost by mistake, that every steady state the solutions settle into solves the equations
exactly, that each jump in the rain experiment falls where the steady states say it should, and
that every number quoted here is the one the code produces.

= Solution

== Without the loop, grass grows gradually

Start with grass alone, and suppose plants did not open the soil, so that rain soaks in at the
bare-ground rate everywhere. As the rain rises, nothing grows until about
#rain(alone.greens_mm) millimeters a year, the point where a few seeds can just get ahead of
dying. From there, grass thickens slowly (@fig:smooth), and lowering the rain retraces the same path
exactly. Here, more rain simply means more grass.

#figure(
  image(figure-file("report", "smooth")),
  caption: [If plants did not open the soil, more rain would simply mean more grass. Grass
    alone, settled at each rainfall while the rain rises slowly and then falls.],
) <fig:smooth>

== With the loop, grass jumps and remembers

Now let grass open the soil, and run the same experiment (@fig:greening). As the rain rises,
nothing changes until about #rain(alone.greens_mm) millimeters, as before. But the moment grass
gets a foothold, it soaks up rain that used to be lost, grows, soaks up more, and leaps to an
established cover. As the rain falls, the grass holds on long after it could have started from scratch, all
the way down to about #rain(alone.fold_mm) millimeters, and only then collapses.

Between #rain(alone.fold_mm) and #rain(alone.greens_mm) millimeters, the same rain supports either
bare ground or a healthy grassland, and which one you find depends on what was there before. Bare
ground sheds the rain, so no grass can start, while grassland soaks it up, so grass survives.
The two ends of this range are tipping points. Cross one, and the land jumps to the other state.
Between them, the land has a memory.

#figure(
  image(figure-file("report", "greening")),
  caption: [Because plants help rain soak in, grass appears suddenly and holds on with less rain
    than it needed to start. The same experiment with the soaking loop, with the path without it
    in grey. Arrows mark the jumps.],
) <fig:greening>

== Why grass jumps

Why a jump, and not a gradual rise? @fig:balance plots, for each amount of grass, how fast grass
grows minus how fast it dies, with soil water at its balance level. Where the curve is above zero,
grass increases. Below zero it decreases, and where it crosses zero, grass stays put.

At 300 millimeters, the curve is above zero from bare ground all the way up to established grass.
Once a few seeds can grow at all, nothing stops them until the grass is established. That is the
jump.
At 260
millimeters, the curve starts below zero, so a few seeds die out, but it rises above zero once
there is a little more grass. Thin grass shrinks back to bare ground, while more grass grows to
the established state and keeps itself there. The open circle marks the dividing line between the two,
and it is why the land remembers. Without the soaking loop, the curve only ever falls as grass
increases, so grass settles where the curve first crosses zero, and a little more rain means a
little more grass.

#figure(
  image(figure-file("report", "balance")),
  caption: [With the soaking loop, a little grass can shrink while a lot of grass grows. Growth
    minus death for each amount of grass alone, at two rainfalls. Filled circles are states grass
    returns to, and the open circle is a threshold it moves away from.],
) <fig:balance>

== Trees and the ceiling

Now add trees, still without fire (@fig:fit). Wherever there is enough water, trees take over,
since they drink the deep water that grass cannot reach and their shade holds grass back. Tree cover
jumps up at the edge of the desert, climbs quickly, and then levels off as the canopy closes and
its own shade holds back its seedlings. This curve is the most tree cover that water can support
at each rainfall, the model's ceiling.

Here is the test. Fitting the one number $S$ stretches the rainfall axis, but the ceiling's shape
is entirely the model's own. It climbs and then levels off, as the data do, reaching
#percent(numbers.model_ceiling_at_knee_percent) percent at #rain(numbers.data.knee_mm) millimeters
a year, where the data level off at #percent(numbers.data.plateau_percent). So water alone gives a
ceiling of the right shape. The match is not perfect. In the driest places the model's ceiling
sits somewhat above even the most wooded sites, and in the wettest it keeps creeping up while the
data stay level.

#figure(
  image(figure-file("report", "fit")),
  caption: [Without fire, water alone sets a ceiling on trees that rises and levels off like the
    data. Each point is one site, and the line is the most tree cover the model reaches without
    fire.],
) <fig:fit>

== Savanna or forest

Now add fire. At #rain(example.outcomes_rain_mm) millimeters a year, we start two runs from nearly
the same mix of grass and trees, one with #percent(example.outcomes_start_cover_percent.at(0))
percent tree cover and the other with #percent(example.outcomes_start_cover_percent.at(1))
(@fig:outcomes). The first settles at #percent(example.outcomes_end_cover_percent.at(0)) percent
cover, with grass thick enough to burn. The second settles at
#percent(example.outcomes_end_cover_percent.at(1)) percent, with too little grass for fire. We call
the first savanna, land where grass carries fire beneath the trees, even when the trees cover
nearly half the ground. We call the second forest, a canopy so closed that fire cannot spread.

#figure(
  image(figure-file("report", "outcomes")),
  caption: [With fire, the same rain can end in savanna or forest, and the start decides which.
    Two runs at #rain(example.outcomes_rain_mm) millimeters a year, from nearly the same mix of
    grass and trees.],
) <fig:outcomes>

Each outcome is held in place by a loop of its own (@fig:fire-loops). With an open canopy, light
reaches the ground, grass grows thick, fire spreads, and fire kills the young trees that would have
closed the canopy. With a dense canopy, shade thins the grass, too little is left to carry fire, and young
trees survive to keep the canopy dense. A small difference at the start decides which loop takes
hold.

#figure(
  grid(
    columns: 2,
    gutter: 1.6cm,
    loop(
      ([thick grass], "grass"),
      ([fire spreads], "fire"),
      ([fewer young trees], "trees"),
      ([more light], "grass"),
      color: role("fire", "mark"),
      size: 8.5pt,
      radius: 1.15,
    ),
    loop(
      ([more trees], "trees"),
      ([deep shade], "trees"),
      ([thin grass], "grass"),
      ([no fire], "fire"),
      color: role("trees", "mark"),
      size: 8.5pt,
      radius: 1.15,
    ),
  ),
  caption: [Fire keeps savanna open (left), and shade keeps forest closed (right).],
) <fig:fire-loops>

== The whole picture

Finally, we run the full model from desert to forest and back, raising the rain and then lowering
it (@fig:sequence). From dry to wet, it goes like this.

- Below about #rain(marks.vegetation_from_mm) millimeters a year, nothing grows.
- Between about #feature("desert tipping", 0) and #feature("desert tipping", 1) millimeters, the
  desert edge has a memory. Bare ground stays bare, and vegetation that is already there stays.
  This edge lies drier than for grass alone, which needed #rain(alone.greens_mm) millimeters to
  start, because trees drink the deep water as well as the soil water, so they can start from
  bare ground with less rain.
- Up to about #feature("open woodland", 1) millimeters, grass and scattered trees grow together,
  too sparse for fire to spread. We call this open woodland, not savanna, since nothing burns.
- From about #rain(marks.fire_onset_mm) millimeters, the grass is thick enough to burn, and fire
  clears the trees by about #feature("grassland", 0), leaving open grassland up to about
  #feature("grassland", 1).
- Above that, trees return in spite of fire, and the savanna grows more wooded as the rain
  increases.
- Between about #rain(marks.savanna_or_forest_mm.at(0)) and
  #rain(marks.savanna_or_forest_mm.at(1)) millimeters, savanna and forest are both possible.
  Coming from the dry side, savanna holds out until #rain(marks.savanna_or_forest_mm.at(1))
  millimeters and then tips into forest. Coming from the wet side, forest holds out down to
  #rain(marks.savanna_or_forest_mm.at(0)) millimeters before fire breaks it open.
- Above about #rain(marks.forest_only_from_mm) millimeters, only forest remains.

#figure(
  image(figure-file("report", "sequence")),
  caption: [From desert to forest, the land jumps, and it jumps at different rainfalls going up
    and coming down. Tree cover settled at each rainfall as the rain rises and then falls. Arrows
    mark the jumps.],
) <fig:sequence>

== Patterns <sec:patterns>

With spreading switched on, grass at the desert edge does not stay even (@fig:maps). Between about
#feature("patterns", 0) and #feature("patterns", 1) millimeters a year, the 1 percent unevenness
grows into regular patterns, with spots at the drier end, a maze in the middle, and gaps at the
wetter end. It is the soaking loop again, working sideways. Where grass is a little denser, more rain
soaks in, while the bare ground around it sheds rain, and that water flows toward the grass. The
denser grass thrives on the extra water, and its neighbors go thirsty and thin out. Small
differences grow into a regular pattern of grass and bare ground.

#figure(
  image(figure-file("report", "maps")),
  caption: [Where neighboring patches share water, grass arranges itself into spots and mazes.
    Each map is a square of 128 by 128 patches at a fixed rainfall, started from even grass with
    1 percent random unevenness, and shown after 30,000 units of time, when the kind of pattern
    no longer changes. Darker means more grass. The bar is 200 units of length, where one unit is
    about how far plants spread by seed in one unit of time.],
) <fig:maps>

== What each fact contributes <sec:facts>

We can also run the experiment in reverse, taking away one fact at a time to see what breaks.
Take away the soaking loop, by letting rain soak in at one fixed rate, the rate under half plant
cover, and the desert edge loses its memory and its patterns. Take away the slower drying in
shade, and most of that memory goes too, as the stretch where bare and green are both possible
shrinks to #shrunk.
Take away the deep water that only trees can reach, and grassland stretches all the way to about
#rain(switched("only trees reach deep water").grassland.at(1)) millimeters. Take away the cap that
shade puts on grass, and forest never forms, as savanna holds at every rainfall we test, up to
#rain(switched("shade caps grass").savanna.at(1)) millimeters. Take away the light that young
trees need, and open woodland vanishes, as forest grows from about
#rain(switched("tree seedlings need light").forest.at(0)) millimeters, where the full model has
bare desert. Take away fire, and the savanna vanishes, as forest takes over from about
#rain(switched("fire spreads through grass").forest.at(0)) millimeters. Let surface water spread
no faster than seeds, and the patterns vanish. Each fact is needed for at least one feature of the
results.

== How much the constants matter <sec:robust>

The constants in @tab:constants are one representative choice, so we checked how much the
results depend on them. We halved each constant, then raised it by half, one at a time, keeping
the shares $theta$ and $h$ at most 1, and looked for every feature again. In #kept of the #tests
tests every feature survives, though each moves. @tab:robust lists the rest. All involve fire or
deep water, and they make physical sense. Fire needs grass thick enough to burn, so with a higher
fuel level it never spreads. And to hold savanna open against forest, it must kill enough young
trees. The fire-cleared grassland is the most fragile feature, which matters in @sec:limits.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 0.5pt + neutral("axis")),
    table.header[*Change*][*Features lost*],
    table.hline(stroke: 0.4pt + neutral("hairline")),
    ..numbers
      .robustness
      .filter(row => row.lost.len() > 0)
      .map(row => {
        let name = constant-name.at(row.constant)
        let how = if row.factor < 1 [halved] else if row.value == 1 [raised to 1] else [raised by half]
        ([#name #how], row.lost.map(f => feature-name.at(f)).join([, ]))
      })
      .flatten(),
    table.hline(stroke: 0.5pt + neutral("axis")),
  ),
  caption: [The tests in which a feature disappears when one constant is halved or raised by half.
    Every other test keeps every feature.],
) <tab:robust>

= Interpretation

== Loops make landscapes jump

Both tipping points come from the same kind of loop, a change that feeds itself. At the desert
edge, grass helps rain soak in, which helps grass. At the forest edge, grass feeds fire, which
keeps out the trees that would shade the grass away. Loops like these let two different states
sustain themselves at the same rain, and they make the switch between them sudden.

== History explains the spread

Back to the puzzle in @fig:data. The model says the spread below the ceiling need not be noise.
Wherever two states are possible, it is a place's history, not its rain, that decides which one
it holds.
A forest that burns at #rain(example.outcomes_rain_mm) millimeters a year can become a savanna and
stay one, even though the rain could support a forest. In the model, fire holds savanna well below
the ceiling that water alone would allow, which is one way the spread in @fig:data can arise. It
explains part of the spread, not all of it, as the next sections show.

== What it means for people

Because land remembers, damage can outlast its cause. In the model, vegetation cleared where the
rain is between #feature("desert tipping", 0) and #feature("desert tipping", 1) millimeters a year
does not come back when the clearing stops, unless the rain rises above about
#rain(marks.bare_soil_greens_above_mm) millimeters. And fire, which people both set and put
out, decides between savanna and forest across a wide range of rain.

== Where the model and the data disagree <sec:limits>

Between about #rain(treeless.at(0)) and #rain(treeless.at(1)) millimeters a year, the model's fire
keeps out every tree, while many real sites at these rains have some (@fig:versus). It is also
the model's most fragile feature (@tab:robust). With a gentler fire switch, a fire that kills
fewer young trees, or more deep water for trees, trees grow there. So
the model cannot say how strong fire is at these rains, and should not be trusted there.

#figure(
  image(figure-file("report", "versus")),
  caption: [The model misses the trees that real land keeps at middling rain. The full model,
    settled as the rain rises and then falls, drawn over the field sites. In the shaded stretch
    its fire keeps every tree out.],
) <fig:versus>

== What the model leaves out

@tab:assumptions lists what this deliberately simple model simplifies. It averages over seasons
and soil types, has no grazing animals, and uses one set of constants for the whole
continent. The data pin down the rainfall scale only to within a few percent, and the pattern
spacing comes in units of how far seeds spread, not in meters.

= Summary

#set list(spacing: 0.7em)
- Water alone sets a ceiling on tree cover, with the shape seen across #numbers.data.sites field
  sites.
- Because plants help rain soak in, vegetation at the desert edge appears suddenly, holds on
  with less rain than it needed to start, and arranges itself into patterns.
- Because grass feeds fire and trees starve it, savanna and forest are both possible between
  about #rain(marks.savanna_or_forest_mm.at(0)) and #rain(marks.savanna_or_forest_mm.at(1))
  millimeters a year, and history decides between them, which explains part of the spread
  below the ceiling.
- Take away any one fact, and part of this picture disappears or moves. Change any one constant
  by half, and in #kept of #tests tests every feature survives.
- The model's clearest miss is that between about #rain(treeless.at(0)) and
  #rain(treeless.at(1)) millimeters a year its fire keeps out every tree, while real land keeps
  some.

= Conclusion

A few physical facts, written as budgets of water and plants and solved numerically, explain the
ceiling on tree cover and part of the spread beneath it. The sudden changes come from loops that
feed themselves, and where two states are possible, history, not rain, decides which you see.
