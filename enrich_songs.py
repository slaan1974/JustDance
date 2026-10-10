#!/usr/bin/env python3
"""
Populate the `era` field for every song from its release `year`.

Era buckets are musical decades; everything before 1960 is grouped as
"1950s & earlier". The script is idempotent (re-running rewrites the same
values) and leaves all other fields untouched.

Usage: python enrich_songs.py
"""

import json
import os
import sys

SONGS = 'songs.json'


def era_from_year(year):
    try:
        y = int(year)
    except (TypeError, ValueError):
        return 'Other'
    if y < 1960:
        return '1950s & earlier'
    return f'{(y // 10) * 10}s'


def main():
    with open(SONGS, encoding='utf-8') as f:
        songs = json.load(f)

    changed = 0
    for s in songs:
        era = era_from_year(s.get('year'))
        if s.get('era') != era:
            s['era'] = era
            changed += 1

    if not os.path.exists(SONGS + '.bak'):
        with open(SONGS + '.bak', 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)

    with open(SONGS, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    counts = {}
    for s in songs:
        counts[s['era']] = counts.get(s['era'], 0) + 1
    print(f'{changed} songs updated. Era distribution:')
    for era in sorted(counts):
        print(f'  {era:<18} {counts[era]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
