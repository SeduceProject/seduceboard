import yaml

SENSORS_ARRAYS = None
SENSORS = None


def load_sensors_arrays_data():
    global SENSORS_ARRAYS
    if SENSORS_ARRAYS is None:
        with open("conf/room_map.yaml") as f:
            SENSORS_ARRAYS = yaml.load(f)
    return SENSORS_ARRAYS


def load_sensors_data():
    global SENSORS
    if SENSORS is None:
        with open("conf/sensors.yaml") as f:
            SENSORS = yaml.load(f)
    return SENSORS


def get_sensors_arrays():
    room_data = load_sensors_arrays_data()
    return room_data


def get_sensors_array_by_name(name):
    room_data = load_sensors_arrays_data()
    return room_data.get(name, None)


def get_sensors_arrays_with_children():
    sensors_arrays = load_sensors_arrays_data()
    sensors = load_sensors_data()

    flatten_sensors_map = dict([(y.get("name"), y) for (k, v) in sensors.items() if k != "classes" for y in v.values()])

    for (sensors_array_name, sensors_array) in sensors_arrays.items():
        sensors_array["children"] = [flatten_sensors_map.get(s) for s in sensors_array.get("sensors")]

    return sensors_arrays


def get_sensors_in_sensor_array(parent):
    sensors_array = get_sensors_array_by_name(parent)
    sensors = load_sensors_data()

    flatten_sensors_map = dict([(y.get("name"), y) for (k, v) in sensors.items() if k != "classes" for y in v.values()])

    sensors = [flatten_sensors_map.get(s) for s in sensors_array.get("sensors")]
    return sensors


def get_sensor_by_name(name):
    sensors = load_sensors_data()

    flatten_sensors_map = dict([(y.get("name"), y) for (k, v) in sensors.items() if k != "classes" for y in v.values()])

    return flatten_sensors_map.get(name, None)


def get_sensors_array_from_sensor_name(sensor_name):
    sensor_arrays = load_sensors_arrays_data()

    sensor_array = [v for (k, v) in sensor_arrays.items() if sensor_name in v.get("sensors")][0]

    return sensor_array
