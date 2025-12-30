import http.client
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger("image-read")
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(stdout_handler)

PORT = int(os.environ.get("IMAGE_READ_PORT", 8081))
BACKEND_HOST = os.environ.get("BACKEND_HOST", "todo-backend-svc")
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 8080))
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/usr/src/app/files/image.jpg")
HTML_FILE = os.environ.get("HTML_FILE", "/app/index.html")

logger.info(f"Server started on port {PORT}")


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
                logger.info("Served image.jpg")
            except Exception as e:
                logger.error(f"Error serving image: {e}")
                self.send_response(404)
                self.end_headers()

        elif self.path == "/api/todos":
            try:
                conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=2)
                conn.request("GET", "/todos")
                res = conn.getresponse()
                todos = res.read()
                conn.close()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(todos)
                logger.info("Proxied GET /api/todos to backend")
            except Exception as e:
                logger.error(f"Backend error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Backend unavailable"}')

        elif self.path == "/" or self.path == "/todos":
            try:
                with open(HTML_FILE, "r") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
                logger.info(f"Served index.html for {self.path}")
            except Exception as e:
                logger.error(f"Error serving HTML: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == "/healthz":
            self.send_response(200)
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()
            logger.info(f"404 for path: {self.path}")

    def do_POST(self):
        if self.path == "/api/todos":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                todo_item = self.rfile.read(content_length).decode().strip()

                conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=2)
                conn.request("POST", "/todos", body=todo_item)
                res = conn.getresponse()
                response_data = res.read()
                conn.close()

                self.send_response(res.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response_data)
                logger.info(f"Proxied POST /api/todos to backend: {todo_item}")
            except Exception as e:
                logger.error(f"Backend error on POST: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Backend unavailable"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith("/api/todos/"):
            try:
                todo_id = self.path.split("/")[-1]

                conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=2)
                conn.request("PUT", f"/todos/{todo_id}")
                res = conn.getresponse()
                conn.close()

                self.send_response(res.status)
                self.end_headers()
                logger.info(f"Proxied PUT /api/todos/{todo_id} to backend")
            except Exception as e:
                logger.error(f"Backend error on PUT: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


HTTPServer(("", PORT), Handler).serve_forever()
