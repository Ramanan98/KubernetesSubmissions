import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        with open("/usr/src/app/files/log.txt", "r") as f:
            response = f.read()
        self.wfile.write(response.encode())


HTTPServer(("", port), Handler).serve_forever()
