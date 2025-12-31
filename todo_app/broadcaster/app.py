import asyncio
import logging
import os
import sys

import nats
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("broadcaster")

NATS_URL = os.getenv("NATS_URL", "nats://my-nats:4222")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def notify(message):
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(telegram_api_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram notification sent: {message}")
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")


async def main():
    nc = await nats.connect(NATS_URL)
    logger.info(f"Connected to NATS at {NATS_URL}")

    async def handler(msg):
        message = msg.data.decode()
        logger.info(f"Received message from subscriber: {message}")
        notify(message)

    await nc.subscribe("todo-backend", queue="broadcasters", cb=handler)
    logger.info("Subscriber started with queue group 'broadcasters'")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
