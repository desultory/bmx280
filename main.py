from machine import Pin, I2C
from bmx280 import BMx280
from utime import sleep_ms

bme_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400_000)
#bme_i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400_000)
bme = BMx280(bme_i2c)
#bmp = BMx280(bmp_i2c)

while True:
    print(bme)
#    print(bmp)
    sleep_ms(250)
