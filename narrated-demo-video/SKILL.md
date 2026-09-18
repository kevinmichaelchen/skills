---
name: narrated-demo-video
description: Narrated product demo videos with a documentary feel — generated British voice-over (Fish Audio through Executor), a CC-licensed score and ambience bed, a Playwright screen take paced to the narration, and an artifact-free ffmpeg mix. Use when asked for a demo video or screen recording with voice-over, a "Planet Earth" or Attenborough feel, music or ambience for a demo, narration added to an existing recording, or to find the source of noise in generated narration.
---

# Narrated Demo Video

**Voice first.** The narration sets the clock: write and generate the lines, measure them, then record one
continuous **take** that waits for each line, and lay every line on the **mark** where its scene began. Freezing
frames afterwards is the fallback, not the plan.

You cannot hear. Every audio claim you make must rest on a measurement or a spectrogram, and the final report
must say the mix still needs human ears and name what to listen for.

## Contract first

When `skillspec` is available, run [`skill.spec.yml`](skill.spec.yml) with the task before acting, and use
[`deps.toml`](deps.toml) for dependency evidence. Work under `.context/demo/` (gitignored); media never enters
source control.

## Workflow

1. **Beat sheet.** List the scenes, the on-screen action in each, and one narration line per scene. Budget
   1.5–1.9 spoken words per second and let speech fill at most three quarters of the runtime (a 60 s video is
   about 75–85 words). Build context before the payoff: arrive, browse, decide, act, result.
   Done when every scene has an action, a line, and a word count, and the total fits the target length.

2. **Voice.** Read [references/voice.md](references/voice.md) before choosing or generating a voice. Generate
   **one** line, audit it, and only then generate the rest:

   ```bash
   python3 <skill-dir>/scripts/pause_bed.py vo/*.mp3        # fails any line whose pauses sit within 30 dB of the speech
   ```

   Done when every line exists as its own file, every line passes the audit, and `vo/durations.json` holds
   each line's measured duration.

3. **Bed.** Read [references/sound.md](references/sound.md) when choosing music or ambience. Fetch with
   `scripts/fetch_audio.py` (it rejects HTML error pages saved as `.mp3`).
   Done when each track's license, attribution line, and source URL are written down beside the file.

4. **Take.** Read [references/recording.md](references/recording.md) before writing the recorder. Build it on
   [`scripts/recorder_kit.mjs`](scripts/recorder_kit.mjs): scripted cursor, human-paced typing, smooth
   scrolling, and `mark()` / `waitForLine()` so each scene holds until its line has finished.
   Done when `marks.json` has a mark for every line plus `end`, the flow's real outcome is confirmed outside the
   browser (API response, database row), and no credential or personal address appears on screen.

5. **Assemble.** Read [references/mixing.md](references/mixing.md) for the chain and its gotchas, then:

   ```bash
   python3 <skill-dir>/scripts/assemble_mix.py --ffmpeg-skill <ffmpeg-skill-dir> \
     --take take/video.webm --marks take/marks.json --lines vo --head 1.4 \
     --music music/bed.mp3 --ambience music/ambience.mp3 --out out/demo.mp4
   ```

   Done when the platform check passes loudness (−14 ± 2 LUFS) and true peak (≤ −1 dBTP) and the duration
   matches the take.

6. **Verify.** Pull one frame from inside each key moment (mixing.md shows how without `drawtext`) and look at
   it. If anything sounds wrong to the user, follow [references/audio-qa.md](references/audio-qa.md): isolate
   the layer before blaming one.
   Done when every key moment has a viewed frame and the report states what was measured versus what needs ears.

7. **Publish.** `gh pr edit <n> --attach <file>` (gh ≥ 2.100) uploads a real attachment and embeds a player; if
   the CLI appends the asset URL instead of rewriting your inline reference, move the URL into place and drop
   the duplicate. Put each required credit line in visible text beside the video, say plainly which steps were
   staged, and delete any saved sign-in state.
   Done when the published page plays the new file, shows the credits, and no token-bearing file remains.

## Non-negotiables

- Never commit media, and never host it on a branch.
- Never ship a voice you have not audited; community voice clones can carry the score of the footage they were
  cloned from.
- Never speed narration up by more than 10 %; shorten the line or hold the picture instead.
- Never show a login form, password, or personal email on camera; sign in off camera and start the take from
  the saved state.
- Never present a staged step as real. If the product cannot do a step yet, drive it another way and disclose it
  wherever the video is published.
- Never drop a CC BY credit or hide it in a comment.
