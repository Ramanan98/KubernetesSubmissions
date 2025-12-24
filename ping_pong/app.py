import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        response = f"pong {Handler.counter}"
        self.wfile.write(response.encode())
        Handler.counter += 1


HTTPServer(("", port), Handler).serve_forever()
