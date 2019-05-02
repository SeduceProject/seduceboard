import sys
import oyaml as yaml
import collections
import json


header = """
classes:

  wattmeter: &wattmeter
    sensor_type: wattmeter
    unit: W

  temperature: &temperature
    sensor_type: temperature
    unit: T

  modbus_inrow: &modbus_inrow
    method: modbus
    ip: 192.168.1.17
    parent: modbus_inrow

  watt_cooler_b232: &watt_cooler_b232
    <<: *wattmeter
    method: flukso
    ip: 192.168.1.65
    port: 8080
    location: B232
    parent: watt_cooler_b232

  watt_cooler_ext: &watt_cooler_ext
    <<: *wattmeter
    method: flukso
    ip: 192.168.1.3
    port: 8080
    location: B232
    parent: watt_cooler_ext

  socomec_server_room: &socomec_server_room
    <<: *wattmeter
    method: socomec
    ip: 192.168.1.8
    unit_id: 4
    location: B232
    parent: socomec_server_room

  temp_Z1_5_back: &temp_Z1_5_back
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_5_back
    rack: Z1.5
    side: back

  temp_Z1_5_front: &temp_Z1_5_front
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_5_front
    rack: Z1.5
    side: front

  temp_Z1_4_back: &temp_Z1_4_back
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_4_back
    rack: Z1.4
    side: back

  temp_Z1_4_front: &temp_Z1_4_front
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_4_front
    rack: Z1.4
    side: front

  temp_Z1_2_back: &temp_Z1_2_back
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_2_back
    rack: Z1.2
    side: back

  temp_Z1_2_front: &temp_Z1_2_front
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_2_front
    rack: Z1.2
    side: front

  temp_Z1_1_back: &temp_Z1_1_back
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_1_back
    rack: Z1.1
    side: back

  temp_Z1_1_front: &temp_Z1_1_front
    <<: *temperature
    method: temperature_push
    parent: temp_Z1_1_front
    rack: Z1.1
    side: front

  temp_additional_card1: &temp_additional_card1
    <<: *temperature
    method: temperature_push
    parent: temp_additional_card1
    rack: Z1.5
    side: front

  temp_room: &temp_room
    <<: *temperature
    method: temperature_push
    parent: temp_room
    rack: room
    side: top

  snmp_inrow: &snmp_inrow
    method: snmp
    ip: 192.168.1.17
    oid: 1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1
    array: true
    parent: snmp_inrow

  snmp_power_inrow: &snmp_power_inrow
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.17
    oid: 1.3.6.1.4.1.318.1.1.27.1.4.1.2.1.3.1
    array: true
    parent: snmp_power_inrow

  snmp_pdu_z151: &snmp_pdu_z151
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.12
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z151

  snmp_pdu_z150: &snmp_pdu_z150
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.11
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z150

  snmp_pdu_z141: &snmp_pdu_z141
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.10
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z141

  snmp_pdu_z140: &snmp_pdu_z140
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.5
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z140

  snmp_pdu_z121: &snmp_pdu_z121
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.16
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z121

  snmp_pdu_z120: &snmp_pdu_z120
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.15
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z120

  snmp_pdu_z111: &snmp_pdu_z111
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.14
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z111

  snmp_pdu_z110: &snmp_pdu_z110
    <<: *wattmeter
    method: snmp
    ip: 192.168.1.6
    oid: 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7
    array: true
    parent: snmp_pdu_z110
"""

