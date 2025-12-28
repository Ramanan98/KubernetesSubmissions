import logging
import os
import sys
import time

import requests

logger = logging.getLogger("image-write")
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(stdout_handler)

URL = os.environ.get("IMAGE_URL", "https://picsum.photos/1200")
IMAGE_PATH = os.environ.get("IMAGE_WRITE_PATH", "/usr/src/app/files/image.jpg")
SLEEP_INTERVAL = int(os.environ.get("SLEEP_INTERVAL", "600"))

while True:
    response = requests.get(URL)

    with open(IMAGE_PATH, "wb") as f:
        f.write(response.content)

    logger.info("Saved image")
    time.sleep(SLEEP_INTERVAL)
