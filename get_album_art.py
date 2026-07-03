#!/usr/bin/env python3
"""
Scrape Just Dance song metadata and album art from MusicBrainz and Cover Art Archive
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

print("="*70)
print("Searching MusicBrainz + Cover Art Archive for album metadata...")
print("="*70 + "\n")

for idx, (artist, title) in enumerate(sorted(unique_songs.keys()), 1):
    # Limit to first 50 for demo
    if idx > 50:
        print(f"\n[Info] Limited to first 50 songs for demo")
        break
    
    sys.stdout.write(f"[{idx:3d}] '{title}' by {artist[:30]:30s} -> ")
    sys.stdout.flush()
    
    try:
        # Search MusicBrainz for recording
        search_query = f'{title} artist:{artist}'
        url = f'https://musicbrainz.org/ws/2/recording?query={quote(search_query)}&fmt=json&limit=3'
        
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
                                    print(f"✓ {album_title}")
                                else:
                                    print("- no cover art")
                                    failed.append((artist, title, "no cover art"))
                        except (urllib.error.HTTPError, urllib.error.URLError):
                            print("- cover art not found")
                            failed.append((artist, title, "cover not in archive"))
                    else:
                        print("- no release ID")
                        failed.append((artist, title, "no release id"))
                else:
                    print("- no releases found")
                    failed.append((artist, title, "no releases"))
            else:
                print("✗ song not found")
                failed.append((artist, title, "not found"))
    
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}")
        failed.append((artist, title, f"HTTP {e.code}"))
    except urllib.error.URLError as e:
        print(f"✗ Network error")
        failed.append((artist, title, "network error"))
    except Exception as e:
        print(f"✗ {type(e).__name__}")
        failed.append((artist, title, type(e).__name__))
    
    # Rate limit: MusicBrainz asks for polite rate limiting
    time.sleep(1.5)

# Summary
print("\n" + "="*70)
print(f"RESULTS: {len(results)} songs with album art found")
print(f"FAILED:  {len(failed)} songs without album art")
print("="*70)

# Save results
output_file = 'album_art_mapping.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(results)} mappings to {output_file}")

# Show sample
if results:
    print("\n" + "="*70)
    print("SAMPLE RESULTS (first 5):")
    print("="*70)
    for i, item in enumerate(results[:5], 1):
        print(f"\n{i}. {item['song_hint']} - {item['artist']}")
        print(f"   Album: {item['album_title']}")
        print(f"   Image: {item['image_url']}")

# Failed summary
if failed:
    print("\n" + "="*70)
    print(f"FAILED SONGS ({len(failed)} total) - Sample:")
    print("="*70)
    for artist, title, reason in failed[:10]:
        print(f"  • {title} by {artist} ({reason})")
    if len(failed) > 10:
        print(f"  ... and {len(failed) - 10} more")

print("\n✓ Done!")
