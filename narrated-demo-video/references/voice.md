# Voice: Fish Audio through Executor

## Reaching Fish

Fish Audio is an Executor integration (`fish_mcp`). Inside the Executor `execute` tool, discover the live paths
rather than guessing them:

```ts
const { items } = await tools.search({ namespace: "fish_mcp", query: "text to speech voice", limit: 20 });
const F = items[0].path.split(".").slice(0, 3).join("."); // e.g. fish_mcp.<owner>.<connection>; never hard-code it
```

| Tool | Use |
| --- | --- |
| `search_voices({ query, language, sort_by: "task_count" })` | Find voices. Prefer a high `task_count`. Returns ids and a `sample_audio` URL. |
| `get_voice({ voice_id })` | Tags, languages, sample, demo text. |
| `text_to_speech({ text, voice_id, language })` | Returns a permanent `audio_url` and `credits_charged`. One identical retry within 5 minutes is free. |
| `get_credit_balance({})` | Plan, remaining credits, per-call text limit. |
| `studio_enhance_text({ text })` | Free; expands numbers and adds delivery tags. |

The result's text content is JSON: parse it for `audio_url`. Cost is about one credit per byte of text, so a
whole 60 s script is a few hundred credits. Download with `scripts/fetch_audio.py`.

The MCP tool takes **no speed or prosody argument**. Fish's REST API has `prosody.speed` (0.5–2.0); through
Executor, pacing is controlled in the text and, as a last resort, in post.

## Voices that have been audited

| Voice | Id | Quietest pause vs speech | Verdict |
| --- | --- | --- | --- |
| David Attenborough Dramatic | `eabac87f2d8b47f1b174e7d2f685618a` | −36 to −50 dB across seven lines | **Use this.** British, measured, about 1.9 words/s. Shipped in a finished demo. |
| Documentary | `c3958f083c2d407982263c77cfa831e3` | −66 dB (one line) | Clean. Untested beyond one line. |
| Sir David Attenborough | `0ae05cee781a4783b5dcf50e8a08711d` | −39 dB (one line) | Clean enough. Untested beyond one line. |
| Paddington, British narrator | `5e79e8f5d2b345f98baa8c83c947532d` | −28 dB | Fails: audible bed. |
| Narrator | `0327fdb5da9e4fd782899a8058c8ae2b` | −21 dB | Fails: audible bed. |
| David Attenborough | `c39a76f685cf4f8fb41cd5d3d66b497d` | −18 to −28 dB (one line −34) | **Do not use.** Reproduces a sustained musical chord under the speech; reads as a mosquito whine. About 1.5 words/s. |

Audit results drift as voices are retrained; re-run the audit rather than trusting this table for a new project.

## The audit, and why it exists

Community clones made from documentary footage learn the score that sat under the original narration and
reproduce it: steady tones at musical pitches (G, B, D…) with slight vibrato, loudest in the pauses. Nothing in
the request asks for it, and Fish does not generate music.

1. Generate one representative line (12–20 words, at least one ellipsis or full stop so there is a pause).
2. `python3 scripts/pause_bed.py line.mp3` — the quietest fifth of a second must sit **30 dB or more** below
   the speech RMS. Clean voices measure −35 dB or lower; the bad one measured −18 dB.
3. Look at 0–6 kHz:
   `ffmpeg -i line.mp3 -lavfi "showspectrumpic=s=1400x600:legend=0:stop=6000" line.png`.
   Horizontal lines that run straight through the pauses are music. Clean speech has dark gaps.
4. Only then generate the remaining lines, and audit them all. The bed varies line to line: the bad voice had one
   line that passed at −34 dB while six failed, so a single passing line does not clear a voice.

What does not fix a bad voice: `afftdn` noise reduction (it is music, not noise; the tones survive and stand out
more), and Demucs vocal separation (it rescued the loudest line and left the rest untouched). Switch voice.

## Writing lines

- One line per scene, 12–20 words. Short sentences carry weight: "Authorised. Captured."
- Punctuation is the pacing tool: ellipses and commas add pauses; a colon sets up a reveal.
- Land a word on a moment: end the line on the thing that happens ("…and chooses a plan." as the click lands).
- British spelling nudges British delivery ("tokenised", "authorised").
- The S1 model reads `(parenthesised)` emotion tags; they were not needed for a documentary register.
- Keep names of real products and numbers speakable; run `studio_enhance_text` if a line has digits or symbols.

Pacing numbers from real runs: 99 words ran 52 s with the Dramatic voice and 66 s with the slower clone. A 28 s
two-beat demo used 51 words; an 85 s seven-beat journey used 99.

## Duration bookkeeping

After downloading, probe every line and write `vo/durations.json` as `{ "1_arrive": 6.24, … }` with keys that
sort in scene order. The recorder reads it to pace scenes; `assemble_mix.py` reads it to place lines.
