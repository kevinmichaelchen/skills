---
name: html-artifacts
description: >-
  Build a polished, self-contained HTML artifact — one file, no server, no CDN,
  no network, works offline over file:// and drops straight into Slack. Use for
  any shareable HTML deliverable: an explanatory write-up, an investigation, a
  report, a dashboard, or a chart. Not for in-app UI inside an existing React
  codebase. Defaults to a Tufte-style article with margin notes and Bklit charts;
  documents the house style, the library landscape, and the single-file build
  gotchas.
---

# HTML Artifacts

Turn work into a **single self-contained `.html` file** that can be shared with
teammates (Slack, email, S3) with **no server, no CDN, and no network** — it
works offline over `file://`.

## The house style — start here

**Default to an article that contains figures, not a grid of panels.** This is
the biggest single decision, it is already made, and you should deviate only
when you can say why.

A panel dashboard is the intuitive shape and it fails in a specific way: it
works only for a reader who already has the vocabulary. Everyone else gets
something that *looks* finished and cannot be read — and nobody reports that as
a bug, because it doesn't look like one. An article carries the same figures at
the same density and stays legible to someone outside the team. The margin
column is what buys that: jargon gets defined beside the sentence that uses it
instead of interrupting it.

### The shape

| Element | Why it is not optional |
|---|---|
| Title + one-sentence dek | The artifact gets pasted into a channel with no context |
| **Labelled** plain-language summary | Not a lede — a card that says "the short version". Written to a hard bar: no tool names, no file counts, no unit that needs defining |
| Numbered sections, each with the question it answers | The question is the real navigation. "Is this the slow part?" gets found; "Pool × isolation" does not |
| A margin column for definitions, asides, provenance | See *When the artifact has to explain itself* below |
| A status badge on every claim | `measured` / `projected` / `retracted` / `rejected` / `unproven` — and a retraction sits **next to the claim it kills**, never in a corrections section at the bottom |
| An environment tag on every metric | "66.3s" means different things on a laptop and a CI runner, and the reader cannot tell which they are looking at |
| A contents rail, past ~2 screens | Rendered from the same array as the headings — see *Navigation* below |
| Provenance footer | Machine, versions, method, ticket, and the command that reproduces the numbers |

### Non-negotiables

1. **One file, no network.** Guard it, don't trust it:
   `grep -qE '<(script|link)[^>]+(src|href)="https?://' dist/index.html` and
   refuse to publish on a hit. An artifact that needs the network is not an
   artifact.
2. **It must survive a reboot.** Publish to `~/.local/share/<tool>/<slug>/` with
   `versions/<stamp>-<sha>.html`, a `current.html` symlink, a `meta.json`, and a
   prune to the last N — so a bad edit never destroys the last good copy. A
   long-lived artifact whose only copy sits in `/tmp` gets deleted by the OS,
   and if the source lived there too it goes with it. That is not hypothetical:
   it is why the reference implementation was rebuilt from nothing.
3. **Numbers in one file, prose in another.** Numbers change when someone re-runs
   the benchmark; wording changes when someone understands the problem better.
   Those two edits should never collide in one diff. Every figure reads from the
   numbers file, so a re-run updates the charts and the prose's claims together.
4. **Fixed slots.** A new finding *updates or supersedes* a row rather than
   appending a section. Without this rule the artifact grows by accretion into a
   scrapbook — invisible per-commit, obvious at twenty.
