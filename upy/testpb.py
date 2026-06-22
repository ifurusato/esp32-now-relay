
import time
from push_button import PushButton

def callback(value):
    print('pushed: {}'.format(value))

btn = PushButton(5, callback)

while True:
    time.sleep(0.5)
