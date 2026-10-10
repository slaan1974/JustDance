#!/usr/bin/env python3
"""
Custom HTTP server that logs all access events to a log file.
Usage: python3 server.py [port]
Default port: 8006 (override with the PORT env var or a CLI argument)
Log file: log.txt (created in the same directory)

Port allocation on the host: 8000 & 8008 = pong, 8080 = qBittorrent, 8006 = jd-new.

Log retention policy:
  - Maximum file size: 10 MB (FIFO — oldest entries rotate out first)
  - Maximum age: 14 days (pruned on startup)
"""

import re
import sys
import os
import logging
import logging.handlers
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timedelta


LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
MAX_BYTES = 10 * 1024 * 1024    # 10 MB
BACKUP_COUNT = 2                # Keep up to 2 rotated backups (FIFO)
RETENTION_DAYS = 14
DEFAULT_PORT = 8006


def prune_old_entries(log_path, max_age_days):
    """Remove log entries older than max_age_days from the log file."""
    if not os.path.exists(log_path):
        return 0

    cutoff = datetime.now() - timedelta(days=max_age_days)
    # Matches timestamps like [28/May/2026 16:10:54]
    timestamp_pattern = re.compile(r'\[(\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\]')

    kept_lines = []
    removed = 0

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            match = timestamp_pattern.search(line)
            if match:
                try:
                    entry_time = datetime.strptime(match.group(1), "%d/%b/%Y %H:%M:%S")
                    if entry_time < cutoff:
                        removed += 1
                        continue
                except ValueError:
                    pass  # Keep lines with unparseable timestamps
            kept_lines.append(line)

    if removed > 0:
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)

    # Also prune rotated backup files
    for i in range(1, BACKUP_COUNT + 1):
        backup = f"{log_path}.{i}"
        if os.path.exists(backup):
            prune_old_entries_single(backup, cutoff, timestamp_pattern)

    return removed


def prune_old_entries_single(path, cutoff, pattern):
    """Prune a single backup log file of entries older than cutoff."""
    kept = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                try:
                    entry_time = datetime.strptime(match.group(1), "%d/%b/%Y %H:%M:%S")
                    if entry_time < cutoff:
                        continue
                except ValueError:
                    pass
            kept.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(kept)


class LoggingHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that logs all events to a file."""

    logger = None

    def do_GET(self):
        # Intercept /log_event requests for client-side event logging
        if self.path.startswith("/log_event?"):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            action = query.get("action", ["unknown"])[0]

            timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
            message = f'{self.client_address[0]} - - [{timestamp}] [USER_EVENT] {action}'
            self.logger.info(message)
            print(f"[USER_EVENT] {self.client_address[0]} - {action}")

            # Send 204 No Content response
            self.send_response(204)
            self.end_headers()
            return

        # All other requests handled normally
        super().do_GET()

    def log_message(self, format, *args):
        # Standard console output (same as default behavior)
        super().log_message(format, *args)

        # Also write to the log file
        timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        message = f'{self.client_address[0]} - - [{timestamp}] {format % args}'
        self.logger.info(message)

    def log_error(self, format, *args):
        # Standard console output for errors
        super().log_error(format, *args)

        # Log errors to file with [ERROR] tag for easy filtering
        timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        message = f'{self.client_address[0]} - - [{timestamp}] [ERROR] {format % args}'
        self.logger.info(message)



def run(port=DEFAULT_PORT):
    print(f"Log file path: {LOG_FILE}")
    print(f"Log directory: {os.path.dirname(LOG_FILE)}")
    print(f"Directory exists: {os.path.exists(os.path.dirname(LOG_FILE))}")
    print(f"Directory writable: {os.access(os.path.dirname(LOG_FILE), os.W_OK)}")

    # Verify we can write to the log file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("")  # Touch the file
        print(f"Log file created/verified: {os.path.exists(LOG_FILE)}")
    except Exception as e:
        print(f"ERROR: Cannot create log file: {e}")
        sys.exit(1)

    # Prune entries older than 14 days on startup
    removed = prune_old_entries(LOG_FILE, RETENTION_DAYS)
    if removed:
        print(f"Pruned {removed} log entries older than {RETENTION_DAYS} days.")

    # Set up file logger with rotation (max 10 MB, FIFO via backups)
    logger = logging.getLogger("access_log")
    logger.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        mode="a",
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)

    LoggingHTTPRequestHandler.logger = logger

    # Log server start
    start_msg = f"--- Server started on port {port} at {datetime.now().strftime('%d/%b/%Y %H:%M:%S')} ---"
    logger.info(start_msg)
    print(start_msg)
    print(f"Logging requests to: {LOG_FILE}")
    print(f"Max file size: {MAX_BYTES // (1024*1024)} MB | Retention: {RETENTION_DAYS} days")

    server = HTTPServer(("0.0.0.0", port), LoggingHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop_msg = f"--- Server stopped at {datetime.now().strftime('%d/%b/%Y %H:%M:%S')} ---"
        logger.info(stop_msg)
        print(f"\n{stop_msg}")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", DEFAULT_PORT))
    run(port)
