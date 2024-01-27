from sensor_controller import SensorController
from machine import reset
from utime import sleep_ms


s = SensorController()

while True:
    print(s)
    sleep_ms(250)

reset()