5. **Screenshot-safe.** Half of these are consumed as a static image. Nothing
   carrying a value may animate on mount or on `whileInView` (gotchas #11, #13),
   and nothing may depend on hover alone (below).
6. **Guard the type scale in the build.** It reaches eleven sizes with half-pixel
   steps by nobody noticing any single addition.

### Vendoring visual effects

Shader/canvas decoration is worth it and cheap (~35 kB for two), but vendor it
so it stays re-syncable: keep the upstream file's script **verbatim** between
markers and shadow what it reaches for — `window`, `document`, `location`,
`requestAnimationFrame` — with local consts above it. A standalone effect
assumes it owns the viewport and runs until the tab closes; the shim is what
scopes it to a box and gives you `stop()` / `setPaused()`. Pause it offscreen,
never start it under `prefers-reduced-motion`, and read gotchas #16–18 before
you capture, proxy, or trust it.

Placement in a reading document is a design decision, not a taste one: a band
may contain **no data marks** (or its colour starts to look like an encoding),
and text over it reads against a scrim rather than against the animation, since
an animated background has no contrast ratio to have tuned.

### Keeping this file current

This is a living file and the failure mode is drift: a technique gets adopted in
the artifact and never written down, so the next artifact re-derives it. The
rule that prevents it — apply it to yourself at the end of any session that
touched an artifact:

- A **fix that took more than one attempt** becomes a gotcha, with the symptom
  first. The symptom is what someone will search for; the cause is what they
  need after they find it.
- A **decision you had to justify twice** becomes a house-style rule.
- A **number you measured** goes in with its measurement, not rounded to a
  vibe — "544–706px against a 500px viewport" survives scrutiny, "tables are
  too wide" does not.
- If a rule now lives in both this file and the reference implementation's
  README, they must agree. When they drift, the code is right and this file is
  stale.

### Reference implementation

`~/dev/github.com/kevinmichaelchen/pc-bklit` — a unit-test performance
investigation, and the source of most of the hard-won material in this file.
Copy wholesale: `src/components/Tufte.tsx` (the margin-note primitives), the
`.post` grid and margin-note rules in `src/index.css`,
`scripts/check-type-scale.sh`, and `scripts/publish.sh` (three-tier publish with
the external-reference guard). Its `docs/TYPOGRAPHY.md` carries the long-form
reasoning behind the type decisions summarised here.

## The self-contained build (Bklit)

Bklit components are React/TSX installed via the shadcn CLI, so this is a small Vite
build — **not** a hand-written HTML file. The output is still a single shareable file.

```bash
mkdir -p /tmp/chart && cd /tmp/chart
pnpm create vite@latest . --template react-ts
pnpm install
pnpm add tailwindcss @tailwindcss/vite clsx tailwind-merge
pnpm add -D vite-plugin-singlefile @types/d3-shape   # d3-shape types: Bklit needs them or tsc fails

# components.json — register the @bklit namespace, then add components:
#   { "registries": { "@bklit": "https://ui.bklit.com/r/{name}.json" } }
# Add only the top-level charts you need; axes/grid/tooltip/legend/visx come along
# automatically as registry dependencies.
pnpm dlx shadcn@latest add @bklit/bar-chart @bklit/pie-chart @bklit/ring-chart --yes --overwrite
pnpm build     # -> dist/index.html, fully inlined
```

Key config:
- **`vite.config.ts`**: add the `@tailwindcss/vite` plugin, **`viteSingleFile()`** from
  `vite-plugin-singlefile`, `base: "./"`, and the `@` → `./src` resolve alias.
- **`tsconfig`**: set `paths: { "@/*": ["./src/*"] }`. Do **not** set `baseUrl`
  (TS 6 deprecates it → `error TS5101`; `paths` works without it).
- **CSS**: `@import "tailwindcss";` plus a `:root` chart palette
  (`--chart-1..n`, `--chart-line-primary/secondary`, `--foreground`,
  `--muted-foreground`).

### Why singlefile is non-negotiable for sharing

`base: './'` alone is **not** enough. Browsers block external `type="module"` scripts
over `file://` (CORS) — a normal Vite build won't run when double-clicked.
`vite-plugin-singlefile` inlines all JS/CSS into one `index.html` with **inline**
module scripts, which execute fine with no fetches. Verify with:

```bash
grep -oE '(src|href)="https?://[^"]+"' dist/index.html   # should print nothing
```

Then the file drops straight into Slack and works on any machine, offline.

## Check the registry before writing a component

Before hand-rolling a badge, tooltip, disclosure, card or icon: it almost
certainly exists. Query first, write second.

| Need | Where | Install |
|---|---|---|
| Tooltip / hover card / accordion / badge / card / separator | shadcn/ui | `pnpm dlx shadcn@latest add tooltip accordion badge` |
| Charts | Bklit (`@bklit`) | see below |
| Animated icons (440, MIT) | [lucide-animated](https://lucide-animated.com) | register `"@la": "https://lucide-animated.com/r/{name}.json"`, then `add @la/gauge @la/cpu` |
| Animation primitives | [`motion`](https://motion.dev/docs) — MIT, already a Bklit dep | nothing to install |

Notes from doing this:
- Registering namespaces in `components.json` (`"@la"`, `"@bklit"`) beats passing
  raw URLs — a URL list on one `add` line gets mangled by shell word-splitting.
- List what's actually there before guessing names:
  `curl -sL https://lucide-animated.com/r/registry.json | jq -r '.items[].name'`.
  Icons are `<Name>Icon` exports that animate on hover and accept `size`.
- shadcn primitives pull `radix-ui`, and `accordion`/`badge` also want
  `lucide-react` + `class-variance-authority` — `tsc` fails until you add them.
- They resolve colors from Tailwind v4 theme tokens (`bg-popover`,
  `text-muted-foreground`). If you deleted the `@theme inline` block per gotcha
  #2, you must write a **correct** one mapping `--color-*` to your palette, or
  every primitive renders unstyled.
- **Motion UI** (motion.dev/magazine/introducing-motion-ui) is a paid Motion+
  product. The core `motion` library is free and is what you want.

### Query the registry with the MCP, not from memory

shadcn ships both a skill set and an MCP server; install and use them instead of
recalling component names:

```bash
pnpm dlx skills add shadcn/ui                 # -> .agents/skills/shadcn, migrate-radix-to-base
pnpm dlx shadcn@latest mcp init --client claude
npx mcporter config add shadcn "npx shadcn@latest mcp"
npx mcporter call shadcn.search_items_in_registries \
  --args '{"registries":["@shadcn"],"query":"stat metric kpi"}'
```

Two things that will cost you a while otherwise: **mcporter does not read a
project-local `.mcp.json`** — it merges `~/.codex/config.toml`, `~/.claude.json`
and `~/.codeium/…`, so the server needs registering with it separately — and the
search tool returns "No registries are configured" unless `registries` is passed
explicitly in `--args`.

Use it to justify hand-rolling, not to skip it: the KPI tile in the reference
implementation is bespoke *because* that search came back empty. The shadcn
skill also ships enforced rules worth adopting wholesale (`size-*` over
`h-N w-N`, `cn()` over template-literal classNames, semantic tokens over raw
colours).

### Step 0 — check for an official library skill first

Many newer libraries publish their own agent skill. **Install and use it instead of
re-deriving the API from memory.** Bklit's:

```bash
npx skills add bklit/bklit-ui
```

It reads your `components.json`, knows the shadcn install commands, and teaches
composition/theming/animation. Before hand-writing usage for *any* charting library,
check whether it ships a skill (`npx skills add <org>/<name>`) or an `llms.txt`.

## Typography and measure

An artifact is mostly text — an article emphatically so. Two rules carry almost
all of the benefit.

**Never set measure in `ch`.** `1ch` is the advance of the `0` glyph, which in a
proportional UI font is far wider than the average character. Measured with
fontTools against SF Pro over 26k glyphs of real dashboard prose: `0` advance
**0.6064em**, average advance **0.3945em** — a ratio of **1.54**. So
`max-width: 65ch` renders **100 characters**, not 65. It is the fix that looks
right and does nothing. Set measure in `rem` (it also stays elastic to a raised
browser minimum font size, which `px` does not) and treat the character count as
derived. Verify per font:

```python
from fontTools.ttLib import TTFont
f = TTFont("/System/Library/Fonts/SFNS.ttf", fontNumber=0, lazy=True)
upem, hmtx, cmap = f["head"].unitsPerEm, f["hmtx"], f.getBestCmap()
avg = sum(hmtx[cmap[ord(c)]][0] for c in corpus if ord(c) in cmap) / len(corpus) / upem
# chars-per-line = width_px / (avg * font_size_px);  target 50–75, aim 65
```

At 14px that puts the useful band around **21rem (≈60 chars)** for panel prose
and **23rem (≈67 chars)** for a page lede.

**Instance a variable font before you measure it.** `fontTools` hands you the
*default* instance, and for a font with an `opsz` axis that default is very
often not a reading size. `NewYork.ttf`'s default `opsz` is **256** — the display
cut, drawn tight for headlines — and it is 19% narrower than the instance a
browser renders at 18px:

| | avg advance |
|---|---|
| New York @ opsz 256 (fontTools default) | 0.3700em |
| New York @ opsz 18 (what actually renders) | **0.4409em** |
| Georgia | **0.4246em** |

Sizing a column off the default would have shipped a 78-character measure while
the arithmetic claimed 65 — the same class of error as `ch`, arrived at by a
different route.

```python
from fontTools.varLib import instancer
f = instancer.instantiateVariableFont(TTFont(path), {"opsz": 18, "wght": 400})
```

Measure **every** face in the stack, not just the first. A single file with no
webfont is read on machines that have New York and machines that fall back to
Georgia, and a measure correct on only one of them has not been set.

**Set numerals in running prose in the UI sans, not the serif.** Once prose is a
serif and figures are a sans, a number quoted in a sentence and the same number
in the table below it stop looking like the same number — different width,
different colour weight, and old-style figures in some serifs sit below the
baseline. One inline class fixes it: the UI family, `tabular-nums`, `0.92em` to
compensate for the x-height jump, and `white-space: nowrap` so `48.68s` never
breaks. Every quoted figure goes through it.

**If it's a document rather than a dashboard, the numbers change.** A serif at
18px wants ~32rem for 65 characters, and a dashboard scale has no body size at
all — nothing on a dashboard is read for more than a sentence. Adding one is a
scale change, so it goes through whatever guard enforces the scale.

**A full-width panel is wide because its chart is wide, not its prose.** Capping
prose at 21rem inside a 1092px panel glues a ribbon of text to the left edge.
Use two explicit columns gated on whatever `wide` flag the panel already has —
**not** `columns: 21rem`, because that value is a *minimum*, so a 518px half
panel renders one 518px column and silently restores the bug you were fixing.
Give each paragraph `break-inside: avoid`, and keep such panels to exactly two
intro paragraphs or column two comes out empty.

**Check [shadcn Typeset](https://ui.shadcn.com/docs/typeset) before writing prose
CSS.** It is a styling system for *rendered markdown* — arbitrary
`h2`/`ul`/`blockquote`/`table`/`pre` you did not author — generated by a builder
rather than shipped in the registry, so `shadcn add` will not find it. Adopt it
when you are rendering markdown; skip it when your prose is hand-authored `<p>`
and your `<table>`s are bespoke data tables it would restyle. It deliberately
sets no `max-width`, so it never solves measure for you. Two of its rules are
worth stealing regardless:

- **`margin-block-start` only, never `:last-child`/`:has()`/`:empty`.** A
  `:last-child` rule restyles an existing block the moment you append another.
  `:first-child` is safe — it cannot depend on what follows. Verified
  pixel-identical output in a two-column container: Chrome truncates a leading
  margin at a column break, so column tops still align.
- **size / leading / flow as three variables**, with flow relative
  (`0.875em`) rather than a fixed px. A literal derived from WCAG 1.4.8 at one
  line-height quietly drifts under the requirement when the size changes; an em
  keeps the relationship.

Two smaller ones worth the trouble:

- **Collapse the size set.** Eleven sizes with half-pixel steps (10, 10.5, 11,
  11.5 …) is what you get by default; six integers is what you want. No constant
  modular ratio fits a dense dashboard — it needs four steps inside 11–16px where
  all its words live and only two above, which is the inverse of what a geometric
  scale allocates. Chrome truncates fractional sizes while Safari renders
  sub-pixel, so column widths diverge by browser. Guard it in the build.
- **On dark, tune text to APCA Lc, not to WCAG 4.5:1.** WCAG's math over-credits
  light-on-dark, so hitting 4.5:1 lands you on the *placeholder* tier for body
  text. And never dim text with element `opacity` — it cascades to child marks
  and is invisible to every static contrast checker. Animate `color` instead.

## When the artifact has to explain itself

The *how* behind the house style's margin column. Three moves, in order of
payoff:

1. **A labelled plain-language summary at the top**, written to a hard bar: no
   tool names, no file counts, no unit that needs defining. If it survives being
   read aloud to someone outside the team, it passes.
2. **Definitions in the margin, on first use.** A hover tooltip fails two
   audiences at once — it does not exist on touch, and it is invisible in a
   screenshot, which is how these artifacts are usually consumed. Keep the
   tooltip for the *second* encounter; the first one has to be readable without
   a pointing device.
3. **A margin column** — roughly 15rem beside a 32rem text column — for those
   definitions, provenance and asides. Tufte's mechanism is a float with a
   negative inline-end margin plus `clear`, so notes queue instead of
   overlapping, and a hidden checkbox whose label is the superscript handles the
   narrow-screen collapse **with no JavaScript**. That last part matters: the
   behaviour has to survive the file being saved and reopened as a static
   artifact.

Numbering: use a CSS counter (`counter-increment` on the label,
`content: counter(...)` on both the marker and the note) so inserting a note
mid-document renumbers everything after it with nobody maintaining a list.

Reserve *numbered* notes for asides the text points at, and unnumbered ones for
definitions — otherwise a reader who already knows the term gets a superscript
interrupting the sentence for nothing.

**A dotted underline is a promise.** Shipping two of them that look identical
and behave differently — one opening a tooltip, one silently doing nothing
because its definition is already in the margin — reads as a broken tooltip, and
gets reported as one. Honour the promise per breakpoint:

| | margin visible | margin collapsed |
|---|---|---|
| what the reader needs | nothing; the definition is already on screen | the definition, somehow |
| so hovering the word | **lights up its margin note** — also teaches where notes live | opens a real tooltip |
| and the word itself | — | is the `<label>`, i.e. the tap target |

Make the word the label rather than adding a separate ⊕ marker: a glyph-sized
target is a poor one, and the word is the thing being asked about. Scope the
hover through a wrapper (`.note-anchor:hover .marginnote`) — the obvious
sibling selector `~ .marginnote` lights every later note in the paragraph.

## Navigation for a long artifact

Past roughly two screens, an artifact needs a spine the reader can see. Three
rules, all learned by getting them wrong first:

**Render it from the same array the headings render from.** A hand-kept table of
contents does not fail loudly when the article changes — it quietly starts
describing an older version of the page, and nothing in the build catches that.
One `SECTIONS` array of `{ id, n, title, question, short }`; the heading
component and the contents list both consume it. `short` exists because a rail
is ~13rem and section titles are written to be read, not to fit.

**A rail is `position: fixed`, never a grid track.** As a track it re-centres the
article every time it appears or disappears at a breakpoint, and the measure is
the one thing on a reading page that must not move. Pad the page aside by the
rail width instead.

**Derive the breakpoint from what fits, not from a device name.** The rail can
appear only where it does not fight the widest figure: bleed column + rail +
gutters. For a 66rem bleed and a 13rem rail that is ~1300px; below it, a burger
with a slide-in sheet. Note this is a *third* breakpoint, above the one where
margin notes collapse — they are answering different questions and should not be
forced to share a number.

Scroll-spy is worth it and is the one IntersectionObserver on the page that may
safely be racy (gotcha #13): the worst case is an unhighlighted rail, because no
value depends on it. Pick the nearest heading at or above the top of the
viewport — "most visible" makes the highlight jump *backwards* when a tall
figure scrolls past a short section. And the sheet needs the boring parts:
Escape to close, scroll lock while open, a 44px minimum target.

## Charts: choosing a library

Everything from here down is about the figures inside the artifact. If the
deliverable has no charts, you are already done with the parts that matter.

**Don't rank by GitHub stars.** A 60k-star incumbent isn't "better" for being old.
Prefer a **newer, actively maintained** library that clears a low adoption floor
(**~100★ is enough**). Document the incumbents for reference, but bias toward the
newer tier.

**Default pick: [Bklit](https://bklit.com/docs/components)** — a shadcn-registry
component set (visx + d3 + motion under the hood), MIT, actively maintained. Great
defaults, dark-mode tokens, and **18 chart types** (verified 2026-07-24) including
candlestick, gauge, sankey, sunburst, radar, choropleth, ring, and live-line.

Pick something else when the task demands it (see the table). Common swaps:
- **Huge / streaming data** → uPlot (Canvas, ~50KB, 100k+ pts) or a WebGL lib.
- **Financial / OHLC time-series** → TradingView Lightweight Charts.
- **One-off, no build tooling wanted** → a Canvas/SVG lib you can load inline
  (e.g. ECharts) — but see the self-contained rule below.

## Charts: picking a type

Match the chart to the *shape of the question*, not to what looks impressive.

**Start from the question, then look up the component:**

| The question is… | Use |
|---|---|
| "how do these categories rank?" | **Bar** |
| "how did this move over time?" | **Line** → **Area** if magnitude/stacking matters → **Live line** if streaming |
| "how do two different encodings compare on one time axis?" | **Composed** (line + area + bar, shared scale) |
| "what share of the whole?" (few, flat categories) | **Pie** / donut |
| "what share of the whole?" (nested hierarchy) | **Sunburst** |
| "how far toward the goal / inside the safe range?" | **Ring** (progress %) or **Gauge** (value vs. range) |
| "are these two numbers related?" | **Scatter** |
| "where is it dense across two dimensions?" | **Heatmap** |
| "where do people drop off?" | **Funnel** |
| "where does the volume *flow*?" | **Sankey** |
| "how do these options compare across many metrics at once?" | **Radar** |
| "how does it vary by place?" | **Choropleth** |
| "what were open/high/low/close?" | **Candlestick** |

### Bklit's chart catalog

Registry names are what you pass to `shadcn add @bklit/<name>`.

| Chart | `@bklit/…` | Reach for it when… | Example |
|---|---|---|---|
| **Bar** | `bar-chart` | comparing/ranking one metric across discrete categories | per-file test time; slowest tests |
| **Line** | `line-chart` | a metric moves over an ordered/continuous axis (usually time) | CI duration over the last 30 runs |
| **Live line** | `live-line-chart` | the same, but streaming/real-time and self-updating | a live latency/throughput tile |
| **Area** | `area-chart` | a line where magnitude or stacked composition over time matters | cumulative bundle size by chunk |
| **Composed** | `composed-chart` | two encodings share one time axis (e.g. volume bars + a trend line) | runs/day bars + p95 duration line |
| **Scatter** | `scatter-chart` | the relationship/correlation between two numeric variables (and outliers) | test count vs. file duration |
| **Pie** | `pie-chart` | part-to-whole for a *few* (~≤6) flat categories | share of jobs by status |
| **Sunburst** | `sunburst-chart` | part-to-whole where the parts *nest*, with drill-down | workflow → job → step time breakdown |
| **Ring** | `ring-chart` | a single value as progress toward a goal (radial %) | coverage % vs. target |
| **Gauge** | `gauge-chart` | a single value against a range/threshold (radial *or* linear) | cache hit-rate, SLA headroom |
| **Heatmap** | `heatmap-chart` | magnitude/density across a 2-D grid (contribution-graph style) | failures by weekday × hour; a correlation matrix |
| **Funnel** | `funnel-chart` | drop-off through ordered stages of one flow | PR pipeline: opened → checks → merged |
| **Sankey** | `sankey-chart` | quantities *flowing* between nodes / multi-step allocation | where wall-clock time goes across jobs → steps |
| **Radar** | `radar-chart` | comparing a few entities across ~4–8 shared metrics (a profile shape) | service scorecards; before/after on 6 axes |
| **Choropleth** | `choropleth-chart` | a metric varying by geography, with zoom/pan | users or latency by region |
| **Candlestick** | `candlestick-chart` | OHLC per period — any open/high/low/close or range-per-bucket | price; p50–p99 latency band per interval |

Two are **modifiers**, not standalone charts — install them alongside their base:

| Add-on | `@bklit/…` | What it does |
|---|---|---|
| Profit/Loss line | `profit-loss-line` | sign-colors a `LineChart`'s segments (green above zero, red below) — good for deltas/regressions |
| Bar depth | `bar-depth` | 3D/glossy surfaces on `BarChart` bars. Purely decorative; skip for diagnostic charts |

### Primitives worth knowing about

`shadcn add` pulls these in automatically as dependencies, but you have to *compose*
them yourself — and two of them are easy to miss:

- **`reference-area`** — a shaded band in data coordinates. The right way to draw an
  SLA/threshold zone behind a time series.
- **`projection-line`** — extends a line past its last point as a forecast segment.
- Also available: `grid`, `x-axis`, `y-axis`, `chart-tooltip`, `legend`, `markers`,
  `background` (pattern fill when grids are hidden), `chart-animation`.

### KPI blocks (stat cards)

For a dashboard header — big number + sparkline + trend badge, prebuilt:
`stat-card-area-01`, `stat-card-line-01`, `stat-card-choropleth-01`.

Heads-up: unlike the charts, these blocks depend on shadcn's own `card` + `badge`
**and** on `@central-icons-react/all` and `@number-flow/react`. If you only want a
number and a sparkline, composing `chart-stat-flow` + an `area-chart` is lighter.

### Rules of thumb

- **Part-to-whole → Pie/Ring/donut, not a stacked bar.** Bklit bars color
  per-*series*, not per-datum, so a single stacked bar can't give each slice its
  own color (see Gotcha #6). A donut (`PieChart` with `innerRadius`) does, and
  reads cleaner for a handful of proportions.
- **Don't reach for exotic types by default.** Sankey/sunburst/candlestick/radar are
  powerful but easy to misuse — if a bar or line answers the question, use it.
- **Radar lies with unlike units.** Only use it when every axis is normalized to a
  comparable scale (e.g. all 0–100), and keep it to a handful of series.
- **Sunburst and choropleth need hierarchical / geo fixture data.** Confirm you
  actually have (or can derive) parent-child rows or a TopoJSON before promising one.

### Re-verify the catalog before quoting it

The registry is the source of truth and moves faster than this file:

```bash
curl -sL https://ui.bklit.com/r/registry.json \
  | jq -r '.items[] | select(.type=="registry:component") | "\(.name)\t\(.description)"'
```

That printed 32 components on 2026-07-24 — the 18 charts above plus the primitives.
Swap `registry:component` for `registry:block` to list the stat-card blocks. Every
item also carries `registryDependencies` and `dependencies`, which is the honest
answer to "what will this drag in?"

## Verifying a capture

Convert before you look at it: `cwebp -q 72 shot.png -o shot.webp` is ~**5x**
smaller (measured: 189 kB → 36 kB on a dark-UI crop) with no loss of legibility
for checking layout or reading text. Crop to the region of interest first — that
saves more than the codec does. Make it part of the pipeline, not a step to
remember: screenshot → crop → `cwebp` → look.

`timeout` is not on macOS (it is `gtimeout`, from coreutils). A capture command
wrapped in it fails instantly with `command not found`, which looks exactly like
a browser that crashed on startup — and sends you debugging the wrong thing.

## Gotchas (hard-won — save yourself the debugging)

1. **`file://` + ES modules = CORS block.** Use `vite-plugin-singlefile` (above).
2. **`shadcn add` rewrites your `index.css`.** It appends a grayscale `.dark`
   `--chart-*` palette that overrides your colors, plus an `@theme inline` block with
   **malformed quadruple-dash vars** (`var(----chart-1)`). Delete both after adding
   components; keep your own palette in `:root`.
3. **Bklit is visx/d3/motion, not Recharts** — don't assume Recharts props. Import
   from wherever the files land (e.g. `@/components/charts`), which is *not*
   necessarily the `charts` alias you set in `components.json` — check the CLI output.
4. **No barrel `index.ts`** despite docs importing from `@/components/charts` — create
   one that re-exports the components you use.
5. **d3 sub-packages ship without types.** The registry installs `d3-shape`, `d3-array`,
   `d3-scale`, `d3-geo`, `d3-sankey` as runtime deps but never their `@types`, so
   `tsc -b` fails with implicit-any. Add the matching ones as dev deps for the charts
   you picked — `@types/d3-shape` (pie/ring/radar/gauge/line/area), `@types/d3-scale`
   (scatter), `@types/d3-geo` (choropleth), `@types/d3-sankey` (sankey).
6. **Bars color per-series, not per-datum.** For a proportional/phase breakdown where
   each slice needs its own color, use a **Pie/Ring/donut**, not a single stacked bar.
7. **Registry URLs redirect** — `curl` the JSON with `-L`.
8. **Vendored chart code** trips `noUnusedLocals`/`noUnusedParameters` — relax those to
   `false` for the build.
9. **Long axis labels truncate, and `margin.left` does not fix it.** `BarYAxisLabel`
   hardcodes `style={{ maxWidth: 70 }}`, so widening the gutter just adds empty
   space while the text keeps ellipsing. It's vendored code — patch it. The clean
   fix is to default the cap to the gutter you already asked for:
   ```tsx
   // bar-y-axis.tsx — add `labelMaxWidth?: number` to BarYAxisProps, thread it
   // through BarYAxisInner, then:
   labelMaxWidth={labelMaxWidth ?? Math.max(40, margin.left - 12)}
   ```
   Now `margin.left` behaves the way every caller already expects.
10. **Headless screenshots randomly come out with blank charts.** Bklit sizes every
    chart through visx `ParentSize` (ResizeObserver + a 10 ms debounce), and that
    races Chrome's `--virtual-time-budget`: `ChartInner` bails out while
    `width < 10`, so you get a page where all the text and tables are perfect and
    the charts are empty rectangles. Measured ~50% of runs blank at
    `--virtual-time-budget=15000`. It is a **capture artifact, not a render bug** —
    don't go debugging your data or your CSS vars.
    - Use `--headless=new`; old headless produced 0 SVGs every time.
    - Confirm which failure you have by dumping the DOM first:
      `--dump-dom | grep -c '<svg'`. Zero SVGs = never mounted (the race above).
      SVGs present with real `height`/`d` attributes but nothing visible = you're
      looking at a genuine paint/color problem instead.
    - Re-shoot until the bars appear; a rendered PNG is materially larger than a
      blank one, so `stat -f%z` makes a usable retry predicate.
11. **Entrance animation on a headline number makes every screenshot wrong.** A
    count-up from 0 means a capture taken mid-flight renders `3.5s` where the
    value is `66.3s` — and unlike a blank chart, nothing looks broken, so it gets
    shared. Animate on *change* (a filter, a what-if toggle), never on mount:
    `useState(value)` for the initial render, and bail out of the effect when
    `prev.current === value`. Same reasoning as gotcha #10, worse consequences.
12. **`BarYAxis` renders *band* (category) labels, not a numeric scale.** It's for
    `orientation="horizontal"`. Drop it into a vertical bar chart and the category
    names render down the left edge, escaping the chart box and overlapping
    whatever follows. Vertical charts get `BarXAxis` only.

13. **`whileInView` is a screenshot bug waiting to happen.** Any element that
    carries a *value* and animates in on an IntersectionObserver renders at
    `opacity: 0` if the observer hasn't fired — and on a page a few thousand
    pixels tall, a headless capture routinely beats it. A whole heat-map of
    numbers came out blank this way while every static element looked correct.
    Use `animate` (fires on mount) for anything with a value in it. A fade on
    mount is safe because the value is right from the first frame; a count-up is
    not (gotcha #11).

14. **Full-bleed grids need five tracks, not three.** The obvious version —
    `1fr | content | 1fr` with the figure spanning all three — makes a
    full-width figure run flush to the window edge on a narrow viewport, because
    the span includes the page's own gutters. Put the bleed lines *inside* the
    gutter tracks:
    ```css
    grid-template-columns:
      minmax(24px, 1fr)
      [bleed-start] minmax(0, calc((var(--bleed) - var(--content)) / 2))
      [content-start] minmax(0, var(--content))
      [content-end] minmax(0, calc((var(--bleed) - var(--content)) / 2))
      [bleed-end] minmax(24px, 1fr);
    ```
    Padding on the figure is not the fix — it makes `--bleed` mean something
    other than what it says. And when you shrink `--content` at a breakpoint,
    shrink those half-tracks too (`minmax(0, 1fr)`), or they keep claiming their
    old share and starve the content column instead.

15. **`--measure: 100%` at a breakpoint is a regression, not a responsive fix.**
    The instinct once the margin column is gone is to let prose fill the
    viewport. At 760px and 18px that is **96 characters** a line — further past
    the 75 ceiling than the desktop layout ever was. Measure is a property of
    reading, not of available space: keep the width, just stop reserving room
    beside it.

16. **A permanent rAF loop hangs `--virtual-time-budget`.** Add any always-on
    canvas effect and headless capture stops working: virtual time waits for an
    idle the page now never reaches. A full-height shot went from timing out at
    120s to finishing in **3.4s** by adding `--force-prefers-reduced-motion`,
    which is the right capture flag anyway — it also exercises the
    reduced-motion fallback you were supposed to build.

17. **A Proxy over a DOM element needs a `set` trap, not just `get`.** Wrapping
    a canvas to intercept `addEventListener` is a normal move; the failure is
    not. `canvas.width = n` is an accessor on the prototype, and Proxy's default
    `set` forwards with `receiver = the Proxy`, so the native setter gets a
    Proxy as `this` and throws **"Illegal invocation"** — from an assignment
    that looks entirely ordinary, in an effect, which unmounts the React tree
    and leaves a blank page.
    ```js
    new Proxy(el, {
      get(t, p) { const v = t[p]; return typeof v === "function" ? v.bind(t) : v },
      set(t, p, v) { t[p] = v; return true },   // ← not optional
    })
    ```

18. **Decoration must not be able to unmount the page.** Anything vendored and
    purely visual goes in a `try/catch` inside its effect, degrading to a plain
    surface. Also handle the *silent* version: a WebGL effect that returns early
    when `getContext("webgl")` is null leaves an empty canvas where an effect
    was implied, which reads as a bug. Mark it and let CSS collapse the band.

19. **Data tables are what breaks a narrow layout, and they break it silently.**
    `th { white-space: nowrap }` plus any `min-inline-size` prose column gives a
    table a hard minimum width — measured here at 544–706px against a 500px
    viewport. Nothing warns you; the *document* simply starts scrolling
    sideways, which is the worst outcome available, because every line of prose
    drifts off-screen as the reader pans to see a number. Contain it so the
    figure scrolls and the article never does:
    ```css
    @media (max-width: 1080px) { .post-figure, .post-callout { overflow-x: auto } }
    ```
    Verify with a DOM probe rather than by eye —
    `document.documentElement.scrollWidth === clientWidth` is the whole test,
    and walking `body *` for `getBoundingClientRect().right > clientWidth` names
    the culprit in one shot. A screenshot cannot tell you this, for the reason
    in #20.

20. **Headless Chrome clamps the viewport to ~500px wide.** Ask for
    `--window-size=390,…` and you get a 390px *screenshot* of a page laid out at
    **500px** — so the image shows content clipped at the right edge that is not
    actually clipped, and hides real overflow that is. Anything narrower than
    500 has to be checked by measuring the DOM (#19) or through CDP device
    emulation, never from the picture.

## Library reference (2026-07-24 — re-verify stars before quoting)

Newer / preferred tier first, incumbents as reference. Stars drift; ~100★ is the floor.

### Newer / preferred (shadcn-registry, animated, indie — all MIT unless noted)

| Library | ~Stars | Docs | Renderer | Fit | Note |
|---|---|---|---|---|---|
| **Bklit** *(default)* | ~1.4k | bklit.com/docs/components | SVG (visx/d3/motion) | React/Tailwind | shadcn registry; 18 types incl. candlestick/gauge/sankey/sunburst/choropleth; ships `bklit-ui` skill |
| shadcn/ui charts | (in shadcn-ui/ui) | ui.shadcn.com/charts | SVG (Recharts) | React/Tailwind | Copy-paste themed Recharts; huge mindshare |
| Tremor | ~3.5k | tremor.so | SVG | React/Tailwind | Dashboard blocks + KPI cards (Apache-2.0) |
| unovis (F5) | ~2.8k | unovis.dev | SVG+Canvas+WebGL | React/Angular/Svelte/vanilla | Framework-agnostic core; network/map graphs (Apache-2.0) |
| LayerChart | ~1.3k | layerchart.com | SVG+Canvas | Svelte | Composable Svelte; pairs w/ shadcn-svelte |
| Reaviz | ~1.2k | reaviz.dev | SVG+motion | React | Animation-first (Apache-2.0) |
| Liveline | ~836 | benji.org/liveline | Canvas 60fps | React 18+ | Real-time animated line/candlestick, zero-dep, SSR-safe |
| Observable Plot | ~5.3k | observablehq.com/plot | SVG | vanilla | Concise grammar-of-graphics (ISC) |

### Established engines (reference / when scale or ubiquity matters)

| Library | ~Stars | Docs | Renderer | Note |
|---|---|---|---|---|
| Apache ECharts | ~67k | echarts.apache.org | Canvas(+SVG/WebGL) | Huge catalog; CDN-friendly; big-data via progressive + echarts-gl (Apache-2.0) |
| Chart.js | ~68k | chartjs.org | Canvas | Simplest ubiquitous default |
| uPlot | ~10k | github.com/leeoniya/uPlot | Canvas | ~50KB, 100k+ pts instantly — fastest non-WebGL time-series |
| TradingView Lightweight Charts | ~17k | tradingview.github.io/lightweight-charts | Canvas | ~35KB, purpose-built financial/OHLC (Apache-2.0) |
| Plotly.js | ~18k | plotly.com/javascript | SVG+WebGL | Scientific/3D + WebGL big-data |
| deck.gl | ~14k | deck.gl | WebGL2/WebGPU | GPU millions of geospatial pts |
| Perspective (FINOS) | ~9k | perspective.finos.org | WASM+WebGL | Streaming analytics (Arrow/WASM), Apache-2.0 |
| D3 | ~110k | d3js.org | SVG/Canvas | Low-level substrate, not turnkey |

Avoid: **Highcharts / LightningChart JS / SciChart** (commercial licensing);
**Muze** (archived); **Slither Charts** (no discoverable repo — a meme lib where every
mark is a live snake).
