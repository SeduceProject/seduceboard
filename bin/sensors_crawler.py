from __future__ import absolute_import, unicode_literals

import threading
import time
import traceback

import requests
from pyModbusTCP.client import ModbusClient
from core.data.influx import get_influxdb_client
from core.collecters.utils import set_interval


DEBUG = True
LAST_TIMESTAMP_INSERTED = {}


def new_flukso_reading(config):
    global LAST_TIMESTAMP_INSERTED
    db_client = get_influxdb_client()

    flukso_name = config["name"]
    flukso_ip = config["ip"]
    flukso_port = config["port"]
    flukso_sensor_id = config["sensor_id"]
    flukso_info = config["info"]
    flukso_unit = config["unit"]
    flukso_sensor_type = config["sensor_type"]
    flukso_location = config["location"]

    flukso_url = "http://%s:%s/sensor/%s?version=1.0&interval=minute&unit=watt" % (flukso_ip,
                                                                                   flukso_port,
                                                                                   flukso_sensor_id)
    response_as_json = requests.get(flukso_url).json()

    insertion_count = 0

    if not flukso_name in LAST_TIMESTAMP_INSERTED:
        LAST_TIMESTAMP_INSERTED[flukso_name] = None

    for measure in response_as_json:
        if LAST_TIMESTAMP_INSERTED[flukso_name] is None or measure[0] > LAST_TIMESTAMP_INSERTED[flukso_name]:
            if (measure[1]) == "nan":
                continue

            data = [{
                "measurement": "sensors",
                "time": int(measure[0]),
                "fields": {
                    "value": float(measure[1])
                },
                "tags": {
                    "location": flukso_location,
                    "sensor": flukso_name,
                    "unit": flukso_unit,
                    "sensor_type": flukso_sensor_type
                }
            }]

            try:
                failure = not db_client.write_points(data, time_precision="s")
                LAST_TIMESTAMP_INSERTED[flukso_name] = measure[0]
            except :
                traceback.print_exc()
                failure = True

            db_client.close()

            if failure:
                print("[%s] failed to insert rows in the database" % (flukso_name))
                return {"status": "failure", "reason": "could not write in the DB"}
            else:
                insertion_count += 1

    print("[%s] %s rows have been inserted in the database" % (flukso_name, insertion_count))
    return {"status": "success", "update_count": insertion_count}


def socomec_read_int(client, address, nb_char):
    result = 0
    regs = client.read_holding_registers(address, nb_char)
    if regs:
        #print regs
        factor = len(regs)
        for i in range(0, len(regs)):
            factor -= 1
            result += regs[i] * (2 ** (factor * 16))
        return result
    else:
        return -1


def new_socomec_reading(config):
    db_client = get_influxdb_client()

    socomec_ip = config.get("ip")
    socomec_name = config.get("name")
    socomec_address = config.get("address")
    socomec_unit_id = config.get("unit_id")
    socomec_info = config.get("info")
    socomec_unit = config.get("unit")
    socomec_sensor_type = config.get("sensor_type")
    socomec_location = config.get("location")
    socomec_port = config.get("port", 502)

    insertion_count = 0

    modbus_client = None
    if 'unit_id' in config:
        modbus_client = ModbusClient(host=socomec_ip, port=socomec_port, unit_id=socomec_unit_id, auto_open=True, auto_close=True)
    else:
        modbus_client = ModbusClient(host=socomec_ip, port=socomec_port, auto_open=True, auto_close=True)

    try:
        socomec_value = socomec_read_int(modbus_client, socomec_address, 2)
    except:
        print("[%s] failed to read a value from socomec (%s:%s:%s)" % (socomec_name,
                                                                       socomec_ip,
                                                                       socomec_unit_id,
                                                                       socomec_address))
        return {"status": "failure", "reason": "could not read socomec (%s:%s:%s)" % (socomec_ip,
                                                                                      socomec_unit_id,
                                                                                      socomec_address)}
    if not socomec_value >= 0:
        print("[%s] failed to read an accurate (%s) value from socomec (%s:%s:%s)" % (socomec_name,
                                                                                      socomec_value,
                                                                                      socomec_ip,
                                                                                      socomec_unit_id,
                                                                                      socomec_address))
        return {"status": "failure",
                "reason": "failed to read an accurate (%s) value from socomec (%s:%s:%s)" % (socomec_value,
                                                                                             socomec_ip,
                                                                                             socomec_unit_id,
                                                                                             socomec_address)}

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": float(socomec_value)
        },
        "tags": {
            "location": socomec_location,
            "sensor": socomec_name,
            "unit": socomec_unit,
            "sensor_type": socomec_sensor_type
        }
    }]

    try:
        failure = not db_client.write_points(data, time_precision="s")
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    if failure:
        print("[%s] failed to insert rows in the database" % (socomec_name))
        return {"status": "failure", "reason": "could not write in the DB"}
    else:
        insertion_count += 1

    print("[%s] %s rows have been inserted in the database" % (socomec_name, insertion_count))
    return {"status": "success", "update_count": insertion_count}


if __name__ == "__main__":
    # from core.config.crawlers_config import WATTMETERS_CONFIG, SOCOMEC_CONFIG
    from core.config.crawlers_config import get_flukso_sensors, get_socomec_sensors

    readers = []
    for config in get_flukso_sensors():
        flukso_reader = set_interval(new_flukso_reading, (config), 1)
        readers += [flukso_reader]

        # To prevent all sensors to crawl in parallel
        time.sleep(2)

    for config in get_socomec_sensors():
        socomec_reader = set_interval(new_socomec_reading, (config), 1)
        readers += [socomec_reader]

        # To prevent all sensors to crawl in parallel
        time.sleep(2)

    for reader in readers:
        reader.join()
