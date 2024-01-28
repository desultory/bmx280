from sensor_controller import SensorController
from machine import reset
from utime import sleep_ms

i2c_controllers = {0: {'pins': (0, 1)},
                   1: {'pins': (26, 27)}}

try:
    s = SensorController(i2c_controllers)
except Exception as e:
    print(e)
    reset()

do_reset = False


while True:
    try:
        print(s)
    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            do_reset = True
            break
    sleep_ms(250)

if do_reset:
    reset()
