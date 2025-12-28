import os
import time

import requests

URL = os.environ.get("IMAGE_URL", "https://picsum.photos/1200")
IMAGE_PATH = os.environ.get("IMAGE_WRITE_PATH", "/usr/src/app/files/image.jpg")
SLEEP_INTERVAL = int(os.environ.get("SLEEP_INTERVAL", "600"))

print("Built in GitHub actions and pushed to Artifact Registry", flush=True)

while True:
    response = requests.get(URL)

    with open(IMAGE_PATH, "wb") as f:
        f.write(response.content)

    print("Saved image", flush=True)
    time.sleep(SLEEP_INTERVAL)
