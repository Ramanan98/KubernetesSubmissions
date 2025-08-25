import os
from http.server import HTTPServer, BaseHTTPRequestHandler

port = int(os.environ.get("PORT", 8080))
print(f"Server started in port {port}", flush=True)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Welcome to to-do app")

HTTPServer(("", port), Handler).serve_forever()