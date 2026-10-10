#!/usr/bin/env python3
"""
Automated tests for the Just Dance Review Hub.

Run from the project root:
    python -m unittest discover -s tests -v
    # or simply:
    python tests/test_site.py

Covers the data file (songs.json) and the HTTP server (server.py). Uses only
the standard library, so no extra install is required.
"""

import json
import logging
import os
import sys
import threading
import unittest
from http.server import HTTPServer
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS_FILE = os.path.join(ROOT, 'songs.json')

REQUIRED_FIELDS = {
    'title', 'artist', 'game', 'year',
    'image_url', 'image_url_local', 'era',
}


class SongsDataTests(unittest.TestCase):
    """Validate songs.json and that referenced local files exist."""

    @classmethod
    def setUpClass(cls):
        with open(SONGS_FILE, encoding='utf-8') as f:
            cls.songs = json.load(f)

    def test_is_json_list(self):
        self.assertIsInstance(self.songs, list)
        self.assertGreater(len(self.songs), 0)

    def test_catalog_size(self):
        # Regression guard: the catalog should hold all 793 songs.
        self.assertEqual(len(self.songs), 793)

    def test_required_fields_present(self):
        for i, song in enumerate(self.songs):
            missing = REQUIRED_FIELDS - set(song)
            self.assertFalse(missing, f'song #{i} ({song.get("title")}) missing {missing}')

    def test_every_song_has_album_art_file(self):
        missing = [s['title'] for s in self.songs
                   if not os.path.isfile(os.path.join(ROOT, s['image_url_local']))]
        self.assertEqual(missing, [], f'{len(missing)} album-art files missing')

    def test_every_song_has_era(self):
        bad = [s['title'] for s in self.songs if not s.get('era')]
        self.assertEqual(bad, [], f'{len(bad)} songs without era')

    def test_preview_files_all_exist(self):
        referenced = [s for s in self.songs if s.get('preview_url_local')]
        missing = [s['title'] for s in referenced
                   if not os.path.isfile(os.path.join(ROOT, s['preview_url_local']))]
        self.assertEqual(missing, [], f'{len(missing)} preview files missing')
        # Sanity check on coverage; adjust if the catalog grows.
        self.assertGreaterEqual(len(referenced), 700)


class ServerTests(unittest.TestCase):
    """Exercise the custom HTTP server end to end."""

    @classmethod
    def setUpClass(cls):
        os.chdir(ROOT)
        sys.path.insert(0, ROOT)
        import server  # noqa: E402  (import after sys.path tweak)

        logger = logging.getLogger('test_access_log')
        logger.addHandler(logging.NullHandler())
        server.LoggingHTTPRequestHandler.logger = logger

        cls.httpd = HTTPServer(('127.0.0.1', 0), server.LoggingHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _get(self, path):
        return urlopen(f'http://127.0.0.1:{self.port}{path}', timeout=10)

    def test_index_served(self):
        with self._get('/') as r:
            self.assertEqual(r.status, 200)
            body = r.read().decode('utf-8')
        self.assertIn('Just Dance Review Hub', body)

    def test_songs_json_served(self):
        with self._get('/songs.json') as r:
            self.assertEqual(r.status, 200)
            data = json.loads(r.read().decode('utf-8'))
        self.assertEqual(len(data), 793)

    def test_static_assets_served(self):
        for asset in ('/styles.css', '/script.js', '/index.html'):
            with self._get(asset) as r:
                self.assertEqual(r.status, 200, asset)

    def test_log_event_returns_204(self):
        with self._get('/log_event?action=test') as r:
            self.assertEqual(r.status, 204)


if __name__ == '__main__':
    unittest.main(verbosity=2)
