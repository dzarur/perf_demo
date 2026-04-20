"""
Tiny localhost-only HTTP server for the network workload.
Run in a separate terminal: python3 server.py

Endpoints:
  /logs       — 100 log lines with 150 ms artificial delay
  /logs/fast  — same payload, no delay
  /status     — health check
"""

import http.server
import random
import time

HOST = "127.0.0.1"
PORT = 5001
DELAY = 0.15  # seconds per request

PATHS = ["/home", "/api/data", "/login", "/logout", "/search", "/static/app.js"]
STATUSES = [200, 200, 200, 301, 404, 500]


def make_log_batch(n=100):
    rng = random.Random()
    lines = []
    for _ in range(n):
        path = rng.choice(PATHS)
        status = rng.choice(STATUSES)
        size = rng.randint(100, 9_999)
        lines.append(
            f'127.0.0.1 - - [01/Jan/2025:00:00:00 +0000] "GET {path} HTTP/1.1" {status} {size}'
        )
    return "\n".join(lines).encode()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/logs":
            time.sleep(DELAY)
            body = make_log_batch()
            self._respond(200, body)
        elif self.path == "/logs/fast":
            body = make_log_batch()
            self._respond(200, body)
        elif self.path == "/status":
            self._respond(200, b"ok")
        else:
            self._respond(404, b"not found")

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silence per-request noise; rely on startup message


if __name__ == "__main__":
    server = http.server.HTTPServer((HOST, PORT), Handler)
    print(f"Server listening on http://{HOST}:{PORT}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
