#!/usr/bin/env python3
"""
Match Just Dance songs against the Music library, trim 20s previews.
Skips songs with < 80% match. Respects existing previews.
"""

import json
import os
import re
import subprocess
import sys
from difflib import SequenceMatcher
from collections import defaultdict

MUSIC_DIR = "/home/slaan1974/Documents/Music"
SONGS_FILE = "/home/slaan1974/Documents/justdance/songs.json"
SONGS_OUT_DIR = "/home/slaan1974/Documents/justdance/songs"
MATCH_THRESHOLD = 60


def clean(s):
    """Lowercase, collapse whitespace, remove underscores/hyphens."""
    s = s.lower().strip()
    s = re.sub(r'[_-]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def strip_track(s):
    """Remove leading track numbers/tags."""
    s = re.sub(r'^\d+[\s_\.\-\]]*', '', s)
    s = re.sub(r'^\[\d+\]\s*', '', s)
    return s.strip()


def name_to_tokens(name):
    """Split a filename into meaningful tokens for keyword search."""
    no_ext = re.sub(r'\.mp3$', '', name, flags=re.IGNORECASE)
    cleaned = strip_track(no_ext)
    cleaned = re.sub(r'[\(\)\[\]]', ' ', cleaned)
    cleaned = re.sub(r'[_-]', ' ', cleaned)
    tokens = [t for t in cleaned.lower().split() if len(t) > 1]
    return tokens


def fuzzy_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def main():
    print("=" * 60)
    print("Just Dance — Music Matcher & Trimmer")
    print("=" * 60)

    # Load songs.json
    with open(SONGS_FILE, 'r', encoding='utf-8') as f:
        songs = json.load(f)

    already = sum(1 for s in songs if s.get("preview_url_local"))
    print(f"\nLoaded {len(songs)} entries ({already} already have previews)")

    # Collect unique songs still needing previews
    todo_seen = set()
    todo_indices = []
    for idx, song in enumerate(songs):
        if song.get("preview_url_local"):
            continue
        key = (song.get("artist", "").strip(), song.get("title", "").strip())
        if key in todo_seen:
            continue
        todo_seen.add(key)
        todo_indices.append(idx)

    todo_artists_titles = [(songs[i]["artist"], songs[i]["title"]) for i in todo_indices]
    print(f"Songs needing previews: {len(todo_indices)}")

    # Scan MP3 files
    print("\nIndexing Music library...")
    mp3_entries = []  # (full_path, basename_no_ext, cleaned_lower)
    for root, dirs, files in os.walk(MUSIC_DIR):
        for f in files:
            if f.lower().endswith('.mp3'):
                fp = os.path.join(root, f)
                bn = os.path.splitext(f)[0]
                cl = clean(strip_track(bn))
                mp3_entries.append((fp, bn, cl))

    print(f"Indexed {len(mp3_entries)} MP3 files")

    # Build inverted index: token -> list of indices in mp3_entries
    token_index = defaultdict(list)
    for i, (fp, bn, cl) in enumerate(mp3_entries):
        for tok in name_to_tokens(bn):
            token_index[tok].append(i)

    os.makedirs(SONGS_OUT_DIR, exist_ok=True)

    matched = 0
    skipped_no_match = 0
    skipped_error = 0

    print(f"\n{'='*60}")
    print(f"Matching and trimming...")
    print(f"{'='*60}\n")

    for pos, idx in enumerate(todo_indices, 1):
        artist = todo_artists_titles[pos - 1][0]
        title = todo_artists_titles[pos - 1][1]
        song = songs[idx]

        q_artist = clean(artist)
        q_title = clean(title)
        q_both = clean(f"{artist} {title}")
        q_title_tokens = q_title.split()

        best_idx = None
        best_score = 0
        method = ""

        # ---- Strategy 1: exact substring match on cleaned filename ----
        for fi, (fp, bn, cl) in enumerate(mp3_entries):
            if q_artist in cl and q_title in cl:
                score = 100
                if score > best_score:
                    best_score = score
                    best_idx = fi
                    method = "exact substring"
                    break  # can't beat 100

        # ---- Strategy 2: token-based candidate narrowing + fuzzy ----
        if best_idx is None:
            candidates = set()
            for tok in q_title_tokens:
                if len(tok) > 2 and tok in token_index:
                    for fi in token_index[tok]:
                        candidates.add(fi)
            for fi in candidates:
                fp, bn, cl = mp3_entries[fi]
                score = fuzzy_ratio(q_both, cl) * 100
                if score > best_score:
                    best_score = score
                    best_idx = fi
                    method = f"fuzzy token ({score:.0f}%)"

        # ---- Strategy 3: brute-force fuzzy against ALL (last resort) ----
        if best_idx is None:
            for fi, (fp, bn, cl) in enumerate(mp3_entries):
                score = fuzzy_ratio(q_both, cl) * 100
                if score > best_score:
                    best_score = score
                    best_idx = fi
                    method = f"fuzzy full ({score:.0f}%)"

        pct = pos / len(todo_indices) * 100
        status = f"[{pos:3d}/{len(todo_indices)}] {pct:5.1f}%"

        if best_idx is not None and best_score >= MATCH_THRESHOLD:
            best_file = mp3_entries[best_idx][0]
            matched += 1
            safe_name = re.sub(r'[^\w\-]', '_', f"{artist}_{title}".lower())
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')[:100]
            out_path = os.path.join(SONGS_OUT_DIR, f"{safe_name}.mp3")

            if not os.path.exists(out_path):
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", best_file, "-t", "20",
                         "-y", "-loglevel", "error", out_path],
                        check=True, capture_output=True, text=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"  {status} ✗ FFMPEG ERROR: {artist} - {title}: {e.stderr.strip()[:80]}")
                    skipped_error += 1
                    continue

            song["preview_url_local"] = f"songs/{safe_name}.mp3"
            print(f"  {status} ✓ {artist} - {title} ({method})")
        else:
            skipped_no_match += 1
            print(f"  {status} - {artist} - {title} (no match ≥{MATCH_THRESHOLD}%, best={best_score:.0f}%)")

    # Write updated songs.json
    with open(SONGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    total = sum(1 for s in songs if s.get("preview_url_local"))
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"  Matched & trimmed:  {matched}")
    print(f"  No match (skipped): {skipped_no_match}")
    print(f"  Errors:             {skipped_error}")
    print(f"  Total with preview: {total}")
    print(f"\n✓ Done! songs.json updated.")


if __name__ == "__main__":
    main()
