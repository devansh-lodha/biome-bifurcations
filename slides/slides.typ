// The talk: one story told in headlines. Every slide states one message as a full sentence and
// shows the evidence for it, with at most a short caption, so the deck also reads on its own.
// Every number comes from build/numbers.json and every figure from build/figures/slides, both
// written by the code. Headlines break by hand, between
// phrases.

#import "/typst/style.typ": *
#import "/typst/deck.typ": *
#import "/typst/diagram.typ": model-diagram
#import "/typst/pictures.typ": drop-rows, loop, neighbors, patch, pill, sideways, staircase, store

#show: deck
#set document(title: "Why the same rain can grow grassland or forest", author: "Devansh Lodha")

#let prm = numbers.parameters
#let alone = numbers.grass_alone
#let example = numbers.examples
#let percent(x) = str(int(calc.round(x)))
// A whole number with its thousands marked by a comma.
#let grouped(n) = {
  let s = str(int(n))
  if s.len() > 3 { s.slice(0, s.len() - 3) + "," + s.slice(s.len() - 3) } else { s }
}
#let rain(x) = grouped(int(mm(x)))
#let soak(i) = 10 * i / (i + 1)
#let bare-soak = int(calc.round(soak(prm.eps)))
#let full-soak = int(calc.floor(soak(prm.eps + prm.beta)))
#let switched(name) = numbers.mechanisms.find(row => row.mechanism == name).features
#let tipping = numbers.features.at("desert tipping")
#let treeless = numbers.features.grassland
#let tests = numbers.robustness.len()
#let kept = numbers.robustness.filter(row => row.lost.len() == 0).len()
// A word in the ink of its meaning, where the evidence draws that meaning in the same color.
#let hue(name, body) = text(fill: role(name, "ink"), body)
// A figure at exactly its drawn width, never scaled.
#let fig(name, width: 21cm) = image(figure-file("slides", name), width: width)
// A grey note under a term of an equation. It takes no width of its own, so the equation keeps
// its natural spacing; math shrinks it, so it is set large. Notes stay short, so neighbors clear.
#let tag(body) = context {
  let note = text(font: text-font, size: 28pt, fill: quiet, body)
  let size = measure(note)
  box(width: 0pt, height: size.height, place(center + top, box(width: size.width, note)))
}
// A note that keeps its natural width, for terms too short and close for notes of no width.
#let wide-tag(body) = text(font: text-font, size: 28pt, fill: quiet, body)
// Written straight after a braced term, with no space between (math would show the space): a box
// of no width that reaches deeper than any term, even one in parentheses, so all the braces of an
// equation sit at one depth.
#let strut = box(width: 0pt, height: 1em, baseline: 0.5em)
// Terms already met, in grey, so the new ones stand out.
#let faded(body) = text(fill: quiet, body)
// A picture beside what to read in it, each at its natural width.
#let pair(left-part, right-part, gutter: 1.6cm) = grid(
  columns: (auto, auto),
  column-gutter: gutter,
  align: horizon,
  box(left-part), box(right-part),
)

#title-slide(
  [Why the same rain can grow \ grassland or forest],
  [A simple model of water, light, and fire],
  [Devansh Lodha],
  [23110091],
  [EH-605 Modeling Earth System and Sustainability],
  [Indian Institute of Technology Gandhinagar],
  [Fall 2026],
)

// The puzzle ----------------------------------------------------------------------------------

#slide(
  title: [More rain means more trees, \ but only up to a ceiling.],
  caption: [Each point is one of #numbers.data.sites places in Africa, and 99 in 100 lie
    below~the~line. Data from NASA's ORNL DAAC, doi:10.3334/ORNLDAAC/850.],
)[
  #fig("ceiling")
]

#slide(
  title: [Below the ceiling, the same rain \ can grow no trees or many.],
  caption: [At about #rain(numbers.data.spread_mm)~mm~a~year, #numbers.data.spread_sites places
    range from #percent(numbers.data.spread_percent.at(0)) to
    #percent(numbers.data.spread_percent.at(1)) percent tree cover.],
)[
  #fig("spread")
]

