import os
import random
import string
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client

s = "".join(random.choices(string.ascii_letters + string.digits, k=12))
port = int(os.environ.get("PORT", 8080))

MESSAGE = os.environ.get("MESSAGE", "")
INFO_FILE = "/config/information.txt"

print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        conn = http.client.HTTPConnection("ping-pong-svc", 2345)
        conn.request("GET", "/pings")
        res = conn.getresponse()
        ping_pong_requests = res.read().decode()
        conn.close()

        file_content = ""
        with open(INFO_FILE, "r") as f:
            file_content = f.read().strip()

        self.send_response(200)
        self.end_headers()

        response = (
            f"{file_content}\n"
            f"{MESSAGE}\n"
            f"{datetime.now().isoformat()}: {s}.\n"
            f"Ping / Pongs: {ping_pong_requests}"
        )

        self.wfile.write(response.encode())


HTTPServer(("", port), Handler).serve_forever()
