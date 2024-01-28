from machine import Pin, I2C
from bmx280 import BMx280

I2C_FREQ = 400_000

SENSORS = {118: BMx280}


class SensorController:
    def __init__(self, i2c_controllers):
        self.i2c_controllers = i2c_controllers
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

    def add_devices(self, controller, devices):
        for device in devices:
            if device in SENSORS:
                self.sensors.append(SENSORS[device](controller))

    def __str__(self):
        from json import dumps, loads
        out_data = {}
        for sensor in self.sensors:
            out_data.update({sensor.name: loads(str(sensor))})
        return dumps(out_data)