#slide(title: [This leaves us with three questions.])[
  #set text(size: 30pt)
  #set par(spacing: 1.1em)
  What sets the ceiling?

  Why does the same rain grow such different land?

  Why can land change suddenly?
]

// The model -----------------------------------------------------------------------------------

#slide(
  title: [We follow one patch of land, \ with many plants and the same rain.],
  caption: [We average everything over the patch. A single point is either under a tree or not,
    but a patch can be partly covered.],
)[
  #patch(unit: 1.08cm, size: 20pt)
]

#slide(
  title: [At first every patch is like its neighbors, \ so flows between them cancel.],
  caption: [Alike patches trade equal flows both ways, so we can follow one patch on its own.],
)[
  #neighbors(unit: 2.8cm, size: 22pt, alike: true)
]

#slide(title: [Each quantity changes by \ what flows in minus what flows out.])[
  #pair(
    store(unit: 2.0cm, size: 26pt),
    $ (dif X) / (dif t) = "in" - "out" $,
    gutter: 2.4cm,
  )
]

#slide(
  title: [If each drop has the same chance of leaving, \ twice the water loses twice as much.],
  caption: [So each outflow is a rate times the amount.],
)[
  #drop-rows(
    ([Of 10 drops, 1 leaves each hour], 10, 1),
    ([Of 20 drops, 2 leave each hour], 20, 2),
    size: 24pt,
    drop: 0.8cm,
  )
]

#slide(
  title: [We measure time in drying times, \ so soil water in full sun dries at rate 1.],
  caption: [One drying time is how long a drop lasts, on average, in bare, sunny soil. Every
    other rate is measured against it.],
)[
  #set text(size: 26pt)
  #table(
    columns: (auto, auto),
    align: (left + horizon, center + horizon),
    column-gutter: 1.5cm,
    table.header[Unit of time][Drying],
    table.hline(stroke: 0.6pt + neutral("hairline")),
    [an hour, a day, or a year], $r #w$,
    [one drying time, $1 \/ r$], $#w$,
  )
]

