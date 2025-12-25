import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)

IMAGE_PATH = "/usr/src/app/files/image.jpg"
HTML_FILE = "/app/index.html"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/image.jpg":
            with open(IMAGE_PATH, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            self.wfile.write(data)
        else:
            with open(HTML_FILE, "rb") as f:
                html_data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html_data)


HTTPServer(("", port), Handler).serve_forever()
