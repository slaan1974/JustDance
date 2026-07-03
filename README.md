# Just Dance Review Hub

A review-ready preview hub for the Just Dance franchise. Browse a searchable catalog of songs from Just Dance 1 through Just Dance 2015 (including DLC), with album art, audio previews, and background music.

## Quick Start

```bash
python3 server.py [port]   # default port: 8000
```

Open `http://localhost:8000` in a browser.

## Features

- **Song catalog** — Search and filter a JSON-backed song database by title, artist, game, or year
- **Album art** — Remote Cover Art Archive images with local fallback; ~714 locally cached covers
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
| `songs.json` | Song catalog (720+ entries across Just Dance titles) |
| `songs/` | Local MP3 preview clips (~310 files) |
| `album_art/` | Local album art fallback images (~714 files) |
| `album_art_mapping.json` | ~4550-entry mapping for album art scraping |
| `background_music/` | Looping background audio track |
| `get_album_art*.py` | Scrapers for MusicBrainz/Cover Art Archive/Spotify album art |
| `match_and_trim.py` | Matches songs against local Music library and trims 20s previews |
| `log.txt` | Auto-rotating access log (10 MB max, 14-day retention) |

## Data Collection

Album art and audio previews were collected using MusicBrainz and Cover Art Archive APIs. The `match_and_trim.py` script matches songs against a local music library, trims 20-second preview clips, and populates `songs.json` with local paths.
