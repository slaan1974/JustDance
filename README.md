# Just Dance Review Hub

A review-ready preview hub for the Just Dance franchise. Browse a searchable catalog of songs from Just Dance 1 through Just Dance 2026 (including DLC), with album art, audio previews, and background music.

## Quick Start

```bash
python3 server.py [port]   # default port: 8000
```

Open `http://localhost:8000` in a browser.

## Features

- **Song catalog** — Search and filter a JSON-backed song database by title, artist, game, or year
- **Album art** — Full coverage: 793/793 songs have art, with 762 locally cached fallbacks in `album_art/`
- **Audio previews** — ~310 trimmed 20s MP3 previews with play/pause on each song card
- **Background music** — Looping background track with toggle button
- **Rotating hero background** — Random Unsplash background on every page load
- **Request logging** — Built-in HTTP server logs all requests to `log.txt` with 10 MB rotation and 14-day retention

## Project Structure

| Path | Description |
|------|-------------|
| `server.py` | Custom Python HTTP server with FIFO log rotation |
| `index.html` | Landing page with hero, info cards, and song section |
| `script.js` | Client-side app: song loading, filtering, audio previews |
| `styles.css` | Dark-themed responsive styles |
| `songs.json` | Song catalog (793 entries across Just Dance titles) |
| `songs/` | Local MP3 preview clips (~310 files) |
| `album_art/` | Local album art fallback images (762 files) |
| `album_art_mapping.json` | ~4550-entry mapping for album art scraping |
| `background_music/` | Looping background audio track |
| `get_album_art*.py` | Scrapers for MusicBrainz/Cover Art Archive/Spotify album art |
| `get_album_art_missing.py` | Fills gaps in album art (Cover Art Archive → MusicBrainz → TheAudioDB → iTunes → Deezer) |
| `match_and_trim.py` | Matches songs against local Music library and trims 20s previews |
| `log.txt` | Auto-rotating access log (10 MB max, 14-day retention) |

## Data Collection

Album art and audio previews were collected using MusicBrainz and Cover Art Archive APIs. The `match_and_trim.py` script matches songs against a local music library, trims 20-second preview clips, and populates `songs.json` with local paths.

Album art is now at 100% coverage (793/793 songs). The last 49 gaps were closed by `get_album_art_missing.py`, which tries each source in order until one returns a cover:

1. **Cover Art Archive** — re-download when `image_url` is already known
2. **MusicBrainz** — recording search → release → Cover Art Archive front cover
3. **TheAudioDB** — track search → album thumbnail
4. **iTunes Search** — best match for modern singles
5. **Deezer Search** — regional/independent tracks

## Repository & Sync

| | |
|---|---|
| Remote | `https://github.com/slaan1974/JustDance.git` (branch `main`) |
| Local clone | `C:\Users\slaan\OneDrive\Documents\jd-new` (Windows) |
| Secondary copy | `~/jd-new` on Raspberry Pi 4 (`slaan1974@192.168.178.18`) |

- **Windows → GitHub:** `git add -A && git commit && git push origin main`
- **Pi → Windows:** passwordless SSH (ed25519 key installed in `~/.ssh/authorized_keys` on the Pi):
  ```bash
  scp -r slaan1974@192.168.178.18:~/jd-new/. /tmp/pi-jd   # or rsync over ssh
  ```
- **Pi is not a git repo** — it holds a plain file copy. As of 2026-10-08 all 1044 files were verified byte-identical to GitHub (only `README.md` and `TEST.md` exist solely in git).
- Line endings: system `core.autocrlf=true` on Windows; the repo stores LF.
