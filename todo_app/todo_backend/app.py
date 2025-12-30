import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

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

conn = None
cur = None


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
            item TEXT
        )
        """
        )
        logger.info("Connected to Postgres")
    except Exception as e:
        conn = None
        cur = None
        logger.error(f"DB connection failed: {e}")


connect_db()

port = int(os.environ.get("TODO_BACKEND_PORT", 8080))
logger.info("Built in GitHub actions and pushed to Artifact Registry")
logger.info(f"Todo backend started on port {port}")


class Handler(BaseHTTPRequestHandler):
    MAX_TODO_LENGTH = 140

    def do_GET(self):
        if self.path == "/todos":
            cur.execute("SELECT item FROM todos")
            rows = cur.fetchall()
            todos = [row[0] for row in rows]
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

            logger.info({"method": "POST", "path": self.path, "item_added": todo_item})
        else:
            self.send_response(404)
            self.end_headers()
            logger.info({"method": "POST", "path": self.path, "response": 404})


HTTPServer(("", port), Handler).serve_forever()
