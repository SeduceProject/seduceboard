from __future__ import absolute_import, unicode_literals

import threading
import time
import traceback

import requests
from influxdb import InfluxDBClient
from pyModbusTCP.client import ModbusClient

from core.data.influx import *

DEBUG = True
LAST_TIMESTAMP_INSERTED = {}


def modbus_read_int(client, address, nb_char):
    result = 0
    regs = client.read_holding_registers(address, nb_char)
    if regs:
        factor = len(regs)
        for i in range(0, len(regs)):
            factor -= 1
            result += regs[i] * (2 ** (factor * 16))
        return result
    else:
        return -1


def new_modbus_reading(config):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    modbus_ip = config["ip"]
    modbus_register = config["register"]

    sensor_name = config.get("name", config["generated_sensor_id"])
    sensor_type = config["sensor_type"]
    sensor_unit = config["unit"]
    sensor_location = config.get("location", "not specified")
    divide_factor = config.get("modbus_divide_by", 1)

    insertion_count = 0

    modbus_client = ModbusClient(host=modbus_ip, port=502, auto_open=True, auto_close=True)

    try:
        sensor_value = modbus_read_int(modbus_client, modbus_register, 2) / divide_factor
    except:
        traceback.print_exc()
        print("[%s] failed to read a value from socomec (%s:%s:%s)" % (sensor_name,
                                                                       modbus_ip,
                                                                       sensor_unit,
                                                                       modbus_register))
        return {"status": "failure", "reason": "could not read socomec (%s:%s:%s)" % (modbus_ip,
                                                                                      sensor_unit,
                                                                                      modbus_register)}
    if sensor_value is None:
        print("[%s] failed to read an accurate value (%s)"
              " from socomec (%s:%s)" % (sensor_name,
                                            sensor_value,
                                            modbus_ip,
                                            modbus_register))
        return {"status": "failure",
                "reason": "failed to read an accurate (%s) value"
                          " from socomec (%s:%s:%s)" % (sensor_name,
                                                        modbus_ip,
                                                        modbus_register)}

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": float(sensor_value)
        },
        "tags": {
            "location": sensor_location,
            "sensor": sensor_name,
            "unit": sensor_unit,
            "sensor_type": sensor_type
        }
    }]

    try:
        failure = not db_client.write_points(data, time_precision="s")
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    if failure:
        print("[%s] failed to insert rows in the database" % (sensor_name))
        return {"status": "failure", "reason": "could not write in the DB"}
    else:
        insertion_count += 1

    print("[%s] %s rows have been inserted in the database" % (sensor_name, insertion_count))
    return {"status": "success", "update_count": insertion_count}


def set_interval(f, args, interval):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False

        def run(self):
            while not self.stop_execution:
                try:
                    self.f(self.args)
                except:
                    traceback.print_exc()
                    print("Something bad happened here :-(")
                    pass
                time.sleep(self.interval)

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval)
    t.start()
    return t


if __name__ == "__main__":
    from core.config.crawlers_config import get_modbus_sensors

    modbus_readers = []
    for config in get_modbus_sensors():
        modbus_readers += [set_interval(new_modbus_reading, (config), 1)]

        # To prevent all sensors to crawl in parallel
        time.sleep(2)

    try:
        for modbus_reader in modbus_readers:
            modbus_reader.join()
    except:
        for modbus_reader in modbus_readers:
            modbus_reader.stop()

