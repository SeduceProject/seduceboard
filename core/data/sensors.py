from core.config.room_config import ROOM_CONFIG


def get_sensors_arrays():
    sensors_arrays = filter(lambda x: "parent" not in x, ROOM_CONFIG)
    return sensors_arrays


def get_sensors_arrays_with_children():
    sensors_arrays = filter(lambda x: "parent" not in x, ROOM_CONFIG)

    for sensors_array in sensors_arrays:
        sensors_array["children"] = filter(lambda x: "parent" in x and x["parent"] == sensors_array["name"], ROOM_CONFIG)

    return sensors_arrays


def get_sensors_in_sensor_array(parent):
    sensors = filter(lambda x: "parent" in x and x["parent"] == parent, ROOM_CONFIG)
    return sensors


def get_sensor_by_name(name):
    sensors = filter(lambda x: x["name"] == name, ROOM_CONFIG)
    if len(sensors) > 0:
        return sensors[0]
    else:
        return None
