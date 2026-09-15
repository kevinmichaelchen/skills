# Provider Comparison: Exa, Parallel, Firecrawl, TinyFish

Evidence snapshot for `web-research-router` routing decisions. Gathered
2026-09-10 from each vendor's pricing and benchmark pages (sources at the
bottom). Load this file when choosing between overlapping providers, when the
user asks "why this tool", or when pricing or quality matters to the decision.
Re-verify prices before quoting them; all four vendors change pricing often.

## The rule of thumb

All four sell "search", "fetch", and some form of "agent". Differentiate on
**what the vendor built first**. Each provider's core product is where quality
is highest and pricing is most rational; the bolt-on features are thinner or
cost more.

| Vendor | Built first | Quality edge | Pricing model | Weak spot |
|---|---|---|---|---|
| Exa | Its own web index and embedding models | Semantic and "find similar" retrieval; sub-200 ms search tier | Per request. Search $7/1k, Contents $1/1k pages, Deep Search $12-15/1k, Agent $0.012-$1.00/run, Monitors $15/1k | No structured extraction; deep queries consume variable credits |
| Parallel | Agentic research tasks with citations and confidence | Best accuracy per dollar on fact-seeking questions | Per request. Search $0.001-$0.005, Extract $0.001, Responses $0.01-$0.25, Task $0.005-$2.40, Monitor $0.003-$0.01, FindAll $0.03-$1 per match | Slowest raw search latency; no browser interaction |
| Firecrawl | Scraping and crawling with JS rendering | Extraction fidelity, crawl/map/download, open source, most reliable task completion | Flat credits on a subscription. 1 credit = 1 page; search 2 credits/10 results; interact 2 credits/browser minute; JSON/question formats +4 credits/page; Standard $83/mo for 100k | Search relevance ranks last of the four in every third-party test; unused credits do not roll over below Scale |
| TinyFish | Browser agent that completes tasks on live sites | Web-agent task completion by a wide margin; fastest search; cleanest fetch output in its own eval | Search and Fetch are free (500 searches/hr, 1,000 fetches/day). Agent $0.016/step, Browser $0.002/min from a prepaid wallet | Newest and smallest index; benchmarks are self-published |

## Quality: claims that survive two sources

Every vendor publishes benchmarks it wins. These are the findings that hold up
across at least two hostile sources, or that a competitor concedes.

- **Parallel wins on accuracy for fact-seeking research.** Parallel's own
  SimpleQA Verified run (2026-09-09) reports Parallel Advanced and Basic at
  97 percent versus Exa Auto at 91 percent and Perplexity at 94-95 percent.
  TinyFish's independent SimpleQA end-to-end run ties Parallel with TinyFish at
  the top (86.8 percent), ahead of Exa (83.6) and Firecrawl (80.0).
- **TinyFish and Exa win on latency.** TinyFish's p50 search figure is about
  556 ms, Exa about 811 ms, Firecrawl about 869 ms, Parallel about 1,709 ms.
  Exa's own page claims sub-180 ms for its Instant tier. Parallel launched
  "Search Fast" in 2026-09 to close this gap, so re-measure before relying on
  this ordering.
- **TinyFish wins on browser agents by a wide margin.** Online-Mind2Web:
  TinyFish 89.9 percent versus Gemini 2.5 Computer Use 69.0, OpenAI Operator
  61.3, Claude Computer Use 56.3. WebVoyager: TinyFish 91.1 versus BrowserUse
  88.3. Firecrawl's interact product is not on either leaderboard.
- **Firecrawl leads on reliability, not relevance.** On BrowseComp it completed
  96/100 tasks without timeout or error (TinyFish 95, Exa 93, Parallel 91,
  built-in tools 63), but ranked last on whether the first search result
  contained enough evidence to answer (38.4 percent, tied with Exa).
- **Exa's differentiator is not on any of these benchmarks.** Semantic
  discovery, "find pages like this one", and the people, company, and scholarly
  indexes are things the others do not offer. Firecrawl's own comparison page
  concedes this and positions Exa as the choice for "conceptually similar
  content".
- **Fetch quality.** TinyFish's own eval of "pages returned as usable context"
  puts TinyFish at 93 percent, Tavily 80, Exa 73, Firecrawl 62, Parallel 58.
  Self-published, so treat as directional.

Caveats. TinyFish's page is dated 2026-07; Parallel's was run 2026-09-09. Both
are vendor-run and neither includes the other vendors' newest tiers. Gaps under
five points are noise.

## Price: three different models

Direct per-request comparison is misleading because the billing units differ.

- **Firecrawl is a subscription with flat credits.** Monthly bill is known in
  advance, JS rendering costs nothing extra, and deep searches never spike.
  Poor fit for bursty or very low-volume use because credits expire monthly
  below the Scale tier. Pay-as-you-go top-ups exist on paid plans.
- **Exa and Parallel are pay-as-you-go per request.** Parallel basic search is
  roughly $1-5 per 1k requests versus Exa's $7 per 1k. Extract is about $1 per
  1k on both. They diverge on deep work: a Parallel Task run tops out at $2.40,
  an Exa Agent run at $1.00. Parallel's benchmark page reports cost including
  LLM tokens (CPM), which is the number that matters inside an agent loop.
- **TinyFish gives Search and Fetch away.** Free at 30/min and 500/hr for
  search, 150/min and 1,000/day for fetch, with no wallet draw and no card. Only
  Agent (per step) and Browser (per minute) are metered. For Kevin's volume this
  makes TinyFish the cheapest possible search-and-fetch path.
- **Monitoring is cheapest on Parallel.** Roughly $3-10 per 1k checks, versus
  Exa Monitors at $15 per 1k and Firecrawl at 7 credits per page per check.

## Routing consequences

These are the decisions encoded in `skill.spec.yml` and `SKILL.md`:

| Intent | Route | Why |
|---|---|---|
| "Find pages about X" / "pages like this URL" | Exa | Only semantic index of the four |
| "What is the answer, with sources" | Parallel Search + Extract, or Parallel Task for multi-step | Best accuracy per dollar; citations and confidence returned |
| Clean markdown, crawls, docs mirrors, JSON schemas | Firecrawl | Extraction fidelity, predictable cost |
| "Log in, click through, fill the form, get the result" | TinyFish Agent | Only one of the four whose core product is completing browser tasks |
| Fetch a single known URL | TinyFish Fetch first, then Parallel Extract | Free and highest usable-context score; Parallel is the paid fallback when Executor is unavailable |
| Recurring monitoring | Parallel Monitor | Cheapest per check by a wide margin |

## Sources

- Exa pricing: https://exa.ai/pricing
- Exa positioning (index size, latency claims): https://exa.ai/
- Parallel pricing: https://parallel.ai/pricing
- Parallel benchmarks (SimpleQA Verified, BrowseComp, WideSearch): https://parallel.ai/benchmarks
- Firecrawl pricing: https://www.firecrawl.dev/pricing
- Firecrawl vs Exa (vendor comparison): https://www.firecrawl.dev/alternatives/firecrawl-vs-exa
- TinyFish pricing: https://www.tinyfish.ai/pricing
- TinyFish benchmarks: https://www.tinyfish.ai/benchmarks

Raw scrapes from the 2026-09-10 collection were kept under
`.context/vendor-compare/` in the working checkout and are not committed.
