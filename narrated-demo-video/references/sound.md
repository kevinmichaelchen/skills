# Bed: music and ambience

## Proven picks

These two sat well together under a British documentary voice and are the default unless the brief says otherwise.

| Layer | Track | Source | License | Credit |
| --- | --- | --- | --- | --- |
| Music | **Borealis**, Scott Buckley: slow, contemplative ambient with a slight lift | `https://www.scottbuckley.com.au/library/wp-content/uploads/2019/09/sb_borealis.mp3` (page: `https://www.scottbuckley.com.au/library/borealis/`) | CC BY 4.0 | Required: `'Borealis' by Scott Buckley - released under CC-BY 4.0. www.scottbuckley.com.au` |
| Ambience | **Forest ambience**, audiopapkin | `https://pixabay.com/sound-effects/nature-forest-ambience-296528/` | Pixabay Content License | Not required; a courtesy credit is kind |

Pixabay downloads need a browser session, so ask the user to download the ambience file and give you its path.
The forest track carries bird trills around 7–8 kHz. At −26 dB they are faint texture; if a listener objects,
low-pass the ambience near 5 kHz or start it from a quieter stretch.

For a bigger payoff beat, Scott Buckley's **Sentinel** (heroic hybrid orchestral) works under a success moment:
`https://www.scottbuckley.com.au/library/wp-content/uploads/2024/04/Sentinel.mp3`. Others worth auditioning from
the same library: Penumbra, Echoes Of Home, Starfire.

## Other sources

| Source | License | Attribution | Notes |
| --- | --- | --- | --- |
| Scott Buckley, `scottbuckley.com.au/library` | CC BY 4.0 | One line, printed on each track page | Cinematic ambient and orchestral; direct MP3 per track, no account. |
| Kevin MacLeod, `incompetech.com` | CC BY 4.0 | Ready-made block per track | Orchestral picks: "Serene", "Noble Race". JavaScript-driven site; download from the track page. |
| Pixabay Music and Sound Effects | Pixabay Content License | None | Quality varies; usually wants a free account. |
| Musopen | Public domain recordings | None | Real orchestral classical; edit it down yourself. |
| Free Music Archive, ccMixter | Per track | Per track | Use CC BY or CC0 only. Anything tagged NC is out for a product demo. |
| YouTube Audio Library | Standard license is contested off YouTube | — | Only its CC BY tracks are safe when the video lives anywhere else. |

## Fetching

`scottbuckley.com.au` sits behind Mod_Security and answers a bare `curl` with an HTML "Not Acceptable!" page
that saves happily as `.mp3`. Use:

```bash
python3 <skill-dir>/scripts/fetch_audio.py <url> music/bed.mp3
```

It sends a browser user agent and refuses to keep a response that is not audio.

## Licensing record

Beside each downloaded file, write a small note: track, artist, license, exact attribution text, source URL,
download date. CC BY credit must be **visible** wherever the video is published (description, PR body, end
card); an HTML comment does not count.

## Levels that worked

Voice at reference; music 18 dB under it with auto-ducking and a 3–4 s fade-out; ambience 26 dB down and never
ducked, so it breathes steadily under everything. Normalise the finished mix to −14 LUFS with true peak at or
below −1.5 dBTP.
