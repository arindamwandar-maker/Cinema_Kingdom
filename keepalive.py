import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, fmt, *args):
        pass


def start():
    port = int(os.getenv('PORT') or 10000)
    server = HTTPServer(('0.0.0.0', port), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
