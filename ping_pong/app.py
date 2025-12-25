import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        if self.path == "/pings":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(Handler.counter).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"pong {Handler.counter}".encode())
            Handler.counter += 1


HTTPServer(("", port), Handler).serve_forever()
