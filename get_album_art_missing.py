#!/usr/bin/env python3
"""
Fill the remaining songs that have no local album art.

Source order per song:
  1. Existing Cover Art Archive URL (image_url already set) - just download.
  2. MusicBrainz recording search -> release -> Cover Art Archive front cover.
  3. TheAudioDB track search -> album thumb.
  4. iTunes Search API -> artwork.
  5. Deezer Search API -> album cover.

Respects MusicBrainz rate limits (1 request per second).
Updates songs.json in place (backup written to songs.json.bak if absent).
"""

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

UA = {'User-Agent': 'JustDanceBot/1.0 (+justdance.local)'}
ART_DIR = 'album_art'
SONGS = 'songs.json'
TADB_KEY = '123'  # public test key


def slugify(text):
    return re.sub(r'_+', '_', re.sub(r'[^a-z0-9]+', '_', text.lower())).strip('_')


def norm(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = text.encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def matches(artist, title, got_artist, got_title):
    a, t, ga, gt = norm(artist), norm(title), norm(got_artist), norm(got_title)
    if not (t and gt):
        return False
    words_a = a.split()
    words_ga = ga.split()
    artist_ok = (a in ga or ga in a or
                 bool(words_a) and bool(words_ga) and
                 (words_a[0] == words_ga[0] or
                  set(words_a[:2]) & set(words_ga[:2])))
    return artist_ok and (t in gt or gt in t or
                          len(set(t.split()) & set(gt.split())) >= max(1, min(len(t.split()), 2)))


def local_path(artist, title, url):
    seed = hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
    return f'{ART_DIR}/{slugify(artist + "_" + title)}_{seed}.jpg'


def get(url, method='GET', timeout=15):
    req = urllib.request.Request(url, method=method, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise urllib.error.HTTPError(url, r.status, 'bad status', r.headers, None)
        return r.read() if method == 'GET' else b''


def get_json(url, timeout=15):
    return json.loads(get(url, timeout=timeout))


def download(url, path):
    data = get(url, timeout=30)
    if len(data) < 500:
        raise ValueError(f'image too small ({len(data)} bytes)')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    return path


def caa_cover(release_id):
    url = f'https://coverartarchive.org/release/{release_id}/front-250.jpg'
    try:
        get(url, method='HEAD', timeout=8)
        return url
    except Exception:
        return None


def find_cover_musicbrainz(artist, title, year=None):
    queries = [f'artist:"{artist}" recording:"{title}"',
               f'{title} AND artist:{artist}',
               title]
    for query in queries:
        api = ('https://musicbrainz.org/ws/2/recording?query=' +
               urllib.parse.quote(query) + '&fmt=json&limit=10')
        try:
            data = get_json(api)
        except Exception:
            time.sleep(1.2)
            continue
        time.sleep(1.2)

        recs = data.get('recordings', [])
        if year:  # prefer releases from the song's year
            recs = sorted(recs, key=lambda r: 0 if any(
                str(rel.get('date', '')).startswith(str(year))
                for rel in r.get('releases', [])) else 1)

        for rec in recs[:6]:
            credit = json.dumps(rec.get('artist-credit', [])).lower()
            if artist.lower() not in credit:
                continue
            for rel in rec.get('releases', [])[:8]:
                cover = caa_cover(rel.get('id', ''))
                if cover:
                    return cover, rel.get('title')
    return None, None


def find_cover_audiodb(artist, title, year=None):
    """TheAudioDB: track search -> album id -> album thumb."""
    try:
        data = get_json('https://www.theaudiodb.com/api/v1/json/' + TADB_KEY +
                        '/searchtrack.php?s=' + urllib.parse.quote(artist) +
                        '&t=' + urllib.parse.quote(title))
    except Exception:
        return None, None

    tracks = data.get('track') or []
    if not tracks:
        return None, None
    track = tracks[0]
    if artist.lower() not in (track.get('strArtist') or '').lower():
        return None, None

    album_id = track.get('idAlbum')
    album = None
    if album_id:
        try:
            res = get_json('https://www.theaudiodb.com/api/v1/json/' + TADB_KEY +
                           '/album.php?m=' + album_id)
            albums = res.get('album') or []
            album = albums[0] if albums else None
        except Exception:
            album = None

    if not album:
        try:
            res = get_json('https://www.theaudiodb.com/api/v1/json/' + TADB_KEY +
                           '/searchalbum.php?s=' + urllib.parse.quote(artist) +
                           '&a=' + urllib.parse.quote(track.get('strAlbum') or ''))
            albums = res.get('album') or []
            album = albums[0] if albums else None
        except Exception:
            return None, None

    if not album:
        return None, None

    thumb = album.get('strAlbumThumbHQ') or album.get('strAlbumThumb')
    if thumb:
        return thumb, album.get('strAlbum')
    return None, None


def find_cover_itunes(artist, title, year=None):
    """iTunes Search API - good coverage for modern singles."""
    url = ('https://itunes.apple.com/search?term=' +
           urllib.parse.quote(f'{artist} {title}') + '&entity=song&limit=10')
    try:
        results = get_json(url).get('results', [])
    except Exception:
        return None, None
    for r in results:
        if matches(artist, title, r.get('artistName'), r.get('trackName')):
            art = r.get('artworkUrl100', '')
            return art.replace('100x100bb', '600x600bb'), r.get('collectionName')
    return None, None


def find_cover_deezer(artist, title, year=None):
    """Deezer Search API - last resort for regional/independent tracks."""
    url = ('https://api.deezer.com/search?q=' +
           urllib.parse.quote(f'{artist} {title}'))
    try:
        results = get_json(url).get('data', [])
    except Exception:
        return None, None
    for r in results[:10]:
        album = r.get('album', {})
        if matches(artist, title, r.get('artist', {}).get('name'), r.get('title')):
            cover = album.get('cover_xl') or album.get('cover_big') or album.get('cover_medium')
            if cover:
                return cover, album.get('title')
    return None, None


def main():
    with open(SONGS, encoding='utf-8') as f:
        songs = json.load(f)

    missing = [s for s in songs
               if not s.get('image_url_local') or not os.path.isfile(s['image_url_local'])]
    print(f'{len(missing)} songs missing local album art: '
          f'{sum(1 for s in missing if s.get("image_url"))} with known URL, '
          f'{sum(1 for s in missing if not s.get("image_url"))} to look up')

    done = failed = 0

    # 1) download covers whose URL is already known
    for s in missing:
        url = s.get('image_url')
        if not url:
            continue
        target = s.get('image_url_local') or local_path(s['artist'], s['title'], url)
        if target.startswith('album_art/') and not target.endswith('.jpg'):
            target += '.jpg'
        try:
            download(url, target)
            s['image_url_local'] = target
            done += 1
            print(f'  [caa]   {s["title"]} - {s["artist"]}')
        except Exception as e:
            failed += 1
            print(f'  [FAIL]  {s["title"]} - {s["artist"]}: {e}')

    # 2) + 3) look up the rest
    todo = [s for s in songs
            if not s.get('image_url_local') or not os.path.isfile(s['image_url_local'])]
    for i, s in enumerate(todo, 1):
        title, artist, year = s['title'], s['artist'], s.get('year')
        print(f'  [{i}/{len(todo)}] {title} - {artist}', flush=True)

        cover = album = src = None
        for name, fn in (('mb', find_cover_musicbrainz),
                         ('tadb', find_cover_audiodb),
                         ('itunes', find_cover_itunes),
                         ('deezer', find_cover_deezer)):
            try:
                cover, album = fn(artist, title, year)
            except Exception as e:
                print(f'    {name} error: {e}')
                cover = album = None
            time.sleep(1.2)
            if cover:
                src = name
                break

        if not cover:
            failed += 1
            print('    no cover found')
            continue

        target = local_path(artist, title, cover)
        try:
            download(cover, target)
            s['image_url'] = cover
            s['image_url_local'] = target
            if album:
                s['album_title'] = album
            done += 1
            print(f'    OK [{src}] {album or ""} -> {target}')
        except Exception as e:
            failed += 1
            print(f'    download failed: {e}')

    if not os.path.exists(SONGS + '.bak'):
        with open(SONGS + '.bak', 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)
    with open(SONGS, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    still = sum(1 for s in songs
                if not s.get('image_url_local') or not os.path.isfile(s['image_url_local']))
    print(f'\nDone: {done} filled, {failed} failed, {still} still missing')
    return 1 if still else 0


if __name__ == '__main__':
    sys.exit(main())
