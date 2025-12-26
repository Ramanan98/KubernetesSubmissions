import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import psycopg2

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)
conn.autocommit = True
cur = conn.cursor()

print("Connected to Postgres", flush=True)

cur.execute("""
CREATE TABLE IF NOT EXISTS todos (
    id SERIAL PRIMARY KEY,
    item TEXT
)
""")

port = int(os.environ.get("TODO_BACKEND_PORT", 8080))
print(f"Todo backend started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/todos":
            cur.execute("SELECT item FROM todos")
            rows = cur.fetchall()
            todos = [row[0] for row in rows]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(todos).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/todos":
            content_length = int(self.headers.get("Content-Length", 0))
            todo_item = self.rfile.read(content_length).decode().strip()
            cur.execute("INSERT INTO todos(item) VALUES (%s)", (todo_item,))
            self.send_response(201)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


HTTPServer(("", port), Handler).serve_forever()
