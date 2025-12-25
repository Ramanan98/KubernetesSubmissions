import os
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("PORT", 8080))
print(f"Server started in port {port}", flush=True)

IMAGE_PATH = "/usr/src/app/files/image.jpg"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/image.jpg":
            try:
                with open(IMAGE_PATH, "rb") as f:
                    data = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            """
            <html>
                <body>
                    <h1>The project app</h1>
                    <img src="/image.jpg" />
                    <p>DevOps with Kubernetes 2025</p>
                </body>
            </html>
        """.encode("utf-8")
        )


HTTPServer(("", port), Handler).serve_forever()
