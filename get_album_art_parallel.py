#!/usr/bin/env python3
"""
Fast parallel album art collection using concurrent requests
Uses concurrent.futures for thread-based parallel API calls
"""

import json
import urllib.request
import urllib.error
from urllib.parse import quote
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
print(f"Processing with parallel requests...\n")

# Results storage (thread-safe)
results = []
failed = []
lock = threading.Lock()
counter = [0]  # counter[0] is mutable reference

def search_song(artist, title):
    """Search for a single song and return album art info if found"""
    counter[0] += 1
    idx = counter[0]
    
    try:
        # Try MusicBrainz API
        search_query = f'{title} artist:{artist}'
        url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=5'
        
        req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceBot/1.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('recordings') and len(data['recordings']) > 0:
                recording = data['recordings'][0]
                
                if recording.get('releases') and len(recording['releases']) > 0:
                    # Try to find release with cover art
                    for release in recording['releases'][:5]:
                        release_id = release.get('id')
                        if release_id:
                            try:
                                cover_url = f'https://coverartarchive.org/release/{release_id}/front-250.jpg'
                                req_cover = urllib.request.Request(cover_url, method='HEAD')
                                with urllib.request.urlopen(req_cover, timeout=5) as r:
                                    if r.status == 200:
                                        return {
                                            "image_url": cover_url,
                                            "album_title": release.get('title', 'Unknown Album'),
                                            "artist": artist,
                                            "song_hint": title
                                        }
                            except:
                                pass
    except:
        pass
    
    return None

# Process songs with parallel requests
print(f"Searching {len(unique_songs)} songs with 10 parallel workers...\n")

processed = 0
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(search_song, artist, title): (artist, title) 
               for artist, title in unique_songs.keys()}
    
    for future in as_completed(futures):
        artist, title = futures[future]
        processed += 1
        
        result = None
        try:
            result = future.result()
        except Exception as e:
            pass
        
        if result:
            with lock:
                results.append(result)
            status = "✓"
        else:
            with lock:
                failed.append((artist, title))
            status = "-"
        
        if processed % 50 == 0 or processed == len(unique_songs):
            sys.stdout.write(f"\r[{processed:3d}/{len(unique_songs)}] Processed: {status} ({len(results)} found)")
            sys.stdout.flush()

print(f"\n\n" + "="*75)
print(f"RESULTS: {len(results)} songs with album art found out of {len(unique_songs)}")
print(f"SUCCESS RATE: {len(results)*100//len(unique_songs)}%")
print("="*75)

# Save results
output_file = 'album_art_mapping.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(results)} mappings to {output_file}")

# Show samples
if results:
    print("\n" + "="*75)
    print("SAMPLE RESULTS (first 10):")
    print("="*75)
    for i, item in enumerate(results[:10], 1):
        print(f"\n{i}. {item['song_hint']} - {item['artist']}")
        print(f"   Album: {item['album_title']}")
        print(f"   Image: {item['image_url'][:70]}...")

print("\n✓ Done!")
print(f"\nJSON file ready at: {output_file}")
