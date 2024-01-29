from machine import Pin, I2C
from bmx280 import BMx280

I2C_FREQ = 400_000

SENSORS = {118: BMx280,
           119: BMx280}


class SensorController:
    def __init__(self, i2c_controllers, ignore_missing=False, interval=500):
        self.i2c_controllers = i2c_controllers
        self.ignore_missing = ignore_missing
        self.interval = interval
        self.scan_devices()

    def scan_devices(self):
        self.sensors = []
        for controller in self.i2c_controllers:
            freq = self.i2c_controllers[controller].get('freq', I2C_FREQ)
            sda, scl = self.i2c_controllers[controller]['pins']
            i2c = I2C(controller, scl=Pin(scl), sda=Pin(sda), freq=freq)
            devices = i2c.scan()
            if devices:
                self.add_devices(i2c, devices)
            elif not self.ignore_missing:
                raise OSError("No I2C devices found on controller: %s" % controller)

    def add_devices(self, controller, devices):
        for device in devices:
            if device in SENSORS:
                sensor = SENSORS[device](i2c=controller, i2c_address=device)
                self.sensors.append(sensor)
            elif not self.ignore_missing:
                raise OSError("Unknown device: %s" % device)

    async def to_json(self):
        from utime import ticks_ms, sleep_ms
        from json import dumps, loads

        current_time = ticks_ms()
        out_data = {}
        for sensor in self.sensors:
            out_data.update({await sensor.name: loads(str(sensor))})
        finish_time = ticks_ms()

        if finish_time - current_time < self.interval:
            sleep_ms(self.interval - (finish_time - current_time))

        return dumps(out_data)

    def __str__(self):
        from asyncio import run
        return run(self.to_json())
