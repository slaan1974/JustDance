#!/usr/bin/env python3
"""
Fast album art collection using Spotify Web API (no auth required for basic search)
"""

import json
import urllib.request
import urllib.error
import time
from urllib.parse import quote
import sys

# Load existing songs
with open('songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

# Collect unique songs by (artist, title)
unique_songs = {}
for song in songs:
    key = (song['artist'], song['title'])
    if key not in unique_songs:
        unique_songs[key] = song

print(f"Loaded {len(unique_songs)} unique songs\n")

# Load what we already have from MusicBrainz
try:
    with open('album_art_mapping.json', 'r', encoding='utf-8') as f:
        existing = json.load(f)
    existing_songs = {(e['artist'], e['song_hint']) for e in existing}
    print(f"Loaded {len(existing)} existing entries from MusicBrainz\n")
except:
    existing = []
    existing_songs = set()
    print("No existing entries found\n")

# Remaining songs to process
remaining_songs = [(artist, title) for artist, title in unique_songs.keys() if (artist, title) not in existing_songs]
print(f"Will search for {len(remaining_songs)} remaining songs\n")

results_from_spotify = []

print("="*75)
print("Searching Spotify API for album art (up to 100 songs)...")
print("="*75 + "\n")

for idx, (artist, title) in enumerate(sorted(remaining_songs)[:100], 1):  # Limit to 100 for fast demo
    sys.stdout.write(f"[{idx:3d}] '{title[:25]:25s}' by {artist[:28]:28s} -> ")
    sys.stdout.flush()
    
    found = False
    
    try:
        # Spotify search API (no auth required for basic search)
        search_query = f'track:{title} artist:{artist}'
        url = f'https://open.spotify.com/search?q={quote(search_query)}&type=track'
        
        # Try alternative API endpoint that may not require auth
        # Use the web API directly
        api_url = f'https://api.spotify.com/v1/search?q={quote(search_query)}&type=track&limit=1'
        
        req = urllib.request.Request(api_url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('tracks', {}).get('items'):
                    track = data['tracks']['items'][0]
                    
                    # Get album info
                    if track.get('album'):
                        album = track['album']
                        album_title = album.get('name', 'Unknown')
                        
                        # Get image
                        if album.get('images') and len(album['images']) > 0:
                            # Get medium-sized image (usually at index 1)
                            image_url = album['images'][min(1, len(album['images'])-1)].get('url')
                            
                            results_from_spotify.append({
                                "image_url": image_url,
                                "album_title": album_title,
                                "artist": artist,
                                "song_hint": title
                            })
                            print(f"✓ {album_title[:35]:35s}")
                            found = True
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("⚠ Spotify API requires authentication")
            else:
                print(f"✗ HTTP {e.code}")
    
    except Exception as e:
        pass
    
    if not found:
        print("- not found")
    
    time.sleep(0.5)  # Rate limit

# Combine all results
all_results = existing + results_from_spotify

print("\n" + "="*75)
print(f"TOTAL RESULTS: {len(existing)} (MusicBrainz) + {len(results_from_spotify)} (Spotify demo) = {len(all_results)}")
print("="*75)

# Save combined results
output_file = 'album_art_mapping.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(all_results)} total mappings to {output_file}")

if results_from_spotify:
    print("\n" + "="*75)
    print("NEW ENTRIES FROM SPOTIFY (sample):")
    print("="*75)
    for i, item in enumerate(results_from_spotify[:5], 1):
        print(f"\n{i}. {item['song_hint']} - {item['artist']}")
        print(f"   Album: {item['album_title']}")
        print(f"   Image: {item['image_url'][:60]}...")

print("\n✓ Done!")
