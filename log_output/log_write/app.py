import random
import string
import time
from datetime import datetime

s = "".join(random.choices(string.ascii_letters + string.digits, k=12))

while True:
    with open("/usr/src/app/files/log.txt", "w") as f:
        f.write(f"{datetime.now().isoformat()} {s}")
    time.sleep(5)
