# Assemble: the ffmpeg chain

Editing runs through [ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (Python, local FFmpeg, no cloud),
reviewed at commit `59f38c15945ba32608bcc2a76d916bcdcc4f3b8d`. Clone that commit under `/tmp` or `.context/`
and pass its path as `--ffmpeg-skill`. Follow its own workflow: plan from `probe.py` numbers, verify with
`check.py`, never overwrite sources (`FFMPEG_SKILL_NO_OVERWRITE=1`).

## The chain `assemble_mix.py` runs

1. `cut.py take.webm --start <head> --end <end mark> --accurate` trims the blank head (about 1.4 s) and converts
   to H.264. Every mark shifts by `head`.
2. For each line, in scene order: gap = line start − end of the previous line. The skill's `pad.py` and
   `fit.py` refuse audio-only input, so route each line through a blank clip:
   `background.py` (clip of the line's length) → `audio.py --replace line.mp3` → `pad.py --start <gap>` →
   `audio.py -o seg.wav`.
3. `join.py seg_*.wav --transition none` butt-joins the segments into one narration track whose lines sit
   exactly on their marks.
4. `audio.py picture.mp4 --replace narration.wav`, then
   `audio.py --music bed.mp3 --duck --music-volume -18 --music-fade-out 4 --effects ambience.mp3 --effects-volume -26`.
   `--effects` is a third bed that is never ducked.
5. `export.py --preset youtube --no-scale --normalize`, then `loudness.py -I -14 --tp -1.5` because the export's
   normalise step can leave the true peak a hair over −1 dBTP.
6. `check.py final.mp4 --platform youtube`. Expect PASS on loudness and true peak. A screen recording at
   1440×900 will FAIL the aspect row (8:5) and WARN on subtitles; both are judgement rows, not defects.

A gap below zero means a line is longer than its scene: re-record with the right durations, shorten the line,
or hold the picture (`freeze.py --at <t> --hold <s>`). Do not overlap lines.

## The short cut: two clips instead of one take

For a 20–30 s demo built from separate clips, fit the picture to the voice after the fact:

- `freeze.py clip.mp4 --at <moment> --hold <seconds>` holds the frame the narration is talking about
  (`--mode extend` holds the last frame).
- Delay a line so a word lands on a moment with the blank-clip route above and `pad.py --start`.
- A slight speed-up is the same route with `fit.py --duration <s> --method speed` (pitch-preserving). Keep it
  under 1.1×.
- `join.py a.mp4 b.mp4 --transition fadeblack --duration 0.8` between beats.

## Gotchas

- **Homebrew FFmpeg has no `drawtext`.** `overlay.py --text`, `look.py`, and contact sheets fail with "No such
  filter". For titles, render a transparent PNG from HTML with `scripts/make_title.mjs` and use
  `overlay.py --image title.png --position top --margin 0 --start 0.3 --end 5 --fade 0.4`.
- **Looking at frames without `look.py`.** Cut one second and export it as a GIF, then view the GIF:
  `cut.py picture.mp4 --start <t> --duration 1 --accurate -o f.mp4` and `export.py f.mp4 --preset gif -o f.gif`.
  A 0.12 s cut is too short; use a full second.
- **An unclosed recording has no duration.** If the recorder crashed, the `.webm` cannot be probed; re-record.
- **zsh does not word-split unquoted variables.** Loops like `for e in "a 1" "b 2"; do set -- $e` silently
  produce wrong file names. Drive multi-file work from Python.
- **Raw `ffmpeg` is for analysis only** (spectrograms, decoding for measurement). Edits go through the skill's
  scripts so their verification still holds.

## Timing targets that felt right

Hold 2–3 s on a key state, 0.8 s fade between separate clips, voice entering 0.3–2 s after the picture, music
−18 dB and ambience −26 dB under the voice, 4 s music fade at the end.
