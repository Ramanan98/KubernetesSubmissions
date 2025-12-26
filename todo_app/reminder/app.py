import os

import psycopg2
import requests

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres-svc")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
WIKI_URL = os.environ.get("WIKI_URL", "https://example.com")


def get_random_wiki() -> str:
    url = WIKI_URL
    headers = {"User-Agent": "RandomWikiScript/1.0 (my_email@example.com)"}
    response = requests.get(url, headers=headers, allow_redirects=True)
    return response.url


def main():
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

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        item TEXT
    )
    """
    )
    random_wiki = get_random_wiki()
    todo_item = f"Read {random_wiki}"
    cur.execute("INSERT INTO todos(item) VALUES (%s)", (todo_item,))


if __name__ == "__main__":
    main()
