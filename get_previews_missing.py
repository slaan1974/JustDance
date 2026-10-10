#!/usr/bin/env python3
"""
Fill songs that have no local audio preview.

Source order per song:
  1. Deezer Search API  -> 30s MP3 preview (downloaded as .mp3).
  2. iTunes Search API  -> 30s M4A preview (downloaded as .m4a).

Both codecs play natively in browsers, so no ffmpeg/trim step is required.
Respects a small delay between requests. Updates songs.json in place
(backup written to songs.json.bak only if it does not already exist).

Usage:
  python get_previews_missing.py            # fill every missing preview
  python get_previews_missing.py --limit 5  # only the first N (dry-run friendly)
  python get_previews_missing.py --dry-run  # search + report, do not download/write
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

try:  # Windows consoles default to cp1252; song titles may be non-Latin
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

UA = {'User-Agent': 'JustDanceBot/1.0 (+justdance.local)'}
SONGS = 'songs.json'
PREVIEW_DIR = 'songs'
MIN_BYTES = 8000  # reject tiny/empty responses


def slugify(artist, title):
    safe = re.sub(r'[^\w\-]', '_', f'{artist}_{title}'.lower())
    return re.sub(r'_+', '_', safe).strip('_')[:100]


def norm(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = text.encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def primary_artist(artist):
    """'The Beach Boys, (The Sunlight Shakers)' -> 'The Beach Boys'."""
    parts = re.split(r'\s*,\s*|\s+ft\.?\s+|\s+feat\.?\s+', artist or '', maxsplit=1, flags=re.I)
    return parts[0].strip()


def clean_title(title):
    """Drop bracket/parenthetical qualifiers: 'Sway (Quien Sera)' -> 'Sway'."""
    t = re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', title or '')
    t = re.sub(r'\s+', ' ', t).strip(' -–—')
    return t or title or ''


def _ratio(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


def is_various(artist):
    return norm(primary_artist(artist)) in ('', 'various artists', 'various')


def artist_ok(artist, got_artist):
    a, ga = norm(primary_artist(artist)), norm(primary_artist(got_artist))
    if not a or not ga:
        return is_various(artist)  # title-only match allowed for VA entries
    if a in ga or ga in a:
        return True
    # tolerate stylised spellings (e.g. "Ke$ha" vs "Kesha")
    return _ratio(a, ga) >= 0.72


def title_ok(title, got_title):
    t, gt = norm(clean_title(title)), norm(clean_title(got_title))
    if not t or not gt:
        return False
    if t in gt or gt in t:
        return True
    return _ratio(t, gt) >= (0.85 if is_various(title) else 0.7)


def matches(artist, title, got_artist, got_title):
    """Tolerant artist+title agreement (handles covers, stylised names, VA)."""
    t, gt = norm(clean_title(title)), norm(clean_title(got_title))
    if not t or not gt:
        return False
    if is_various(artist):  # junk artist; require a strongly-matching title
        return t in gt or gt in t or _ratio(t, gt) >= 0.9
    if not title_ok(title, got_title):
        return False
    return artist_ok(artist, got_artist)


def candidate_queries(artist, title):
    """Search strings to try, most specific first."""
    pa = primary_artist(artist)
    ct = clean_title(title)
    queries = [f'{pa} {title}', f'{pa} {ct}', f'{artist} {ct}', ct]
    seen, out = set(), []
    for q in queries:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise urllib.error.HTTPError(url, r.status, 'bad status', r.headers, None)
        return r.read()


def get_json(url, timeout=20):
    return json.loads(get(url, timeout=timeout))


def find_preview_deezer(artist, title, year=None):
    """Deezer Search API -> 30s mp3 preview URL."""
    for query in candidate_queries(artist, title):
        url = 'https://api.deezer.com/search?q=' + urllib.parse.quote(query)
        try:
            results = get_json(url).get('data', [])
        except Exception:
            continue
        for r in results[:10]:
            if matches(artist, title, r.get('artist', {}).get('name'), r.get('title')):
                preview = r.get('preview')
                if preview:
                    return preview
    return None


def find_preview_itunes(artist, title, year=None):
    """iTunes Search API -> 30s m4a preview URL."""
    for query in candidate_queries(artist, title):
        url = ('https://itunes.apple.com/search?term=' +
               urllib.parse.quote(query) + '&entity=song&limit=10')
        try:
            results = get_json(url).get('results', [])
        except Exception:
            continue
        for r in results:
            if matches(artist, title, r.get('artistName'), r.get('trackName')):
                preview = r.get('previewUrl')
                if preview:
                    return preview
    return None


def download(url, path):
    data = get(url, timeout=45)
    if len(data) < MIN_BYTES:
        raise ValueError(f'preview too small ({len(data)} bytes)')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    return path


def build_todo(songs):
    """One work item per unique (artist, title) still missing a preview."""
    seen = set()
    todo = []
    for s in songs:
        if s.get('preview_url_local') and os.path.isfile(s['preview_url_local']):
            continue
        key = (norm(s.get('artist')), norm(s.get('title')))
        if not key[0] or not key[1] or key in seen:
            continue
        seen.add(key)
        todo.append((s['artist'], s['title']))
    return todo


def apply_to_all(songs, artist, title, path):
    """Assign a found preview to every song sharing this artist+title."""
    key = (norm(artist), norm(title))
    n = 0
    for s in songs:
        if (norm(s.get('artist')), norm(s.get('title'))) == key:
            s['preview_url_local'] = path
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='only process first N songs')
    ap.add_argument('--dry-run', action='store_true', help='search only, do not download or write')
    args = ap.parse_args()

    with open(SONGS, encoding='utf-8') as f:
        songs = json.load(f)

    have = sum(1 for s in songs
               if s.get('preview_url_local') and os.path.isfile(s['preview_url_local']))
    todo = build_todo(songs)
    print(f'{len(songs)} songs total, {have} with a local preview, '
          f'{len(todo)} unique tracks to look up')

    if args.limit:
        todo = todo[:args.limit]

    done = failed = 0
    for i, (artist, title) in enumerate(todo, 1):
        pct = i / len(todo) * 100 if todo else 100
        prefix = f'  [{i:3d}/{len(todo)}] {pct:5.1f}%'

        preview = src = None
        for name, fn in (('deezer', find_preview_deezer),
                         ('itunes', find_preview_itunes)):
            try:
                preview = fn(artist, title)
            except Exception as e:
                print(f'{prefix} {name} error: {e}')
                preview = None
            time.sleep(0.5)
            if preview:
                src = name
                break

        if not preview:
            failed += 1
            print(f'{prefix} - {artist} - {title} (no preview)')
            continue

        if args.dry_run:
            done += 1
            print(f'{prefix} [{src}] {artist} - {title}')
            continue

        ext = '.mp3' if src == 'deezer' else '.m4a'
        target = os.path.join(PREVIEW_DIR, slugify(artist, title) + ext).replace('\\', '/')
        try:
            download(preview, target)
        except Exception as e:
            failed += 1
            print(f'{prefix} download failed [{src}]: {e}')
            continue

        n = apply_to_all(songs, artist, title, target)
        done += 1
        print(f'{prefix} OK [{src}] {artist} - {title} -> {target} ({n} song(s))')

    if args.dry_run:
        print(f'\nDry run: {done} found, {failed} not found. No files written.')
        return 0

    if not os.path.exists(SONGS + '.bak'):
        with open(SONGS + '.bak', 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)

    with open(SONGS, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    still = sum(1 for s in songs
                if not s.get('preview_url_local') or not os.path.isfile(s['preview_url_local']))
    print(f'\nDone: {done} filled, {failed} failed, {still}/{len(songs)} still missing')
    return 1 if still else 0


if __name__ == '__main__':
    sys.exit(main())
