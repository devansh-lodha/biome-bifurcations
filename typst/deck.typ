// The slide design. Every content slide is a headline and its evidence: the headline states the
// slide's one message as a full sentence, and the body shows what supports it, a figure, a
// picture, or an equation, with at most a short caption beneath. There are no boxes or bands:
// grouping comes from space and type, and color appears only where it carries a meaning.

#import "style.typ": math-font, neutral, text-font

#let ink = neutral("text")
#let quiet = neutral("label")

// Type roles, in points: few sizes, clearly apart.
#let sizes = (headline: 30pt, body: 22pt, caption: 19pt, small: 14pt)

// The whole deck: 16:9 pages, Lato at a size readable from the back of a room.
#let deck(body) = {
  set page(
    paper: "presentation-16-9",
    margin: (x: 1.9cm, top: 1.45cm, bottom: 1.2cm),
    fill: neutral("paper"),
  )
  set text(
    font: text-font,
    size: sizes.body,
    fill: ink,
    lang: "en",
    hyphenate: false,
    costs: (runt: 4000%, widow: 400%, orphan: 400%),
  )
  set par(leading: 0.55em, spacing: 0.9em, linebreaks: "optimized")
  set list(indent: 0pt, body-indent: 0.55em, spacing: 0.75em, marker: text(fill: neutral("axis"))[•])
  set enum(indent: 0pt, body-indent: 0.6em, spacing: 0.8em)
  set table(stroke: none, inset: (x: 11pt, y: 8pt))
  show table.cell.where(y: 0): set text(weight: "bold")
  show math.equation: set text(font: math-font)
  show math.equation.where(block: true): set text(size: 36pt)
  body
}

#let page-number = context text(size: sizes.small, fill: quiet, counter(page).display("1"))

// Centered text whose lines fill evenly, so no line is left with a word or two.
#let balanced(frac: 95%, body) = layout(sz => {
  let full = sz.width * (frac / 100%)
  let height(w) = measure(block(width: w, body)).height
  let target = height(full)
  let lo = full * 0.45
  let hi = full
  for _ in range(9) {
    let mid = (lo + hi) / 2
    if height(mid) <= target + 0.1pt { hi = mid } else { lo = mid }
  }
  align(center, block(width: hi + 1pt, align(center, body)))
})

// Left-aligned text whose lines fill evenly, for headlines.
#let balanced-left(frac: 100%, body) = layout(sz => {
  let full = sz.width * (frac / 100%)
  let height(w) = measure(block(width: w, body)).height
  let target = height(full)
  let lo = full * 0.5
  let hi = full
  for _ in range(9) {
    let mid = (lo + hi) / 2
    if height(mid) <= target + 0.1pt { hi = mid } else { lo = mid }
  }
  block(width: hi + 1pt, body)
})

// A short caption under the evidence: the detail that lets the slide stand on its own.
#let caption-text(body) = balanced(frac: 82%, text(size: sizes.caption, fill: quiet, body))

// The words of a piece of content, for messages.
#let plain(it) = if type(it) == str { it } else if it.has("text") { plain(it.text) } else if (
  it.has("children")
) { it.children.map(plain).join() } else if it.has("body") { plain(it.body) } else { " " }

// A content slide: the headline on top, then the evidence and its caption, centered in the space
// left. The evidence must fit whole: one too tall or too wide for its slide stops the build, naming
// the slide. Width is measured in unbounded space, so a picture that runs off the page is caught.
#let slide(title: none, caption: none, body) = page(
  footer: align(right, page-number),
  footer-descent: 0.3cm,
  grid(
    columns: (1fr,),
    rows: (auto, 1fr),
    row-gutter: 0.75cm,
    balanced-left(frac: 92%, text(size: sizes.headline, weight: "bold", fill: ink, title)),
    layout(room => {
      let evidence = pad(bottom: 0.25cm, {
        body
        if caption != none {
          v(0.45cm)
          caption-text(caption)
        }
      })
      let need = measure(evidence, width: room.width).height
      let wide = measure(body).width
      let named = "slide '" + plain(title) + "'"
      assert(need <= room.height, message: named + " is too tall by " + repr(need - room.height))
      assert(wide <= room.width, message: named + " is too wide by " + repr(wide - room.width))
      block(width: 100%, height: room.height, align(center + horizon, evidence))
    }),
  ),
)

// The title slide: the talk in the middle, its setting in the four corners.
#let title-slide(title, subtitle, author, id, course, place-name, term) = page(
  margin: (x: 1.1cm, y: 0.9cm),
  header: none,
  footer: none,
  {
    let corner(body) = text(size: sizes.small, fill: quiet, body)
    place(top + left, corner(course))
    place(top + right, corner(place-name))
    place(bottom + left, corner(term))
    place(bottom + right, page-number)
    align(center + horizon, block(width: 86%, {
      set par(leading: 0.4em)
      text(size: 44pt, weight: "bold", fill: ink, title)
      v(0.7cm)
      text(size: 24pt, fill: quiet, subtitle)
      v(1.3cm)
      text(size: 22pt, weight: "bold", fill: ink, author)
      v(0.12cm)
      text(size: 17pt, fill: quiet, id)
    }))
  },
)

// The closing slide, with where to find the code if a link is given.
#let thanks(author, id, code: none) = page(
  footer: none,
  align(center + horizon, {
    text(size: 48pt, weight: "bold", fill: ink)[Thank you]
    v(1cm)
    text(size: 22pt, weight: "bold", fill: ink, author)
    v(0.12cm)
    text(size: 17pt, fill: quiet, id)
    if code != none {
      v(1.1cm)
      text(size: 19pt, fill: quiet, code)
    }
  }),
)
