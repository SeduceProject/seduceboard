import yaml

# import json
# JSON_CLUSTER_TEMPERATURE_CONFIGURATION_PATH = "conf/g5k/nantes/ecotype/temperature.json"


def get_temperature_sensors_infrastructure():
    # result = {}
    # with open(JSON_CLUSTER_TEMPERATURE_CONFIGURATION_PATH) as data_file:
    #     cluster_data = json.load(data_file)
    #     print("ici")
    #     for rack_id, rack_data in cluster_data.iteritems():
    #         for side, rack_side_data in rack_data.iteritems():
    #             rack_side_id = ("%s.%s" % (rack_id, side)).lower()
    #             positions = dict([(v["serie"], int(k)) for (k, v) in rack_side_data.iteritems()])
    #             positions_index = dict([(int(k), v["serie"]) for (k, v) in rack_side_data.iteritems()])
    #             sensors_series = [v["serie"] for (k, v) in rack_side_data.iteritems()]
    #             result[rack_side_id] = {
    #                 "rack": rack_side_id,
    #                 "sensors": sensors_series,
    #                 "positions": positions,
    #                 "positions_index": positions_index
    #             }
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
    return result
