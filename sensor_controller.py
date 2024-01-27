from machine import Pin, I2C
from bmx280 import BMx280

I2C_FREQ = 400_000

I2C_CONTROLLERS = {0: {'pins': [(0, 1), (4, 5), (8, 9), (12, 13), (16, 17), (20, 21)],
                       'freq': I2C_FREQ},
                   1: {'pins': [(2, 3), (6, 7), (10, 11), (14, 15), (18, 19), (26, 27)],
                       'freq': I2C_FREQ}}

SENSORS = {118: BMx280}


class SensorController:
    def __init__(self, i2c_controllers=I2C_CONTROLLERS):
        self.i2c_controllers = i2c_controllers
        self.scan_devices()

    def scan_devices(self):
        for controller in self.i2c_controllers:
            freq = self.i2c_controllers[controller]['freq']
            for pins in self.i2c_controllers[controller]['pins']:
                i2c = I2C(controller, scl=Pin(pins[1]), sda=Pin(pins[0]), freq=freq)
                devices = i2c.scan()
                if devices:
                    self.add_devices(i2c, devices)
                    break

    def add_devices(self, controller, devices):
        self.sensors = []
        for device in devices:
            if device in SENSORS:
                print('Found device: {}'.format(device))
                print('Using controller: {}'.format(controller))
                self.sensors.append(SENSORS[device](i2c=controller))
            print(self.sensors)

    def __str__(self):
        from json import dumps, loads
        out_data = {}
        for sensor in self.sensors:
            out_data.update({sensor.name: loads(str(sensor))})
        return dumps(out_data)