#slide(
  title: [Rain on the surface \ either soaks into the soil or is lost.],
  caption: [Lost water evaporates or runs off into streams. $I$ says how fast rain soaks in
    compared with how fast it is lost.],
)[
  $
    (dif #O) / (dif t) = underbrace(#p#strut, #tag[rain]) - underbrace(I #O#strut, #tag[soaks in])
    - underbrace(#O#strut, #tag[lost])
  $
]

#slide(
  title: [Soil water fills from above \ and dries out through the surface.],
  caption: [A share $theta$ of what soaks in trickles below the grass roots. The rest dries as
    water seeps up through the soil's tiny pores and evaporates at the top, without pooling
    first.],
)[
  $
    (dif #w) / (dif t) = underbrace((1 - theta) I #O#strut, #tag[soaks in, stays])
    - underbrace(#w#strut, #tag[dries])
  $
]

#slide(
  title: [Grass drinks soil water, \ more where there is more grass or more water.],
  caption: [Twice the grass or twice the water means twice the drinking, at a rate set by $u$.],
)[
  $
    (dif #w) / (dif t) = (1 - theta) I #O - #w - underbrace(u #w #G#strut, #tag[drunk by grass])
  $
]

#slide(
  title: [Grass grows from what it drinks \ until the ground is full, and dies steadily.],
  caption: [Grass is about #int(1 / prm.m_g) times slower than soil water. Full cover is
    $#G = 1$, and at $#w = 1$ sparse grass only just survives.],
)[
  $
    (dif #G) / (dif t) = underbrace(m_g #w #G (1 - #G)#strut, #tag[grows])
    - underbrace(m_g #G#strut, #tag[dies])
  $
]

#slide(
  title: [Roots and leaves break the soil crust, \ so rain soaks in faster under plants.],
  caption: [$epsilon$ is how fast rain soaks into bare, crusted soil, where only #bare-soak drops
    in 10 get in. $beta$ is how much plants add.],
)[
  #pair(
    drop-rows(([bare soil], 10, bare-soak), ([full grass], 10, full-soak), size: 24pt, drop: 0.7cm),
    $ I = epsilon + beta #G $,
    gutter: 2.2cm,
  )
]

#slide(title: [So more grass lets in more rain, \ which grows more grass.])[
  #loop(
    ([more grass], "grass"),
    ([more rain soaks in], "water"),
    ([wetter soil], "water"),
    color: role("grass", "mark"),
    size: 24pt,
    radius: 1.0,
  )
]

#slide(
  title: [Water below the grass roots becomes deep water, \ which only trees reach.],
  caption: [Deep water fills and drains fast and never moves sideways, so it always sits where
    inflow equals outflow.],
)[
  #show math.equation.where(block: true): set text(size: 32pt)
  $
    (dif #d) / (dif t) = underbrace(theta I #O#strut, #wide-tag[trickles down])
    - underbrace(#d#strut, #wide-tag[drains]) - underbrace(u #T #d#strut, #wide-tag[drunk by trees])
  $
  #v(0.1cm)
  $
    #d = (theta I #O) / underbrace(1 + u #T, #tag[rate of leaving])
  $
]

#slide(
  title: [Each layer of leaves passes the same share of light, \ so shade deepens fast.],
  caption: [$k$ sets how much shade trees cast. Tree cover, as the data measure it, is the share
    of light the crowns catch, $1 - L$.],
)[
  #pair(fig("light", width: 13cm), $ L = e^(-k #T) $)
]

#slide(
  title: [Shade slows drying, caps grass, \ and holds back young trees.],
  caption: [A tree's growth here means young trees joining the stand, so a closed canopy shades
    out its own seedlings. That is what limits trees.],
)[
  #set text(size: 24pt)
  #grid(
    columns: (auto, auto, auto),
    column-gutter: 0.8cm,
    row-gutter: 0.6cm,
    align: (right + horizon, left + horizon, left + horizon),
    pill([soil water], name: "water", size: 24pt), [dries more slowly], [$L #w$ instead of #w],
    pill([grass], name: "grass", size: 24pt), [is capped by the light], [$#w #G (1 - #G \/ L)$],
    pill([young trees], name: "trees", size: 24pt), [need light], [tree growth times $L$],
  )
]

#slide(
  title: [Trees grow from shallow and deep water, \ in the light that is left.],
  caption: [Trees are about #int(1 / prm.m_t) times slower than soil water. Like grass, they drink
    soil water and help rain soak in.],
)[
  $
    (dif #T) / (dif t) = underbrace(m_t (#w + #d) L #T#strut, #tag[grows])
    - underbrace(m_t #T#strut, #tag[dies])
  $
]

#slide(
  title: [Fire passes from tuft to tuft, \ so it crosses a patch only where grass is thick.],
  caption: [#F is the share of the patch that burns. It switches on near the fuel level $g_c$, and
    $n$ sets how sharply.],
)[
  #pair(fig("fire", width: 13cm), $ #F = #G^n / (#G^n + g_c^n) $)
]

#slide(
  title: [Fire kills young trees, \ while burnt grass sprouts again from its roots.],
  caption: [Grass keeps its roots alive underground and regrows soon after a fire, but young trees
    die. Where fire burns, it kills a share $h$ of them.],
)[
  $
    (dif #T) / (dif t) = m_t (#w + #d) L underbrace((1 - h #F)#strut, #tag[spared by fire]) #T
    - m_t #T
  $
]

#slide(title: [Four budgets make the whole model, \ each term from one physical fact.])[
  #show math.equation.where(block: true): set text(size: 24pt)
  $
    (dif #O) / (dif t) & = #p - I #O - #O \
    (dif #w) / (dif t) & = (1 - theta) I #O - L #w - u #w (#G + #T) \
    (dif #G) / (dif t) & = m_g [#w #G (1 - #G \/ L) - #G] \
    (dif #T) / (dif t) & = m_t [(#w + #d) L (1 - h #F) #T - #T]
  $
  #v(0.25cm)
  #text(size: 21pt)[$I = epsilon + beta (#G + #T)$ #h(1.4em) $L = e^(-k #T)$ #h(1.4em)
    $#d = theta I #O \/ (1 + u #T)$ #h(1.4em) $#F = #G^n \/ (#G^n + g_c^n)$]
]

#slide(title: [Water feeds the plants, \ and shade and fire link them.])[
  #model-diagram(size: 16pt, tall: 0.6, wide: 1.4)
]

#slide(
  title: [Eleven constants set how strong \ and how fast each process is.],
  caption: [Halve any one of them, or raise it by half, and every feature you will see survives in
    #kept of #tests such tests.],
)[
  #set text(size: 22pt)
  #set table(inset: (x: 7pt, y: 8pt))
  #show table.cell.where(y: 0): set text(weight: "regular")
  #let row(symbol, meaning, value) = (symbol, meaning, align(right, value))
  #let constants(..rows) = table(
    columns: (auto, 1fr, auto),
    align: left + horizon,
    table.hline(stroke: 0.6pt + neutral("hairline")),
    ..rows.pos().flatten(),
    table.hline(stroke: 0.6pt + neutral("hairline")),
  )
  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1cm,
    align: top,
    constants(
      row($epsilon$, [bare-soil soaking], [#prm.eps]),
      row($beta$, [soaking from plants], [#prm.beta]),
      row($theta$, [share trickling down], [#prm.theta]),
      row($u$, [drinking by plants], [#prm.u]),
      row($k$, [shade from trees], [#prm.k]),
      row($g_c$, [grass fuel for fire], [#prm.gc]),
    ),
    constants(
      row($n$, [fire switch sharpness], [#int(prm.n)]),
      row($h$, [young trees fire kills], [#prm.h]),
      row($m_g$, [speed of grass], [#prm.m_g]),
      row($m_t$, [speed of trees], [#prm.m_t]),
      row($D_O$, [surface water spread], [#grouped(prm.d_o)]),
      ([~], [], []), // an empty row, as tall as the others, so both tables end level
    ),
  )
]

// Solving it ----------------------------------------------------------------------------------

#slide(
  title: [Solved over time, \ a few seeds grow into a steady grassland.],
  caption: [Grass alone at #rain(example.growth_rain_mm)~mm~a~year, solved with SciPy's
    `solve_ivp` (BDF method). One conversion factor, set from the data later, turns the model's
    rain into millimeters.],
)[
  #fig("growth")
]

#slide(
  title: [To see what rain does, \ we raise it slowly, then lower it.],
  caption: [Each point marks where the land settles before the rain changes again. If~the way down
    differs from the way up, the land remembers its past.],
)[
  #staircase(unit: 1.0cm, size: 22pt)
]

#slide(
  title: [A plant at zero stays at zero, \ so each step adds a trace of seed.],
  caption: [Real land gets seeds from elsewhere. So before each change of rain, any plant that has
    died out gets one ten-thousandth of full cover, while plants already growing are left alone.],
)[
  $
    (dif #G) / (dif t) = m_g underbrace(#G#strut, #tag[zero stays zero]) [#w (1 - #G \/ L) - 1]
  $
]

// Results -------------------------------------------------------------------------------------

#slide(
  title: [If plants did not open the soil, \ more rain would simply mean more grass.],
  caption: [Grass alone, with every patch soaking like bare soil. As the rain rises and then
    falls, grass follows the same path both ways.],
)[
  #fig("smooth")
]

#slide(
  title: [Because plants open the soil, \ grass appears suddenly and holds on with less rain.],
  caption: [Between #rain(alone.fold_mm) and #rain(alone.greens_mm)~mm~a~year, land can be bare or
    green, depending on what was there before.],
)[
  #fig("greening")
]

#slide(
  title: [Above #rain(alone.greens_mm)~mm, a few seeds keep growing \ until the grass is
    established.],
  caption: [The curve shows growth minus death for each amount of grass. Where it is above zero,
    grass grows.],
)[
  #fig("jump")
]

#slide(
  title: [At 260~mm, a few seeds die out, \ but established grass keeps itself going.],
  caption: [The open circle is a threshold. Below it grass shrinks to nothing, and above it grass
    grows.],
)[
  #fig("memory")
]

#slide(
  title: [Without fire, water alone sets a ceiling \ that rises and levels off like the data.],
  caption: [Fire only thins trees, so the most wooded places show what water allows. We convert
    model rain to millimeters so this curve lies along the top of the data.],
)[
  #fig("fit")
]

#slide(
  title: [With fire, the same rain \ can end as #hue("fire")[savanna] or as #hue("trees")[forest].],
  caption: [At #rain(example.outcomes_rain_mm)~mm~a~year, a start at
    #percent(example.outcomes_start_cover_percent.at(0)) percent tree cover ends at
    #percent(example.outcomes_end_cover_percent.at(0)), and a start at
    #percent(example.outcomes_start_cover_percent.at(1)) ends at
    #percent(example.outcomes_end_cover_percent.at(1)).],
)[
  #fig("outcomes")
]

#slide(title: [We call it #hue("fire")[savanna] \ when grass carries fire beneath the trees.])[
  #let side(name, head, ..lines) = align(left, {
    pill(head, name: name, size: 28pt)
    v(0.35cm)
    set text(size: 24pt)
    pad(left: 0.5em, lines.pos().join(linebreak()))
  })
  #grid(
    columns: 2,
    column-gutter: 3cm,
    side(
      "fire",
      [savanna],
      [#percent(example.outcomes_end_cover_percent.at(0)) percent tree cover],
      [thick grass],
      [fire spreads],
    ),
    side(
      "trees",
      [forest],
      [#percent(example.outcomes_end_cover_percent.at(1)) percent tree cover],
      [thin grass],
      [fire cannot spread],
    ),
  )
]

#slide(title: [#hue("fire")[Fire] keeps savanna open \ by killing the young trees that would close it.])[
  #loop(
    ([thick grass], "grass"),
    ([fire spreads], "fire"),
    ([fewer young trees], "trees"),
    ([more light for grass], "grass"),
    color: role("fire", "mark"),
    size: 24pt,
    radius: 1.0,
  )
]

#slide(title: [#hue("trees")[Shade] keeps forest closed \ by starving fire of grass.])[
  #loop(
    ([more trees], "trees"),
    ([deep shade], "trees"),
    ([thin grass], "grass"),
    ([no fire], "fire"),
    color: role("trees", "mark"),
    size: 24pt,
    radius: 1.0,
  )
]

#slide(
  title: [From desert to forest, the land jumps, \ at different rains going up and down.],
  caption: [Two states are possible at #rain(tipping.at(0)) to #rain(tipping.at(1)) and
    #rain(marks.savanna_or_forest_mm.at(0)) to #rain(marks.savanna_or_forest_mm.at(1))~mm~a~year.
    Fire keeps every tree out from #rain(treeless.at(0)) to #rain(treeless.at(1))~mm.],
)[
  #fig("sequence")
]

#slide(
  title: [Neighboring patches share water \ in proportion to how much they differ.],
  caption: [$nabla^2 #O$ is how much more water the neighbors hold, on average, than the patch.],
)[
  #pair(
    neighbors(unit: 1.6cm, size: 20pt),
    $
      (partial #O) / (partial t) = #p - I #O - #O + underbrace(D_O nabla^2 #O#strut, #tag[sharing])
    $,
    gutter: 1.1cm,
  )
]

#slide(
  title: [Every budget gains a spreading term, \ except deep water, which stays put.],
  caption: [Lengths are measured so that seeds spread at rate 1, and surface water spreads
    #grouped(prm.d_o) times faster.],
)[
  #show math.equation.where(block: true): set text(size: 24pt)
  $
    (partial #O) / (partial t) & = #faded($p - I O - O$) + D_O nabla^2 #O \
    (partial #w) / (partial t) & = #faded($(1 - theta) I O - L w - u w (G + T)$) + nabla^2 #w \
    (partial #G) / (partial t) & = #faded($m_g [w G (1 - G \/ L) - G]$) + nabla^2 #G \
    (partial #T) / (partial t) & = #faded($m_t [(w + d) L (1 - h F) T - T]$) + nabla^2 #T
  $
]

#slide(
  title: [At the desert edge, \ grass forms spots, mazes, and gaps.],
  caption: [128 by 128 patches, from even grass with 1~percent random unevenness, shown after
    30,000 drying times.],
)[
  #fig("maps")
]

#slide(
  title: [Bare ground sheds rain toward grass, \ which thrives while its neighbors go thirsty.],
  caption: [The soaking loop, working sideways, turns small unevenness into a pattern.],
)[
  #sideways(unit: 2.6cm, size: 22pt)
]

#slide(title: [Take away any one fact, \ and part of the picture disappears or moves.])[
  #set text(size: 24pt)
  #table(
    columns: (auto, auto),
    align: (left + horizon, left + horizon),
    column-gutter: 0.3cm,
    inset: (x: 12pt, y: 8pt),
    table.hline(stroke: 0.6pt + neutral("axis")),
    table.header[Take away][and the model loses],
    table.hline(stroke: 0.4pt + neutral("hairline")),
    [the soaking loop], [the desert edge's memory, and the patterns],
    [deep water for trees], [savanna below #rain(switched("only trees reach deep water").grassland.at(1))~mm],
    [shade slowing drying], [most of the desert edge's memory],
    [shade capping grass], [forest],
    [light for young trees], [open woodland],
    [fire], [savanna],
    [fast surface water], [the patterns],
    table.hline(stroke: 0.6pt + neutral("axis")),
  )
]

// What it means -------------------------------------------------------------------------------

#slide(title: [The model answers all three questions.])[
  #set text(size: 24pt)
  #table(
    columns: (11cm, 13cm),
    align: (left + horizon, left + horizon),
    inset: (x: 11pt, y: 11pt),
    table.hline(stroke: 0.6pt + neutral("axis")),
    table.header[Question][Answer],
    table.hline(stroke: 0.4pt + neutral("hairline")),
    [What sets the ceiling?], [Water. It sets the most trees the land can hold.],
    [Why does the same rain grow such different land?], [Fire and shade make two states possible, and history picks one.],
    [Why can land change suddenly?], [Loops that feed themselves create jumps and memory.],
    table.hline(stroke: 0.6pt + neutral("axis")),
  )
]

#slide(
  title: [Because land remembers, \ a change can outlast its cause.],
  caption: [Where two states are possible, the land keeps the one it has. Cleared land stays bare,
    and forest opened by fire stays savanna.],
)[
  #fig("windows")
]

#slide(
  title: [The model misses the trees that real land keeps \ between #rain(treeless.at(0)) and
    #rain(treeless.at(1))~mm~a~year.],
  caption: [Grey points are the field sites. The model also leaves out seasons, grazing, and
    differences between places, and the report lists every simplification.],
)[
  #fig("versus")
]

#thanks(
  [Devansh Lodha],
  [23110091],
  code: [All code and data at
    #link("https://github.com/devansh-lodha/biome-bifurcations")[github.com/devansh-lodha/biome-bifurcations]],
)
