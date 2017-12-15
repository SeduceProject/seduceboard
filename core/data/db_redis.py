import redis
import json


REDIS_HOST = "192.168.1.8"
#REDIS_PORT = 8086
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_USER = 'root'
REDIS_PASSWORD = 'root'
REDIS_NAME = 'pidiou'


def redis_set_sensor_error_count(sensor_name, error_count):
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    sensor_key = "sensors_data"
    sensors_data_str = redis_client.get(sensor_key)

    if sensors_data_str is not None:
        sensors_data = json.loads(sensors_data_str)
    else:
        sensors_data = {}

    if sensor_name not in sensors_data:
        sensors_data[sensor_name] = {}

    sensor_data = sensors_data[sensor_name]

    if "error_count" not in sensor_data:
        sensor_data["error_count"] = 0
    sensor_data["error_count"] = error_count

    sensors_data_str_new = json.dumps(sensors_data)
    redis_client.set(sensor_key, sensors_data_str_new)

    return sensor_data


def redis_increment_sensor_error_count(sensor_name):
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    sensor_key = "sensors_data"
    sensors_data_str = redis_client.get(sensor_key)

    if sensors_data_str is not None:
        sensors_data = json.loads(sensors_data_str)
    else:
        sensors_data = {}

    if sensor_name not in sensors_data:
        sensors_data[sensor_name] = {}

    sensor_data = sensors_data[sensor_name]

    if "error_count" not in sensor_data:
        sensor_data["error_count"] = 0
    sensor_data["error_count"] += 1

    sensors_data_str_new = json.dumps(sensors_data)
    redis_client.set(sensor_key, sensors_data_str_new)

    return sensor_data


def redis_get_sensor_error_count(sensor_name):
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    sensor_key = "sensors_data"
    sensors_data_str = redis_client.get(sensor_key)

    if sensors_data_str is not None:
        sensors_data = json.loads(sensors_data_str)
    else:
        return 0

    if sensor_name not in sensors_data:
        return 0

    sensor_data = sensors_data[sensor_name]

    if "error_count" not in sensor_data:
        return 0
    return sensor_data["error_count"]


def redis_get_sensors_data():
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    sensor_key = "sensors_data"
    sensors_data_str = redis_client.get(sensor_key)

    if sensors_data_str is None:
        return {}

    result = json.loads(sensors_data_str)
    return result


def redis_get_sensors_names():
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    sensor_key = "sensors_data"
    sensors_data_str = redis_client.get(sensor_key)

    if sensors_data_str is None:
        return {}

    result = json.loads(sensors_data_str).keys()
    return result


if __name__ == "__main__":

    print(redis_get_sensors_data())
    redis_set_sensor_error_count("toto", 33)
    n = redis_get_sensor_error_count("toto")
    print(n)
    redis_increment_sensor_error_count("toto")
    n = redis_get_sensor_error_count("toto")
    print(n)
    print(redis_get_sensors_names())
