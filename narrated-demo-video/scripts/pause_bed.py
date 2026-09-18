#!/usr/bin/env python3
"""Audit generated narration for a bed baked into the voice.

For each file, finds the quietest fifth of a second (a pause) and reports its level relative to the
speech RMS. Clean text-to-speech pauses sit 35 dB or more below the speech; a voice clone that
reproduces background music sits much closer (a bad one measured -18 to -28 dB). Audit every line:
the bed varies, and one quiet line does not clear a voice.

Usage: pause_bed.py [--threshold -30] FILE [FILE ...]
Exit status is 1 when any file's pause level is above the threshold. Needs ffmpeg on PATH.
Python standard library only.
"""
import argparse
import array
import math
import subprocess
import sys
import tempfile
import wave

WINDOW_S = 0.2  # short enough to fit between sentences; a half-second window misreads lines with no long pause
HOP_S = 0.05
EDGE_S = 0.3  # ignore the file's own lead-in and tail silence


def decode(path: str) -> tuple[int, array.array]:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", tmp.name],
            check=True,
        )
        with wave.open(tmp.name) as wav:
            samples = array.array("h")
            samples.frombytes(wav.readframes(wav.getnframes()))
            return wav.getframerate(), samples


def rms(values) -> float:
    total = 0
    count = 0
    for v in values:
        total += v * v
        count += 1
    return math.sqrt(total / count) if count else 0.0


def measure(path: str) -> tuple[float, float]:
    rate, samples = decode(path)
    window, hop, edge = int(WINDOW_S * rate), int(HOP_S * rate), int(EDGE_S * rate)
    if len(samples) < window + 2 * edge:
        raise ValueError("file is shorter than the analysis window")
    # prefix sums of squares make each window O(1)
    prefix = [0]
    for v in samples:
        prefix.append(prefix[-1] + v * v)
    quietest, at = None, 0
    for start in range(edge, len(samples) - window - edge, hop):
        energy = prefix[start + window] - prefix[start]
        if quietest is None or energy < quietest:
            quietest, at = energy, start
    pause = math.sqrt(quietest / window)
    speech = rms(samples)
    relative = 20 * math.log10(max(pause, 1e-9) / max(speech, 1e-9))
    return relative, at / rate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--threshold", type=float, default=-30.0, help="dB relative to speech; pauses must be at or below this")
    args = parser.parse_args()

    failed = False
    for path in args.files:
        try:
            relative, at = measure(path)
        except (subprocess.CalledProcessError, ValueError, wave.Error) as error:
            print(f"ERROR {path}: {error}")
            failed = True
            continue
        verdict = "ok  " if relative <= args.threshold else "FAIL"
        failed = failed or relative > args.threshold
        print(f"{verdict} {path}: quietest {WINDOW_S}s at {at:.1f}s is {relative:.1f} dB vs speech (limit {args.threshold:.0f})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
