#!/usr/bin/env python3
"""
Optimized album art collection using MusicBrainz API
- Respects MusicBrainz rate limits (1 request per second)
- Uses fallback search strategies
- Processes 100+ songs for good coverage
"""

import json
import urllib.request
import urllib.error
from urllib.parse import quote
import sys
import time

# Load existing songs
with open('songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

# Collect unique songs by (artist, title)
unique_songs = {}
for song in songs:
    key = (song['artist'], song['title'])
    if key not in unique_songs:
        unique_songs[key] = song

print(f"Loaded {len(unique_songs)} unique songs")
print(f"Using improved search strategies with proper rate limiting\n")

results = []
failed = []

print(f"Searching {len(unique_songs)} songs...\n")

for idx, (artist, title) in enumerate(sorted(unique_songs.keys()), 1):
    sys.stdout.write(f"\r[{idx:3d}/{len(unique_songs)}]", )
    sys.stdout.flush()
    
    found = False
    
    # Strategy 1: Direct artist + title search
    if not found:
        try:
            search_query = f'artist:"{artist}" recording:"{title}"'
            url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=10'
            
            req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceBot/1.0 (+justdance.local)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('recordings'):
                    for recording in data['recordings'][:3]:
                        if recording.get('releases'):
                            for release in recording['releases'][:5]:
                                release_id = release.get('id')
                                if release_id and not found:
                                    try:
                                        cover_url = f'https://coverartarchive.org/release/{release_id}/front-250.jpg'
                                        req_cover = urllib.request.Request(cover_url, method='HEAD')
                                        with urllib.request.urlopen(req_cover, timeout=5) as r:
                                            if r.status == 200:
                                                results.append({
                                                    "image_url": cover_url,
                                                    "album_title": release.get('title', 'Unknown'),
                                                    "artist": artist,
                                                    "song_hint": title
                                                })
                                                found = True
                                                break
                                    except:
                                        pass
        except:
            pass
    
    # Strategy 2: Simpler search
    if not found:
        try:
            search_query = f'{title} artist:{artist}'
            url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=3'
            
            req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceBot/1.0 (+justdance.local)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('recordings') and data['recordings'][0].get('releases'):
                    for release in data['recordings'][0]['releases'][:3]:
                        release_id = release.get('id')
                        if release_id and not found:
                            try:
                                cover_url = f'https://coverartarchive.org/release/{release_id}/front-250.jpg'
                                req_cover = urllib.request.Request(cover_url, method='HEAD')
                                with urllib.request.urlopen(req_cover, timeout=5) as r:
                                    if r.status == 200:
                                        results.append({
                                            "image_url": cover_url,
                                            "album_title": release.get('title', 'Unknown'),
                                            "artist": artist,
                                            "song_hint": title
                                        })
                                        found = True
                                        break
                            except:
                                pass
        except:
            pass
    
    if not found:
        failed.append((artist, title))
    
    # Respect MusicBrainz rate limiting: 1 request per second
    time.sleep(1.2)

print(f"\n\n" + "="*75)
print(f"RESULTS: {len(results)} songs with album art found")
print(f"SUCCESS RATE: {len(results)*100//len(unique_songs)}%")
print("="*75)

# Save results
output_file = 'album_art_mapping.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(results)} complete mappings to {output_file}")

# Show samples
if results:
    print("\n" + "="*75)
    print("SAMPLE RESULTS (first 15):")
    print("="*75)
    for i, item in enumerate(results[:15], 1):
        print(f"{i:2d}. {item['song_hint'][:40]:40s} - {item['artist'][:30]:30s}")
        print(f"    Album: {item['album_title'][:60]}")

print("\n✓ Complete! Ready to use with your app.")
