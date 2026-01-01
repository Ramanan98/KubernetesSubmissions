import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg2

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc.project.svc.cluster.local")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

conn = None
cur = None
db_connected = False


def connect_db():
    global conn, cur, db_connected
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ping_counter (
                id SERIAL PRIMARY KEY,
                counter INT
            )
            """
        )
    except Exception as e:
        db_connected = False
        conn = None
        cur = None
        print(f"DB connection failed: {e}", flush=True)
    else:
        db_connected = True
        print("Connected to Postgres", flush=True)


connect_db()

print("Version 2", flush=True)

PORT = int(os.environ.get("PORT", 8080))
print(f"Server started on port {PORT}", flush=True)


class Handler(BaseHTTPRequestHandler):
    counter = 0

    def do_GET(self):
        global db_connected, cur

        if self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"pong {Handler.counter}".encode())
            Handler.counter += 1

            if db_connected:
                try:
                    cur.execute(
                        "INSERT INTO ping_counter(counter) VALUES (%s)",
                        (Handler.counter,),
                    )
                except Exception as e:
                    db_connected = False
                    print(f"DB write failed: {e}", flush=True)

        elif self.path == "/pings":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(Handler.counter).encode())

        elif self.path == "/healthz":
            status_code = 200 if db_connected else 500
            self.send_response(status_code)
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()


HTTPServer(("", PORT), Handler).serve_forever()
