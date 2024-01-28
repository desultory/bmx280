from sensor_controller import SensorController
from machine import reset
from utime import sleep_ms

i2c_controllers = {0: {'pins': (0, 1)},
                   1: {'pins': (26, 27)}}

s = SensorController(i2c_controllers)

while True:
    print(s)
    sleep_ms(250)

reset()
