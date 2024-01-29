from sensor_controller import SensorController
from machine import reset
from utime import sleep_ms
from machine import Pin, freq

led = Pin(25, Pin.OUT)
missing_toggle = Pin(16, Pin.IN)
missing_pwr = Pin(17, Pin.OUT)
missing_pwr.value(1)

i2c_controllers = {0: {'pins': (0, 1)},
                   1: {'pins': (26, 27)}}

ignore_missing = bool(missing_toggle.value())

try:
    s = SensorController(i2c_controllers, ignore_missing=ignore_missing, interval=250)
except Exception as e:
    print(e)
    for _ in range(50):
        led.toggle()
        sleep_ms(50)
    reset()

do_reset = False

freq(50_000_000)

while True:
    try:
        led.toggle()
        print(s)
    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            do_reset = True
            break

if do_reset:
    reset()
