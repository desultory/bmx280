from machine import I2C
from ustruct import calcsize, unpack
from time import sleep_ms
from math import ceil
from utime import ticks_ms


# Address for the BME280/BMP280
BMx_I2C_ADDRESS = 0x76


class BMx280:
    # Calibration data name, address start, and structure
    TRIMS = {'T': (0x88, 'Hhh'), 'P': (0x8E, 'Hhhhhhhhh'), 'H': (0xA1, 'B')}
    # Humidity trims are split across two addresses
    HUMIDITY_TRIMS = (0xE1, 'hBhhb')

    PRESSURE_RANGE = (30000, 110000)

    # 2 also works for forced mode
    MODES = {'sleep': 0, 'forced': 1, 'normal': 3}

    CONTROL_REGISTERS = {'id': 0xD0, 'reset': 0xE0, 'humidity': 0xF2, 'status': 0xF3, 'control': 0xF4, 'config': 0xF5}
    DATA_REGISTERS = {'pressure': (0xF7, 20), 'temperature': (0xFA, 20), 'humidity': (0xFD, 16)}

    SLEEP_MS = 10
    RETRY_COUNT = 100

    def __init__(self, i2c, i2c_address=BMx_I2C_ADDRESS, cache_ms=225,
                 init_mode='normal', t_oversample=5, p_oversample=5, h_oversample=5):
        """
        i2c: I2C object
        i2c_address: I2C address of the sensor
        init_mode: 'sleep', 'forced', or 'normal'
        h, t, p_oversample: Values from 0 to 5. The rate is 2**oversample capped at 16
        """
        if not isinstance(i2c, I2C):
            raise TypeError('I2C object required')
        self.cache_life = cache_ms
        self.i2c = i2c
        self.i2c_address = i2c_address
        self.t_oversample = t_oversample
        self.p_oversample = p_oversample
        self.h_oversample = h_oversample
        self.load_calibration_data()
        self.set_mode(init_mode)

    async def to_json(self):
        from json import dumps
        data = {'temperature': await self.temperature, 'pressure': await self.pressure}
        if self.humidity_sensor:
            data['humidity'] = await self.humidity
        return dumps(data)

    def __str__(self):
        from asyncio import run
        return run(self.to_json())

    def load_calibration_data(self):
        """ Load calibration data based on defined trims. Detect humidity sensor."""
        self.humidity_sensor = False
        for name, parameters in self.TRIMS.items():
            address, structure = parameters
            data = self._read_register(address, calcsize(structure))
            self.process_calibration_data(data, structure, name)

        # If the humidity register is non-zero, we have a humidity sensor, so process the trims
        if getattr(self, 'H1', 0) != 0:
            self.humidity_sensor = True
            address, structure = self.HUMIDITY_TRIMS
            data = self._read_register(address, calcsize(structure))
            self.process_calibration_data(data, structure, 'H', num=2)

    def process_calibration_data(self, data, structure, field_name, num=1, offset=0):
        for fmt in structure:
            data_size = calcsize(fmt)
            chunk = data[offset:offset + data_size]
            if field_name == 'H' and num == 4:
                # Mask off the unused bits, adjust the offset for the next read
                offset -= 1
                self.H4 = (chunk[0] * 16) | (chunk[1] & 0x0F)
            elif field_name == 'H' and num == 5:
                # Handle unwrapping the signed value
                self.H5 = (chunk[1] * 16) | (chunk[0] >> 4)
            else:
                value = unpack(fmt, chunk)
                setattr(self, f"{field_name}{num}", value[0])

            offset += data_size
            num += 1

    def _read_register(self, register, length=1):
        return bytearray(self.i2c.readfrom_mem(self.i2c_address, register, length))

    async def read_register(self, register, length=1):
        return self._read_register(register, length)

    def read_data(self):
        """ Read the temperature, pressure, and humidity data from the sensor. """
        retries = 0
        while await self.status != 'ready':
            sleep_ms(self.SLEEP_MS)
            retries += 1
            if retries > self.RETRY_COUNT:
                raise RuntimeError('Timed out waiting for sensor to become ready')

    async def get_data(self, data_type):
        if data_type not in self.DATA_REGISTERS:
            raise ValueError('Invalid data type: %s' % data_type)

        # Returns cached data if it's fresh
        if getattr(self, f"_raw_{data_type}", None) and ticks_ms() - getattr(self, f"_time_{data_type}") < self.cache_life:
            return getattr(self, f"_raw_{data_type}")

        self.read_data()
        register, length = self.DATA_REGISTERS[data_type]
        data = await self.read_register(register, ceil(length / 8))

        # Get the value from the most/least significant bits
        value = (data[0] << 8) + data[1]

        # Add the extended LSB if present
        if len(data) > 2:
            value = (value << 8) + data[2]

        if len(data) * 8 > length:
            # Shift off unused bits
            value = value >> (len(data) * 8 - length)

        # Write raw data to cache, and set the timestamp
        setattr(self, f"_raw_{data_type}", value)
        setattr(self, f"_time_{data_type}", ticks_ms())
        return value

    @property
    async def name(self):
        from re import compile, search
        rstr = compile(r'I2C\((\d), freq=(\d+), scl=(\d+), sda=(\d+).*\)')
        controller, freq, scl, sda = search(rstr, str(self.i2c)).groups()
        name = 'BME280' if self.humidity_sensor else 'BMP280'
        return f"{name}-{controller}:{self.i2c_address};{scl},{sda}"

    @property
    async def t_fine(self):
        await self.temperature  # Ensure the t_fine value is calculated
        return self._t_fine

    @property
    async def temperature(self):
        " Return the temperature in degrees Celsius. "
        raw_temp = await self.get_data('temperature')
        var1 = (((raw_temp / 8) - (self.T1 * 2)) * self.T2) / 2048
        var2 = (((((raw_temp / 16) - self.T1) ** 2) / 4096) * self.T3) / 16384
        self._t_fine = var1 + var2
        return (self._t_fine * 5 + 128) / 25600

    @property
    async def humidity(self):
        " Return the relative humidity in percent. "
        raw_humidity = await self.get_data('humidity')

        var1 = await self.t_fine - 76800
        var2 = raw_humidity * 16384
        var3 = self.H4 * 1048576
        var4 = self.H5 * var1
        var5 = (var2 - var3 - var4 + 16384) / 32768
        var2 = (var1 * self.H6) / 1024
        var3 = (var1 * self.H3) / 2046
        var4 = ((var2 * (var3 + 32768)) / 1024) + 2097152
        var2 = ((var4 * self.H2) + 8192) / 16384
        var3 = var5 * var2
        var4 = ((var3 / 32768) ** 2) / 128
        var5 = var3 - ((var4 * self.H1) / 16)
        var5 = 0 if var5 < 0 else 419430400 if var5 > 419430400 else var5
        return var5 / (2 ** 22)

    @property
    async def pressure(self):
        " Return the pressure in hPa. "
        raw_pressure = await self.get_data('pressure')

        var1 = (await self.t_fine / 2) - 64000
        var2 = (((var1 / 4) ** 2) / 2048) * self.P6
        var2 += (var1 * self.P5) * 2
        var2 = (var2 / 4) + (self.P4 * 65536)
        var3 = (self.P3 * ((var1 / 4) ** 2) / 8192) / 8
        var4 = (self.P2 * var1) / 2
        var1 = (var3 + var4) / 262144
        var1 = ((32768 + var1) * self.P1) / 32768

        if var1 == 0:
            return 0

        var5 = 1048576 - raw_pressure
        pressure = (var5 - (var2 / 4096)) * 3125
        if pressure < 0x80000000:
            pressure = (pressure * 2) / var1
        else:
            pressure = (pressure / var1) * 2

        var1 = (self.P9 * (((pressure / 8) ** 2) / 8192)) / 4096
        var2 = ((pressure / 4) * self.P8) / 8192
        pressure += (var1 + var2 + self.P7) / 16

        pressure_min, pressure_max = self.PRESSURE_RANGE
        if pressure < pressure_min:
            pressure = pressure_min
        elif pressure > pressure_max:
            pressure = pressure_max

        return pressure

    @property
    async def id(self):
        return await self.read_register(self.CONTROL_REGISTERS['id'])[0]

    @property
    async def status(self):
        # Bit 3 is measuring, bit 0 is im_update
        status = await self.read_register(self.CONTROL_REGISTERS['status'])[0]
        return 'measuring' if status & 0x08 else 'updating' if status & 0x01 else 'ready'

    @property
    async def mode(self):
        mode = await self.read_register(self.CONTROL_REGISTERS['control'])[0]
        if mode & 1 == 0:
            return 'sleep'
        elif mode & 11:
            return 'normal'
        else:
            return 'forced'

    def set_mode(self, value):
        if value not in self.MODES:
            raise ValueError('Invalid mode: %s' % value)
        if self.humidity_sensor:
            self.i2c.writeto_mem(self.i2c_address, self.CONTROL_REGISTERS['humidity'], bytes([self.h_oversample]))

        control = (self.t_oversample << 5) + (self.p_oversample << 2) + self.MODES[value]
        self.i2c.writeto_mem(self.i2c_address, self.CONTROL_REGISTERS['control'], bytes([control]))
