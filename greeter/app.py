import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
VERSION = os.environ.get("VERSION", "1")

print(f"Greeter version {VERSION}", flush=True)
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Hello from version {VERSION}".encode())


HTTPServer(("", port), Handler).serve_forever()
