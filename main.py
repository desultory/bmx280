from sensor_controller import SensorController
from machine import reset
from utime import sleep_ms
from machine import Pin, freq

led = Pin(25, Pin.OUT)

i2c_controllers = {0: {'pins': (0, 1)},
                   1: {'pins': (26, 27)}}

try:
    s = SensorController(i2c_controllers, ignore_missing=False, interval=250)
except Exception as e:
    print(e)
    for _ in range(50):
        led.toggle()
        sleep_ms(50)
    reset()

do_reset = False

freq(40_000_000)


while True:
    try:
        led.toggle()
        print(s.to_json())
    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            do_reset = True
            break

if do_reset:
    reset()
