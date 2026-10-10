# Just Dance Review Hub

A review-ready preview hub for the Just Dance franchise. Browse a searchable catalog of songs from Just Dance 1 through Just Dance 2026 (including DLC), with album art, audio previews, and background music.

## Quick Start

```bash
python3 server.py            # default port: 8006
python3 server.py 9000       # or pass a port explicitly
PORT=8006 python3 server.py  # or set the PORT env var
```

Open `http://localhost:8006` in a browser.

> **Port allocation on the host:** `pong` uses `8000` & `8008`, qBittorrent uses `8080`, so **jd-new uses `8006`**.

## Features

- **Song catalog** — Search and filter a JSON-backed song database by title, artist, game, or year
- **Era filter** — Tag row filters by musical decade (1950s & earlier → 2020s), derived from each song's year
- **Album art** — Full coverage: 793/793 songs have art, with 762 locally cached fallbacks in `album_art/`
- **Audio previews** — 775/793 songs have a 30s preview (Deezer/iTunes sourced, plus 20s local-library trims) with play/pause on each song card
- **Background music** — Looping background track with toggle button
- **Rotating hero background** — Random Unsplash background on every page load
- **Request logging** — Built-in HTTP server logs all requests to `log.txt` (gitignored) with 10 MB rotation and 14-day retention
- **Tests** — `unittest` suite covering the data file and HTTP server (`python -m unittest discover -s tests`)

## Project Structure

| Path | Description |
|------|-------------|
| `server.py` | Custom Python HTTP server with FIFO log rotation |
| `index.html` | Landing page with hero, info cards, and song section |
| `script.js` | Client-side app: song loading, filtering, audio previews |
| `styles.css` | Dark-themed responsive styles |
| `songs.json` | Song catalog (793 entries across Just Dance titles) |
| `songs/` | Local MP3/M4A preview clips (772 files) |
| `album_art/` | Local album art fallback images (762 files) |
| `album_art_mapping.json` | ~4550-entry mapping for album art scraping |
| `background_music/` | Looping background audio track |
| `get_album_art_missing.py` | Fills gaps in album art (Cover Art Archive → MusicBrainz → TheAudioDB → iTunes → Deezer) |
| `get_previews_missing.py` | Fills gaps in audio previews (Deezer → iTunes) |
| `enrich_songs.py` | Populates the `era` field (musical decade) from each song's year |
| `match_and_trim.py` | Matches songs against local Music library and trims 20s previews |
| `tests/test_site.py` | `unittest` suite for songs.json and the HTTP server |
| `log.txt` | Auto-rotating access log (gitignored; 10 MB max, 14-day retention) |

## Data Collection

Album art and audio previews were collected using MusicBrainz and Cover Art Archive APIs. The `match_and_trim.py` script matches songs against a local music library, trims 20-second preview clips, and populates `songs.json` with local paths.

Album art is now at 100% coverage (793/793 songs). The last 49 gaps were closed by `get_album_art_missing.py`, which tries each source in order until one returns a cover:

1. **Cover Art Archive** — re-download when `image_url` is already known
2. **MusicBrainz** — recording search → release → Cover Art Archive front cover
3. **TheAudioDB** — track search → album thumbnail
4. **iTunes Search** — best match for modern singles
5. **Deezer Search** — regional/independent tracks

## Audio Previews

Previews are at 775/793 coverage. The 313 originals were trimmed to 20s from a local Music library by `match_and_trim.py` (Pi only). The remaining gaps were filled by `get_previews_missing.py`, which tries:

1. **Deezer Search** — 30s MP3 preview (saved as `.mp3`)
2. **iTunes Search** — 30s M4A preview (saved as `.m4a`)

Both play natively in browsers, so no ffmpeg/trim step is needed. Match logic normalizes cover artists (`Artist, (Cover Artist)` → `Artist`), drops bracketed qualifiers, and tolerates stylised spellings (`Ke$ha` ↔ `Kesha`). The 18 songs still without a preview are Just Dance original compositions or censored/regional titles that have no commercial release.

```bash
python get_previews_missing.py            # fill all missing previews
python get_previews_missing.py --limit 5  # process only the first 5
python get_previews_missing.py --dry-run  # search + report, do not download
```

## Era Metadata

Every song carries an `era` field derived from its release `year` by `enrich_songs.py`: `1950s & earlier`, then `1960s` … `2020s`. The tag row on the site filters on this field. The script is idempotent and only writes `era` (leaves all other fields alone).

```bash
python enrich_songs.py    # recompute era for every song
```

## Tests

```bash
python -m unittest discover -s tests -v   # or: python tests/test_site.py
```

The suite validates `songs.json` (valid list, 793 entries, required fields, `era` present, and that every referenced album-art/preview file exists) and exercises `server.py` end to end (index, JSON, static assets, and `/log_event` → 204). Standard library only.

## Repository & Sync

| | |
|---|---|
| Remote | `https://github.com/slaan1974/JustDance.git` (branch `main`) |
| Local clone | `C:\Users\slaan\OneDrive\Documents\jd-new` (Windows) |
| Secondary copy | `~/jd-new` on Raspberry Pi 4 (`slaan1974@192.168.178.18`) |
| Served port | `8006` (`pong` uses 8000 & 8008, qBittorrent uses 8080) |

- **Windows → GitHub:** `git add -A && git commit && git push origin main`
- **Windows → Pi (mirror):** `rsync` via WSL. Exclude `.git` (not a repo on the Pi), `log.txt` (keep the Pi's runtime log), and caches/backups; `--delete` syncs removals. Use `--exclude=PATTERN` (no space) so bash won't glob-expand the pattern into extra args:
  ```bash
  wsl -- bash -lc 'rsync -av --delete --exclude=.git --exclude=log.txt \
    --exclude=__pycache__ --exclude=*.pyc --exclude=*.log --exclude=*.bak \
    /mnt/c/Users/slaan/OneDrive/Documents/jd-new/ slaan1974@192.168.178.18:~/jd-new/'
  ```
- **Pi → Windows:** passwordless SSH (ed25519 key installed in `~/.ssh/authorized_keys` on the Pi):
  ```bash
  scp -r slaan1974@192.168.178.18:~/jd-new/. /tmp/pi-jd   # or rsync over ssh
  ```
- **Serve from the Pi:** `cd ~/jd-new && python3 server.py` → `http://192.168.178.18:8006`
- **Pi is not a git repo** — it holds a plain file copy (mirrored from the Windows clone).
- Line endings: system `core.autocrlf=true` on Windows; the repo stores LF.
