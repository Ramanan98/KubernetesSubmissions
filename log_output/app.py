import http.client
import os
import random
import string
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

s = "".join(random.choices(string.ascii_letters + string.digits, k=12))
port = int(os.environ.get("PORT", 8080))

MESSAGE = os.environ.get("MESSAGE", "")
INFO_FILE = "/config/information.txt"

print(f"Server started on port {port}", flush=True)

connection = False


def check_ping_pong():
    try:
        conn = http.client.HTTPConnection("ping-pong-svc", 2345, timeout=2)
        conn.request("GET", "/pings")
        res = conn.getresponse()
        conn.close()
        return res.status == 200
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
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

        elif self.path == "/healthz":
            if check_ping_pong():
                self.send_response(200)
            else:
                self.send_response(500)
            self.end_headers()


HTTPServer(("", port), Handler).serve_forever()
