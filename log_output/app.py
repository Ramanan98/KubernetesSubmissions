import time
import random
import string
from datetime import datetime

s = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
while True:
    print(datetime.now().isoformat(), s, flush=True)
    time.sleep(5)