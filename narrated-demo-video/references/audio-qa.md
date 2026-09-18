# Audio QA: finding the source of a noise

You cannot hear the mix. When a listener reports a whine, hiss, pumping, or "mosquito", do not guess and do not
stop at the first plausible culprit. A noise that "comes and goes with the narration" can be the voice, the
ducking, or a coincidence with another layer.

## Isolate before blaming

1. **List every layer and intermediate** with paths, so the listener can check each by ear: each voice line as
   delivered, the music, the ambience, the narration-only track, picture plus voice only, and the final mix.
   The decisive file is *picture plus voice only*: if the noise is there, the bed is innocent.
2. **Measure the voice pauses**: `python3 scripts/pause_bed.py vo/*.mp3`. Anything within 30 dB of the speech
   level is a bed baked into the voice; clean voices measure −35 dB or lower.
3. **Look, per layer, at the band in question**. A whine is a narrow steady tone, so zoom in:

   ```bash
   ffmpeg -i layer.mp3 -lavfi "showspectrumpic=s=1400x600:legend=0:stop=6000" layer.png      # 0–6 kHz
   ffmpeg -t 12 -i final.mp4 -lavfi "showspectrumpic=s=1200x500:legend=0" final-head.png     # full band, first 12 s
   ```

   Steady horizontal lines through pauses are tones (baked-in music, hum). Repeating bright sweeps at 6–9 kHz in
   an ambience track are birdsong or insects. Broadband haze is noise.
4. **Name the pitches.** If the peak frequencies in a pause are musical (392, 494, 988, 1175, 1318, 1568 Hz are
   G, B, B, D, E, G), it is music reproduced by the voice model, not an encoder artifact.
5. When the listener's report and your analysis disagree, **the listener wins**. Re-examine the layer they named.

## Causes seen so far

| Symptom | Cause | Fix |
| --- | --- | --- |
| Thin sustained whine under every line, loudest in pauses | Voice clone reproducing the score from its source footage | Switch to an audited voice. `afftdn` leaves the tones; Demucs only helps the loudest line. |
| Faint high chirring that comes and goes regardless of speech | Bird or insect trills in the ambience | Low-pass the ambience near 5 kHz, pick another stretch, or lower it to about −32 dB. |
| True peak over −1 dBTP after export | Normalising step overshoot | `loudness.py -I -14 --tp -1.5` on the export. |
| A `.mp3` that will not decode | HTML error page saved as audio | Re-fetch with `scripts/fetch_audio.py`. |

Generational loss from the blank-clip round trip (MP3 → AAC → AAC → WAV → AAC) was suspected once and ruled out
by spectrogram: it does not add tones. Do not re-blame it without evidence.

## Reporting

State what was measured, what the spectrogram shows, which layer carries the noise, and what changed in the fix.
Keep the diagnostic images beside the project so the claim can be checked. Then say the new mix still needs a
listen.
