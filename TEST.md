# Testing Guide

Manual test checklist for the Just Dance Review Hub. An automated suite lives in `tests/test_site.py` (see section 6).

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
| Era tags | Click "2010s" — grid filters to that decade; click "All" resets |
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

# Check all local image files exist (expected: 0)
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

# Preview coverage (expected: 775/793 with a preview, 0 broken refs)
python3 -c "
import json
songs = json.load(open('songs.json'))
print(f\"{sum(1 for s in songs if s.get('preview_url_local'))}/{len(songs)} songs have previews\")
"

# Album art mapping size
python3 -c "import json; d=json.load(open('album_art_mapping.json')); print(f'{len(d)} mappings')"
```

## 4. Data Collection Scripts

Run each script from the project root.

| Script | Purpose |
|--------|---------|
| `python3 get_album_art_missing.py` | Fills any song still missing local art (Cover Art Archive → MusicBrainz → TheAudioDB → iTunes → Deezer) |
| `python3 get_previews_missing.py` | Fills any song still missing an audio preview (Deezer → iTunes); supports `--limit N` and `--dry-run` |
| `python3 enrich_songs.py` | Populates the `era` field (musical decade) from each song's `year` |

```bash
# Check that each script parses cleanly
for f in get_album_art_missing.py get_previews_missing.py enrich_songs.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print(f'$f: syntax OK')"
done

# Re-check coverage (expected: 0 songs with missing album art)
python3 get_album_art_missing.py   # exits 0 when coverage is complete
```

## 5. Preview Scripts

```bash
# Match songs against local Music library and trim 20s previews (Pi only)
python3 match_and_trim.py

# Download 30s previews for any songs still missing one (Deezer -> iTunes)
python3 get_previews_missing.py --dry-run   # report what would be found
python3 get_previews_missing.py             # download + update songs.json

# Check output directory
ls songs/ | wc -l    # unique preview files (fewer than song count when tracks repeat)
```

## 6. Automated Tests

```bash
# Run the whole suite from the project root (standard library only)
python3 -m unittest discover -s tests -v    # or: python3 tests/test_site.py
```

Covers `songs.json` (valid list, 793 entries, required fields, `era` present, all album-art/preview files exist) and `server.py` (index, `/songs.json`, static assets, `/log_event` → 204).

## 7. Suggested Tooling

- **`curl`** — Test server endpoints and response codes
- **Browser DevTools** (F12) — Console for JS errors, Network tab for 404s, Sources for breakpoints
- **`python3 -m json.tool`** — Validate JSON files
- **`unittest`** — The built-in suite in `tests/`
- **Lighthouse / PageSpeed** — Performance and accessibility audit
