import time

import requests

URL = "https://picsum.photos/1200"
IMAGE_PATH = "/usr/src/app/files/image.jpg"

while True:
    response = requests.get(URL)

    with open(IMAGE_PATH, "wb") as f:
        f.write(response.content)

    print("Saved image", flush=True)
    time.sleep(600)
