# BMx280

A Micropython library for BME280 and BMX280 sensors.


## Usage

`SensorController` can be used to connect to multiple sensors.

An instance can be created using a dict of bus numbers and pins:

```

i2c_controllers = {0: {'pins': (0, 1)},
                   1: {'pins': (26, 27)}}

controller = SensorController(i2c_controllers, ignore_missing=True)
```

> `ignore_missing` will ignore empty busses and missing devices

Once created, all attached sensor's stats can be printed with:

```
print(controller)

{"BME280-0:118;1,0": {"pressure": 101363.4, "temperature": 22.28417, "humidity": 36.84885}, "BME280-1:118;27,26": {"pressure": 101429.8, "temperature": 22.10638, "humidity": 37.86998}, "BMP280-1:119;27,26": {"pressure": 101445.0, "temperature": 22.25535}}
```

Each sensor will have a key in the format:

`<SENSOR_NAME>-<CONTROLLER>:<ADDRESS>;<SCL>,<SCA>`


