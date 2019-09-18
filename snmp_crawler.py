from __future__ import absolute_import, unicode_literals

import traceback
import sys
import subprocess
import time
import threading
from core.config.crawlers_config import get_snmp_sensors

from docopt import docopt
from core.data.influx import *

NO_PAUSE = -1
SENSOR_ERROR_PAUSE_S = 3.0

DEBUG = True
LAST_TIMESTAMP_INSERTED = {}

RECORDS = []

influx_lock = threading.Lock()


def process_one_outlet(sensor_name, sensor_location, timestamp, sensor_value, sensor_unit, sensor_type):

    try:
        float(sensor_value)
    except:
        print("something wrong happened here :-(")

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": float(sensor_value),
        },
        "time": timestamp,
        "tags": {
            "location": sensor_location,
            "sensor": sensor_name,
            "unit": sensor_unit,
            "sensor_type": sensor_type
        }
    }]

    return data


def flush_records(args):
    global influx_lock
    global RECORDS
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    influx_lock.acquire()
    flush_data = RECORDS
    RECORDS = []
    influx_lock.release()

    try:
        db_client.write_points(flush_data, time_precision="s")
        print("[influx] %s rows have been inserted in the database" % (len(flush_data)))
    except :
        traceback.print_exc()

    db_client.close()

    return False


def read_all_sensors(snmp_sensors):
    global influx_lock
    global RECORDS

    data = []

    oids_sensors_map = dict([
        (sensor.get('name'), "%s.%s" % (sensor.get('oid'), sensor.get('index')))
        for sensor in snmp_sensors
    ])

    oids = " ".join(oids_sensors_map.values())
    sensors_names = " ".join(oids_sensors_map.keys())

    print("Crawling %s" % (sensors_names))

    timestamp = int(time.time())

    ip_candidates = list(set([sensor.get("ip") for sensor in snmp_sensors]))
    if len(ip_candidates) > 1:
        raise Exception("ip candidates are too numerous: %s, I don't know which sensor I should contact!" % ip_candidates)
    sensor_ip = ip_candidates[0]

    snmpget_cmd = "snmpget -On -v2c -c public %s %s" % (sensor_ip, oids)

    # Execute the snmpget command
    try:
        snmp_output = subprocess.check_output([x for x in snmpget_cmd.split(" ") if x != ''])
    except subprocess.CalledProcessError:
        print("There was an error when contacting the sensor, I will wait %s seconds" % (SENSOR_ERROR_PAUSE_S))
        time.sleep(SENSOR_ERROR_PAUSE_S)
        return True

    snmp_output_str = snmp_output.decode("utf8")

    # Find the values returned by snmpget
    for line in snmp_output_str.split("\n"):

        if "=" not in line:
            continue

        address_and_type, value = line.split(": ")
        address, data_type = address_and_type.split(" = ")

        if "INTEGER" in data_type:
            outlet_value = value
        elif "STRING" in data_type:
            outlet_value = value.replace("\"", "")
        else:
            continue

        sensor_value = float(outlet_value)
        print(sensor_value)

        [corresponding_sensor] = [sensor for sensor in snmp_sensors if ".%s.%s" % (sensor.get("oid"), sensor.get("index")) == address]

        # Prepare a database record for the current value
        sensor_name = corresponding_sensor.get("name")
        sensor_unit = corresponding_sensor.get("unit")
        sensor_type = corresponding_sensor.get("type")

        if "pdu" in corresponding_sensor.get("name"):
            location, pdu_short_id = corresponding_sensor.get("name").split("_pdu-")
        else:
            location = corresponding_sensor.get("name")

        data += process_one_outlet(sensor_name, location, timestamp, sensor_value, sensor_unit, sensor_type)

    # Put the outlets' consumption values in the list of values that should be inserted in DB
    influx_lock.acquire()
    RECORDS += data
    influx_lock.release()

    return False


def set_interval(f, args, interval):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False
            self.daemon = True

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

    help = """PDUs crawler

Usage:
  pdus_crawler.py --pdu=<pdu>
  pdus_crawler.py -l

Options:
  -h --help          Show this message and exit.
  -l --list          List PDUs that can be crawled.
"""
    arguments = docopt(help)
    snmp_sensors = get_snmp_sensors()

    if arguments["--list"]:
        print("Available pdus:")
        for pdu_name in snmp_sensors:
            print("  %s" % pdu_name)
        pass
        sys.exit(0)
    else:
        pdu_candidate = arguments["--pdu"]

        selected_sensors = [sensor for sensor in snmp_sensors if pdu_candidate in sensor.get("name")]

        snmp_readers = []
        for selected_sensor in selected_sensors:
            snmp_readers += [set_interval(read_all_sensors, ([selected_sensor]), 1)]

        flusher = set_interval(flush_records, (selected_sensors), 30)

        for snmp_reader in snmp_readers:
            snmp_reader.join()

        sys.exit(0)
