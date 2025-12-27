import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import psycopg2

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc.project.svc.cluster.local")
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
CREATE TABLE IF NOT EXISTS ping_counter (
    id SERIAL PRIMARY KEY,
    counter INT
)
""")

port = int(os.environ.get("PORT", 8080))
print(f"Server started on port {port}", flush=True)


class Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        if self.path == "/pings":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(Handler.counter).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"pong {Handler.counter}".encode())
            Handler.counter += 1
            cur.execute(
                "INSERT INTO ping_counter(counter) VALUES (%s)", (Handler.counter,)
            )


HTTPServer(("", port), Handler).serve_forever()
