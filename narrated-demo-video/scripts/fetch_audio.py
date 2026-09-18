#!/usr/bin/env python3
"""Download an audio file and refuse anything that is not audio.

Some music hosts answer a bare client with an HTML error page that saves happily as `.mp3`.
This sends a browser user agent and checks the first bytes before keeping the file.

Usage: fetch_audio.py URL OUTPUT
Python standard library only.
"""
import sys
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0 Safari/537.36"
)


def looks_like_audio(head: bytes) -> bool:
    if head[:3] == b"ID3":  # MP3 with ID3 tag
        return True
    if len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:  # MPEG audio frame sync
        return True
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return True
    if head[:4] in (b"OggS", b"fLaC"):
        return True
    if head[4:8] == b"ftyp":  # MP4 / M4A
        return True
    return False


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    url, output = sys.argv[1], sys.argv[2]
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if not looks_like_audio(data[:16]):
        preview = data[:120].decode("utf-8", "replace").replace("\n", " ")
        print(f"refused: response is not audio ({len(data)} bytes): {preview}")
        return 1
    with open(output, "wb") as handle:
        handle.write(data)
    print(f"saved {output} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
