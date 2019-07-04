import yaml

# import json
# JSON_CLUSTER_TEMPERATURE_CONFIGURATION_PATH = "conf/g5k/nantes/ecotype/temperature.json"

TEMPERATURE_SENSOR_INFRASTRUCTURE = None


def get_temperature_sensors_infrastructure():
    global TEMPERATURE_SENSOR_INFRASTRUCTURE
    if TEMPERATURE_SENSOR_INFRASTRUCTURE is None:

        result = {}
        with open("conf/sensors.yaml") as f:
            sensors = yaml.load(f)
            temperature_sensors = sensors["temperature"]
            for temperature_sensor_name, temperature_sensor in temperature_sensors.items():
                if temperature_sensor.get("exclude_from_rack_temperature_overview", False):
                    continue
                rack_side_key = ("%s.%s" % (temperature_sensor.get("rack"), temperature_sensor.get("side"))).lower()
                position = temperature_sensor.get("position")
                if rack_side_key not in result:
                    result[rack_side_key] = {
                        "positions": {},
                        "positions_index": {},
                        "rack": rack_side_key,
                        "sensors": []
                    }
                result[rack_side_key].get("positions")[temperature_sensor_name] = position
                result[rack_side_key].get("positions_index")[position] = temperature_sensor_name
                sensors = result[rack_side_key].get("sensors")
                sensors += [temperature_sensor_name]
        TEMPERATURE_SENSOR_INFRASTRUCTURE = result
    return TEMPERATURE_SENSOR_INFRASTRUCTURE
