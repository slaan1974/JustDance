# Testing Guide

Manual test checklist for the Just Dance Review Hub.

---

## 1. HTTP Server

```bash
# Start default port
python3 server.py

# Start custom port
python3 server.py 9090
```

| Test | Expected |
|------|----------|
| Server starts without errors | Prints "Server started on port 8000" |
| `log.txt` created in project root | File exists and is writable |
| Server responds on `http://localhost:8000` | 200, serves `index.html` |
| Custom port works | `python3 server.py 9090` → `localhost:9090` |
| `/log_event` endpoint | `curl "http://localhost:8000/log_event?action=test"` → 204 No Content |
| Log captures events | Check `log.txt` for `USER_EVENT` entries |
| Ctrl+C stops server | Prints "Server stopped" and exits cleanly |

## 2. Front-end

Open `http://localhost:8000` in a browser.

| Test | Expected |
|------|----------|
| Page loads | Hero section visible with title "Just Dance Review Hub" |
| Debug banner | Shows "songs ready" or "failed to load songs" |
| Background image | Random concert/dance image fills viewport |
| "New background" button | Cycles to a different Unsplash image |
| Song grid renders | Cards with title, artist, album art, and metadata appear |
| Search box | Type "blinding" — only matching songs shown |
| Era tags | Click "Classic pop" — grid filters to that era; click "All" resets |
| Album art fallback | Disconnect network — local `album_art/` images load instead |
| Audio preview | Hover a song card with preview, click ▶ — audio plays; click ⏹ — stops |
| Background music toggle | Click 🔇 bottom-right — music plays (🔊); click again — stops (🔇) |
| Mobile layout | Resize browser < 880px — layout stacks vertically |

## 3. Data Validation

```bash
# Validate songs.json is well-formed
python3 -m json.tool songs.json > /dev/null && echo "OK" || echo "FAIL"

# Count entries
python3 -c "import json; print(len(json.load(open('songs.json'))))"

# Check all local image files exist
python3 -c "
import json, os
songs = json.load(open('songs.json'))
missing = [s for s in songs if s.get('image_url_local') and not os.path.isfile(s['image_url_local'])]
print(f'{len(missing)} songs with missing album art')
"

# Check all local preview files exist
python3 -c "
import json, os
songs = json.load(open('songs.json'))
missing = [s for s in songs if s.get('preview_url_local') and not os.path.isfile(s['preview_url_local'])]
print(f'{len(missing)} songs with missing previews')
"

# Album art mapping size
python3 -c "import json; d=json.load(open('album_art_mapping.json')); print(f'{len(d)} mappings')"
```

## 4. Data Collection Scripts

Run each script from the project root. They scrape MusicBrainz / Cover Art Archive for album art and populate or update `songs.json`.

| Script | Purpose |
|--------|---------|
| `python3 get_album_art.py` | Basic MusicBrainz + Cover Art Archive scrape |
| `python3 get_album_art_enhanced.py` | Enhanced version with retries |
| `python3 get_album_art_parallel.py` | Multi-threaded scraping |
| `python3 get_album_art_final.py` | Final pass to fill remaining gaps |
| `python3 get_album_art_spotify.py` | Spotify-backed art lookup |

```bash
# Dry-run check that each script imports cleanly
for f in get_album_art*.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print(f'$f: syntax OK')"
done
```

## 5. Preview Trim Script

```bash
# Match songs against Music library and trim 20s previews
python3 match_and_trim.py

# Check output directory
ls songs/ | wc -l    # should match preview_url_local count in songs.json
```

## 6. Suggested Tooling

- **`curl`** — Test server endpoints and response codes
- **Browser DevTools** (F12) — Console for JS errors, Network tab for 404s, Sources for breakpoints
- **`python3 -m json.tool`** — Validate JSON files
- **Lighthouse / PageSpeed** — Performance and accessibility audit
- **`pytest`** (optional) — If scripts grow complex, wrap server and data validation in automated tests
