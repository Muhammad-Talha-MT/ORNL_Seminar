"""Tiny static server for the deck that tells the browser NOT to cache.
(python3 -m http.server lets browsers keep stale CSS/JS, which makes edits look broken.)
Usage: python3 tools/serve.py [port]    then open http://localhost:8000/"""
import http.server, os, sys

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print(f"Serving the deck on http://localhost:{port}/  (no-cache)  Ctrl+C to stop")
http.server.ThreadingHTTPServer(("", port), NoCache).serve_forever()
