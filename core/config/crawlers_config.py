import yaml


def get_sensors_by_collect_method(collect_method):
    result = []
    with open("conf/sensors.yaml") as f:
        yaml_as_dict = yaml.load(f)
        # json_as_dict = json.load(f)
        for unit_name, unit_dict in yaml_as_dict.items():
            if unit_name == "classes":
                continue
            for sensor_name, sensor_dict in unit_dict.items():
                if sensor_dict.get("method", "ko") == collect_method:
                    generated_sensor_id = "%s.%s" % (unit_name, sensor_name)
                    sensor_dict["generated_sensor_id"] = generated_sensor_id
                    result += [sensor_dict]
    return result


def get_modbus_sensors():
    return get_sensors_by_collect_method("modbus")


def get_flukso_sensors():
    return get_sensors_by_collect_method("flukso")


def get_socomec_sensors():
    return get_sensors_by_collect_method("socomec")


def get_snmp_sensors():
    return get_sensors_by_collect_method("snmp")
