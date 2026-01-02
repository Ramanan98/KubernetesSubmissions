import asyncio
import logging
import os
import sys

import nats
import requests

# -------------------
# Logging
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("broadcaster")

# -------------------
# Config
# -------------------
NATS_URL = os.getenv("NATS_URL", "nats://my-nats:4222")
BROADCASTER_MODE = os.getenv("BROADCASTER_MODE", "forward")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# -------------------
# Telegram
# -------------------
def notify(message: str):
    if BROADCASTER_MODE == "log-only":
        logger.info(f"(log-only) {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logger.info("Telegram notification sent")
    except Exception as e:
        logger.error(f"Telegram notify failed: {e}")


# -------------------
# NATS
# -------------------
async def main():
    nc = await nats.connect(NATS_URL, connect_timeout=5)
    logger.info(f"Connected to NATS at {NATS_URL}")
    logger.info("Saved locally")

    async def handler(msg):
        message = msg.data.decode()
        logger.info(f"Received: {message}")
        notify(message)

    await nc.subscribe(
        subject="todo-backend",
        queue="broadcasters",
        cb=handler,
    )

    logger.info("Subscriber started (queue=broadcasters)")

    # Block forever
    await asyncio.Event().wait()


# -------------------
# Entrypoint
# -------------------
if __name__ == "__main__":
    asyncio.run(main())