if __name__ == "__main__":

    yaml_sensor_path = "conf/save/sensors.yaml"
    yaml_temperature_path = "conf/save/temperature.yaml"
    yaml_racks_path = "conf/save/racks.yaml"

    snmp_json_path = "conf/g5k/nantes/ecotype/snmp.json"

    with open(snmp_json_path) as f:
        snmp_json_data = json.load(f)

    with open(yaml_racks_path) as f:
        racks_data = yaml.load(f)

    with open(yaml_temperature_path) as f:
        temperature_data = yaml.load(f)

    CLASSES = {}

    with open(yaml_sensor_path) as f:
        sensors_arrays = yaml.load(f)

        print(header)

        for (sensor_array_name, sensors) in sensors_arrays.items():
            sensors_name = list(sensors)
            if sensor_array_name == "classes":
                CLASSES = sensors
                continue

            key_used_for_sorting = "parent"
            if "parent" not in sensors[sensors_name[0]]:
                key_used_for_sorting = "info"

            sorted_sensors_name = sorted(sensors_name, key=lambda s: sensors[s].get(key_used_for_sorting))
            sorted_sensors = [sensors[name] for name in sorted_sensors_name]

            for sensor_name, sensor_dict in sensors.items():
                parent_class = CLASSES[sensor_dict.get("parent")]
                sensor_dict["<<: *"] = sensor_dict.get("parent")

                if "index" in sensor_dict:
                    del sensor_dict["index"]

                if "temp_" in sensor_dict.get("parent", ""):
                    # Find position of the sensor
                    if "temp_additional_card1" == sensor_dict.get("parent", ""):
                        (position_str, temp_dict) = [(k,v) for (k,v) in temperature_data.get("Z1.5TC.exp").get(sensor_dict.get("side")).items() if sensor_dict.get("name") == v.get("serie")][0]
                    else:
                        (position_str, temp_dict) = [(k,v) for (k,v) in temperature_data.get(sensor_dict.get("rack")).get(sensor_dict.get("side")).items() if sensor_dict.get("name") == v.get("serie")][0]
                    position = int(position_str)
                    sensor_dict["position"] = position
                    # Find tags of the sensor
                    if "tags" in temp_dict:
                        sensor_dict["tags"] = temp_dict["tags"]

                    pass
                if "pdu" in sensor_dict.get("parent", ""):
                    # Find tags of the sensor
                    (component_name, pdu_full_name) = sensor_name.split("_pdu")

                    pdu_name = "pdu%s" % pdu_full_name

                    index, component_name_2 = [(k, v) for (k, v) in snmp_json_data.get(pdu_name).get("power").get("sensors").items() if v == component_name][0]

                    if component_name_2 != component_name:
                        raise Exception("server names don't match :-(")

                    sensor_dict["index"] = int(index)
                    sensor_dict["tags"] = []
                    sensor_dict["tags"] += [component_name]
                    # print("ici")
                    pass

            # sorted_sensors_dict = dict([(name,sensors[sensor_array_name][name]) for name in sorted_sensors_name])

            sorted_sensors_dict = collections.OrderedDict()

            if sensor_array_name == "temperature":
                def compute_weight(s):
                    if s.get("parent", "") in ["temp_additional_card1", "temp_room"]:
                        weight_rack = 10000
                        weight_side = 0
                    else:
                        weight_rack = int(s.get("rack").split(".")[1]) * 1000
                        weight_side = 0 if s.get("side") == "front" else 500
                    weight_position = s.get("position")
                    return weight_rack + weight_side + weight_position
                sorted_sensors_name = sorted(sensors_name, key=lambda s: compute_weight(sensors[s]))
                sorted_sensors = [sensors[name] for name in sorted_sensors_name]

                for sensor in sorted_sensors:
                    sorted_sensors_dict[sensor.get("name")] = sensor
            else:
                for sensor in sorted_sensors:
                    sorted_sensors_dict[sensor.get("name")] = sensor

            for sensor, sensor_dict in sorted_sensors_dict.items():
                for key in parent_class:
                    # remove duplicate keys
                    if key in sensor_dict:
                        del sensor_dict[key]

            yaml_result = \
                yaml.safe_dump(
                    {
                        sensor_array_name: sorted_sensors_dict
                    },
                    default_flow_style=False)
            yaml_result = yaml_result.replace("'<<: *': ", "<<: *")

            print(yaml_result)

    sys.exit(0)