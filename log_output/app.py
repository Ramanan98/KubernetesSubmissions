import os
import random
import string
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

s = "".join(random.choices(string.ascii_letters + string.digits, k=12))
port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open("/usr/src/app/files/pingpongs.txt", "r") as f:
            ping_pong_requests = f.read()
        self.send_response(200)
        self.end_headers()
        response = (
            f"{datetime.now().isoformat()} {s}\nPing / Pongs: {ping_pong_requests}"
        )
        self.wfile.write(response.encode())


HTTPServer(("", port), Handler).serve_forever()
