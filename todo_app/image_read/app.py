import http.client
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

PORT = int(os.environ.get("IMAGE_READ_PORT", 8080))
BACKEND_HOST = os.environ.get("BACKEND_HOST", "todo-backend-svc")
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 2345))
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/usr/src/app/files/image.jpg")
HTML_FILE = os.environ.get("HTML_FILE", "/app/index.html")

print(f"Server started on port {PORT}", flush=True)


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
            conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT)
            conn.request("GET", "/todos")
            res = conn.getresponse()
            todos = res.read().decode()
            conn.close()
            with open(HTML_FILE, "r") as f:
                html_template = f.read()

            html = html_template.replace("{{TODOS}}", todos_to_html(todos))
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
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
