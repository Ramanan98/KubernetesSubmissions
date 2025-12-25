import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

port = int(os.environ.get("TODO_BACKEND_PORT", 8080))
print(f"Todo backend started on port {port}", flush=True)

TODOS = []


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/todos":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(TODOS).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/todos":
            content_length = int(self.headers.get("Content-Length", 0))
            todo_item = self.rfile.read(content_length).decode().strip()
            TODOS.append(todo_item)
            self.send_response(201)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


HTTPServer(("", port), Handler).serve_forever()
