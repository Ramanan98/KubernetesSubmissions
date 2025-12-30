import http.client
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

logger = logging.getLogger("image-read")
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(stdout_handler)

PORT = int(os.environ.get("IMAGE_READ_PORT", 8080))
BACKEND_HOST = os.environ.get("BACKEND_HOST", "todo-backend-svc")
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 2345))
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/usr/src/app/files/image.jpg")
HTML_FILE = os.environ.get("HTML_FILE", "/app/index.html")

logger.info(f"Server started on port {PORT}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/image.jpg":
            with open(IMAGE_PATH, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/todos"):
            try:
                conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=2)
                conn.request("GET", "/todos")
                res = conn.getresponse()
                todos = res.read().decode()
                conn.close()
            except Exception:
                self.send_response(500)
                self.end_headers()
                return

            with open(HTML_FILE, "r") as f:
                html_template = f.read()
            html = html_template.replace("{{TODOS}}", todos_to_html(todos))
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/healthz":
            try:
                conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT)
                conn.request("GET", "/todos")
                res = conn.getresponse()
                conn.close()
                self.send_response(200 if res.status == 200 else 500)
            except Exception:
                self.send_response(500)
            self.end_headers()
        else:
            self.send_response(200)
            with open(HTML_FILE, "r") as f:
                html_template = f.read()
            html = html_template.replace("{{TODOS}}", "")
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

    def do_POST(self):
        if self.path == "/todos":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode()
            parsed = parse_qs(post_data)
            todo_item = parsed.get("todo", [""])[0]
            conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT)
            conn.request("POST", "/todos", body=todo_item)
            conn.getresponse()
            conn.close()
            self.send_response(303)
            self.send_header("Location", "/todos")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def todos_to_html(todos_str):
    try:
        todos = json.loads(todos_str)
    except Exception:
        todos = []
    return "".join(f"<li>{t}</li>" for t in todos)


HTTPServer(("", PORT), Handler).serve_forever()
