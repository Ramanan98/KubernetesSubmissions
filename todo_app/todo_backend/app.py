import asyncio
import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import nats
import psycopg2

logger = logging.getLogger("todo-backend")
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(stdout_handler)

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
NATS_URL = os.environ.get("NATS_URL", "nats://my-nats:4222")

conn = None
cur = None
nc = None
nats_loop = None


def connect_db():
    global conn, cur
    try:
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
        cur.execute(
            "ALTER TABLE todos ADD COLUMN IF NOT EXISTS done BOOLEAN DEFAULT FALSE"
        )
        logger.info("Connected to Postgres")
    except Exception as e:
        conn = None
        cur = None
        logger.error(f"DB connection failed: {e}")


async def nats_error_cb(e):
    logger.error(f"NATS error: {e}")


async def nats_disconnected_cb():
    logger.warning("NATS disconnected")


async def nats_reconnected_cb():
    logger.info("NATS reconnected")


async def nats_closed_cb():
    logger.warning("NATS connection closed")


async def nats_worker():
    global nc
    try:
        nc = await nats.connect(
            NATS_URL,
            connect_timeout=5,
            max_reconnect_attempts=3,
            reconnect_time_wait=2,
            error_cb=lambda e: logger.error(f"NATS error: {e}"),
            disconnected_cb=lambda: logger.warning("NATS disconnected"),
            reconnected_cb=lambda: logger.info("NATS reconnected"),
            closed_cb=lambda: logger.warning("NATS connection closed"),
        )
        logger.info(f"Connected to NATS at {NATS_URL}")
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"NATS connection failed: {e}")


def start_nats_thread():
    global nats_loop

    def run_loop():
        global nats_loop
        nats_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(nats_loop)
        nats_loop.run_until_complete(nats_worker())

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    time.sleep(2)
    logger.info("NATS thread started")


def publish_message(message):
    if nc is None or nats_loop is None:
        logger.warning("NATS not connected, skipping message publish")
        return

    try:
        future = asyncio.run_coroutine_threadsafe(
            nc.publish("todo-backend", message.encode()), nats_loop
        )
        future.result(timeout=2)
        logger.info(f"Published to NATS: {message}")
    except Exception as e:
        logger.error(f"Failed to publish to NATS: {e}")


connect_db()
start_nats_thread()

port = int(os.environ.get("TODO_BACKEND_PORT", 8080))
logger.info("Built in GitHub actions and pushed to Artifact Registry")
logger.info(f"Todo backend started on port {port}")


class Handler(BaseHTTPRequestHandler):
    MAX_TODO_LENGTH = 140

    def do_GET(self):
        if self.path == "/todos":
            cur.execute("SELECT id, item, done FROM todos")
            rows = cur.fetchall()
            todos = [{"id": row[0], "item": row[1], "done": row[2]} for row in rows]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(todos).encode())

            logger.info({"method": "GET", "path": self.path, "response": todos})
        elif self.path == "/healthz":
            try:
                if cur is None:
                    connect_db()
                if cur is not None:
                    cur.execute("SELECT 1")
                    self.send_response(200)
                else:
                    self.send_response(500)
            except Exception:
                self.send_response(500)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            logger.info({"method": "GET", "path": self.path, "response": 404})

    def do_POST(self):
        if self.path == "/todos":
            content_length = int(self.headers.get("Content-Length", 0))
            todo_item = self.rfile.read(content_length).decode().strip()

            if len(todo_item) > self.MAX_TODO_LENGTH:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                error_msg = {
                    "error": f"Todo item too long (max {self.MAX_TODO_LENGTH} chars)"
                }
                self.wfile.write(json.dumps(error_msg).encode())
                logger.error(
                    {
                        "method": "POST",
                        "path": self.path,
                        "error": "Todo item too long",
                        "length": len(todo_item),
                        "item": todo_item,
                    }
                )
                return

            cur.execute("INSERT INTO todos(item) VALUES (%s)", (todo_item,))
            self.send_response(201)
            self.end_headers()

            publish_message(f"New todo created: {todo_item}")

            logger.info({"method": "POST", "path": self.path, "item_added": todo_item})
        else:
            self.send_response(404)
            self.end_headers()
            logger.info({"method": "POST", "path": self.path, "response": 404})

    def do_PUT(self):
        if self.path.startswith("/todos/"):
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
                logger.info({"method": "PUT", "path": self.path, "response": 404})
            else:
                self.send_response(200)
                self.end_headers()

                if row:
                    todo_item = row[0]
                    publish_message(f"Todo completed: {todo_item}")

                logger.info({"method": "PUT", "path": self.path, "todo_id": todo_id})
        else:
            self.send_response(404)
            self.end_headers()
            logger.info({"method": "PUT", "path": self.path, "response": 404})


HTTPServer(("", port), Handler).serve_forever()
