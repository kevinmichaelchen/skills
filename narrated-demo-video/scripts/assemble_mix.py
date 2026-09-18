#!/usr/bin/env python3
"""Assemble a narrated, scored demo from a take, its marks, and the narration lines.

Runs the chain documented in references/mixing.md through ffmpeg-skill's scripts:
trim the take, place each narration line on its mark, replace the audio, add a ducked music
bed and an optional ambience layer, export, then bring loudness and true peak into range.

Usage:
  assemble_mix.py --ffmpeg-skill DIR --take take.webm --marks marks.json --lines vo/ \
      --out out/demo.mp4 [--head 1.4] [--music bed.mp3] [--ambience forest.mp3] \
      [--music-volume -18] [--ambience-volume -26] [--music-fade-out 4] [--preset youtube]

`--lines` holds one audio file per narration line plus durations.json ({"<key>": seconds}); each key
needs a "vo:<key>" mark, and the marks need an "end". Python standard library only.
"""
import argparse
import json
import pathlib
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ffmpeg-skill", required=True, help="checkout of kajisho5/ffmpeg-skill")
    parser.add_argument("--take", required=True)
    parser.add_argument("--marks", required=True)
    parser.add_argument("--lines", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--head", type=float, default=1.4, help="seconds trimmed from the start of the take")
    parser.add_argument("--music")
    parser.add_argument("--ambience")
    parser.add_argument("--music-volume", default="-18")
    parser.add_argument("--ambience-volume", default="-26")
    parser.add_argument("--music-fade-out", default="4")
    parser.add_argument("--preset", default="youtube")
    args = parser.parse_args()

    scripts = pathlib.Path(args.ffmpeg_skill) / "scripts"
    out = pathlib.Path(args.out)
    work = out.parent / f"{out.stem}-work"
    work.mkdir(parents=True, exist_ok=True)
    lines_dir = pathlib.Path(args.lines)

    def run(script: str, *argv: str) -> dict:
        result = subprocess.run(["python3", str(scripts / script), *argv, "--json-brief"], capture_output=True, text=True)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            sys.exit(f"{script}: unreadable output\n{result.stdout[:400]}\n{result.stderr[-400:]}")
        if payload.get("status") != "completed":
            sys.exit(f"{script} failed: {payload.get('error')}")
        return payload

    marks = {m["name"]: m["ms"] / 1000 for m in json.loads(pathlib.Path(args.marks).read_text())["marks"]}
    durations = json.loads((lines_dir / "durations.json").read_text())
    if "end" not in marks:
        sys.exit('marks.json has no "end" mark')

    picture = work / "picture.mp4"
    run("cut.py", args.take, "--start", str(args.head), "--end", str(marks["end"]), "--accurate", "-o", str(picture))

    cursor, segments = 0.0, []
    for key in sorted(durations):
        if f"vo:{key}" not in marks:
            sys.exit(f'no "vo:{key}" mark for narration line {key}')
        source = next((p for p in sorted(lines_dir.glob(f"{key}.*")) if p.suffix != ".json"), None)
        if source is None:
            sys.exit(f"no audio file for narration line {key} in {lines_dir}")
        start = marks[f"vo:{key}"] - args.head
        gap = round(start - cursor, 3)
        if gap < 0:
            sys.exit(f"line {key} would overlap the previous line by {-gap:.2f}s; shorten it, re-record, or hold the picture")
        # pad.py and fit.py refuse audio-only input, so each line rides a blank clip while it is padded
        blank, voiced, padded, segment = (work / f"{key}-{n}" for n in ("blank.mp4", "voiced.mp4", "padded.mp4", "seg.wav"))
        run("background.py", "-o", str(blank), "--duration", str(durations[key]), "--width", "320", "--height", "180")
        run("audio.py", str(blank), "--replace", str(source), "-o", str(voiced))
        run("pad.py", str(voiced), "--start", str(gap), "-o", str(padded))
        run("audio.py", str(padded), "-o", str(segment))
        segments.append(str(segment))
        cursor = start + durations[key]
        print(f"{key}: starts {start:6.2f}s (gap {gap:5.2f}s, line {durations[key]:5.2f}s)")

    narration = work / "narration.wav"
    run("join.py", *segments, "--transition", "none", "-o", str(narration))
    voiced_picture = work / "picture-vo.mp4"
    run("audio.py", str(picture), "--replace", str(narration), "-o", str(voiced_picture))

    scored = voiced_picture
    if args.music:
        scored = work / "scored.mp4"
        mix = [str(voiced_picture), "--music", args.music, "--duck", "--music-volume", args.music_volume, "--music-fade-out", args.music_fade_out]
        if args.ambience:
            mix += ["--effects", args.ambience, "--effects-volume", args.ambience_volume]
        run("audio.py", *mix, "-o", str(scored))

    exported = work / "export.mp4"
    run("export.py", str(scored), "--preset", args.preset, "--no-scale", "--normalize", "-o", str(exported))
    final = run("loudness.py", str(exported), "-I", "-14", "--tp", "-1.5", "-o", str(out))
    print("final:", final.get("summary"))
    print(f"isolate layers for QA: {voiced_picture} (voice only), {scored} (voice + bed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
