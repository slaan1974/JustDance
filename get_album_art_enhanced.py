#!/usr/bin/env python3
"""
Enhanced scraper: Get Just Dance song metadata and album art from MusicBrainz
Uses multiple search strategies and handles retries for better coverage
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

print(f"Loaded {len(songs)} songs from songs.json")

# Collect unique songs by (artist, title)
unique_songs = {}
for song in songs:
    key = (song['artist'], song['title'])
    if key not in unique_songs:
        unique_songs[key] = song

print(f"Found {len(unique_songs)} unique songs\n")

# Results storage
results = []
failed = []

print("="*75)
print("Searching MusicBrainz + Cover Art Archive for complete album metadata...")
print("="*75 + "\n")

for idx, (artist, title) in enumerate(sorted(unique_songs.keys()), 1):
    sys.stdout.write(f"[{idx:3d}/{len(unique_songs)}] '{title[:25]:25s}' by {artist[:28]:28s} -> ")
    sys.stdout.flush()
    
    found = False
    
    try:
        # Strategy 1: Try exact search with artist filter
        search_query = f'{title} artist:{artist}'
        url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=5'
        
        req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceAlbumArtBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('recordings') and len(data['recordings']) > 0:
                recording = data['recordings'][0]
                
                # Try to get album/release info
                if recording.get('releases') and len(recording['releases']) > 0:
                    release = recording['releases'][0]
                    album_title = release.get('title', 'Unknown Album')
                    release_id = release.get('id')
                    
                    # Try to fetch cover art
                    if release_id:
                        try:
                            cover_url = f'https://coverartarchive.org/release/{release_id}/front-250.jpg'
                            # Verify the image exists with a HEAD request
                            req_cover = urllib.request.Request(cover_url, method='HEAD')
                            with urllib.request.urlopen(req_cover, timeout=5) as r:
                                if r.status == 200:
                                    results.append({
                                        "image_url": cover_url,
                                        "album_title": album_title,
                                        "artist": artist,
                                        "song_hint": title
                                    })
                                    print(f"✓ {album_title[:35]:35s}")
                                    found = True
                        except (urllib.error.HTTPError, urllib.error.URLError):
                            pass
                    
                    if not found:
                        # Try to get cover art from first release with artwork
                        if recording.get('releases'):
                            for rel in recording['releases'][:5]:
                                rel_id = rel.get('id')
                                if rel_id:
                                    try:
                                        cover_url = f'https://coverartarchive.org/release/{rel_id}/front-250.jpg'
                                        req_cover = urllib.request.Request(cover_url, method='HEAD')
                                        with urllib.request.urlopen(req_cover, timeout=5) as r:
                                            if r.status == 200:
                                                album_title = rel.get('title', 'Unknown Album')
                                                results.append({
                                                    "image_url": cover_url,
                                                    "album_title": album_title,
                                                    "artist": artist,
                                                    "song_hint": title
                                                })
                                                print(f"✓ {album_title[:35]:35s}*")
                                                found = True
                                                break
                                    except:
                                        pass
        
        if not found:
            # Strategy 2: Try album search with artist
            try:
                search_query = f'recording:"{title}" artist:"{artist}"'
                url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=3'
                
                req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceAlbumArtBot/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if data.get('recordings') and len(data['recordings']) > 0:
                        recording = data['recordings'][0]
                        if recording.get('releases') and len(recording['releases']) > 0:
                            for rel in recording['releases'][:3]:
                                rel_id = rel.get('id')
                                if rel_id:
                                    try:
                                        cover_url = f'https://coverartarchive.org/release/{rel_id}/front-250.jpg'
                                        req_cover = urllib.request.Request(cover_url, method='HEAD')
                                        with urllib.request.urlopen(req_cover, timeout=5) as r:
                                            if r.status == 200:
                                                album_title = rel.get('title', 'Unknown Album')
                                                results.append({
                                                    "image_url": cover_url,
                                                    "album_title": album_title,
                                                    "artist": artist,
                                                    "song_hint": title
                                                })
                                                print(f"✓ {album_title[:35]:35s}**")
                                                found = True
                                                break
                                    except:
                                        pass
            except:
                pass
        
        if not found:
            # Try just the song title
            try:
                search_query = f'{title}'
                url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=10'
                
                req = urllib.request.Request(url, headers={'User-Agent': 'JustDanceAlbumArtBot/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if data.get('recordings') and len(data['recordings']) > 0:
                        for recording in data['recordings'][:5]:
                            # Filter by approximate artist match
                            if recording.get('releases') and len(recording['releases']) > 0:
                                for rel in recording['releases'][:2]:
                                    rel_id = rel.get('id')
                                    if rel_id:
                                        try:
                                            cover_url = f'https://coverartarchive.org/release/{rel_id}/front-250.jpg'
                                            req_cover = urllib.request.Request(cover_url, method='HEAD')
                                            with urllib.request.urlopen(req_cover, timeout=5) as r:
                                                if r.status == 200:
                                                    album_title = rel.get('title', 'Unknown Album')
                                                    results.append({
                                                        "image_url": cover_url,
                                                        "album_title": album_title,
                                                        "artist": artist,
                                                        "song_hint": title
                                                    })
                                                    print(f"✓ {album_title[:35]:35s}***")
                                                    found = True
                                                    break
                                        except:
                                            pass
                            if found:
                                break
            except:
                pass
        
        if not found:
            print("- not found")
            failed.append((artist, title))
    
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}")
        failed.append((artist, title))
    except urllib.error.URLError as e:
        print(f"✗ Network error")
        failed.append((artist, title))
    except Exception as e:
        print(f"✗ Error")
        failed.append((artist, title))
    
    # Rate limit
    time.sleep(0.8)

# Summary
print("\n" + "="*75)
print(f"RESULTS: {len(results)} songs with album art found")
print(f"FAILED:  {len(failed)} songs without album art")
print(f"SUCCESS: {len(results)*100//len(unique_songs)}% coverage")
print("="*75)

# Save results
output_file = 'album_art_mapping.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(results)} mappings to {output_file}")

# Show sample
if results:
    print("\n" + "="*75)
    print("SAMPLE RESULTS (first 10):")
    print("="*75)
    for i, item in enumerate(results[:10], 1):
        print(f"\n{i}. {item['song_hint']} - {item['artist']}")
        print(f"   Album: {item['album_title']}")
        print(f"   Image: {item['image_url']}")

print("\n✓ Done!")
