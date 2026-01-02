import asyncio
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import nats
import psycopg2

# -------------------
# Logging
# -------------------
logger = logging.getLogger("todo-backend")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# -------------------
# Config
# -------------------
DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
NATS_URL = os.environ.get("NATS_URL", "nats://my-nats:4222")
PORT = int(os.environ.get("TODO_BACKEND_PORT", 8080))

# -------------------
# Database
# -------------------
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)
conn.autocommit = True
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        item TEXT,
        done BOOLEAN DEFAULT FALSE
    )
    """
)

logger.info("Connected to Postgres")
logger.info("Saved locally")


async def _publish(message: str):
    nc = await nats.connect(NATS_URL, connect_timeout=60)
    await nc.publish("todo-backend", message.encode())
    await nc.flush()
    await nc.close()


def publish_message(message: str):
    try:
        asyncio.run(_publish(message))
        logger.info(f"Published to NATS: {message}")
    except Exception as e:
        logger.error(f"NATS publish failed: {e}")


# -------------------
# HTTP Handler
# -------------------
class Handler(BaseHTTPRequestHandler):
    MAX_TODO_LENGTH = 140

    def do_GET(self):
        if self.path == "/todos":
            cur.execute("SELECT id, item, done FROM todos")
            rows = cur.fetchall()
            todos = [{"id": r[0], "item": r[1], "done": r[2]} for r in rows]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(todos).encode())
            return

        if self.path == "/healthz":
            try:
                cur.execute("SELECT 1")
                self.send_response(200)
            except Exception:
                self.send_response(500)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/todos":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        item = self.rfile.read(length).decode().strip()

        if len(item) > self.MAX_TODO_LENGTH:
            self.send_response(400)
            self.end_headers()
            return

        cur.execute("INSERT INTO todos(item) VALUES (%s)", (item,))
        self.send_response(201)
        self.end_headers()

        publish_message(f"New todo created: {item}")

    def do_PUT(self):
        if not self.path.startswith("/todos/"):
            self.send_response(404)
            self.end_headers()
            return

        try:
            todo_id = int(self.path.split("/")[-1])
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return

        cur.execute("SELECT item FROM todos WHERE id = %s", (todo_id,))
        row = cur.fetchone()

        cur.execute("UPDATE todos SET done = TRUE WHERE id = %s", (todo_id,))
        if cur.rowcount == 0:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

        if row:
            publish_message(f"Todo completed: {row[0]}")


# -------------------
# Server
# -------------------
logger.info(f"Todo backend started on port {PORT}")
HTTPServer(("", PORT), Handler).serve_forever()
