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
        self.send_response(200)
        self.end_headers()
        response = f"{datetime.now().isoformat()} {s}"
        self.wfile.write(response.encode())


HTTPServer(("", port), Handler).serve_forever()
