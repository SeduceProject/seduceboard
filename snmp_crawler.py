from __future__ import absolute_import, unicode_literals

import traceback
import sys
import subprocess
import time
import threading
from core.config.crawlers_config import get_snmp_sensors
from itertools import groupby

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


def chunks(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]


def read_all_sensors(snmp_sensors, group_calls_factor=1):
    global influx_lock
    global RECORDS

    data = []

    ip_candidates = list(set([sensor.get("ip") for sensor in snmp_sensors]))
    if len(ip_candidates) > 1:
        raise Exception("ip candidates are too numerous: %s, I don't know which sensor I should contact!" % ip_candidates)
    sensor_ip = ip_candidates[0]

    oids_sensors_map = dict([
        (sensor.get('name'), "%s.%s" % (sensor.get('oid'), sensor.get('index')))
        for sensor in snmp_sensors
    ])

    sensors_names = " ".join(oids_sensors_map.keys())
    oids = oids_sensors_map.values()

    oids = chunks(list(oids), group_calls_factor)

    print("Crawling %s" % (sensors_names))

    timestamp = int(time.time())

    snmpget_cmd = ""

    for oid in oids:
        snmpget_cmd += "snmpget -On -v2c -c public %s %s; " % (sensor_ip, " ".join(oid))

    # Execute the snmpget command
    try:
        snmp_output = subprocess.check_output(snmpget_cmd, shell=True)
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
                before = time.time()
                try:
                    self.f(*self.args)
                except:
                    traceback.print_exc()
                    print("Something bad happened here :-(")
                    pass
                execution_duration = time.time() - before
                time_to_wait = self.interval - execution_duration
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval)
    t.start()
    return t


if __name__ == "__main__":

    help = """PDUs crawler

Usage:
  pdus_crawler.py --pdu=<pdu> [--mode=<mode>] [--group_calls_factor=<mode>]
  pdus_crawler.py -l

Options:
  -h --help          Show this message and exit.
  -l --list          List PDUs that can be crawled.
"""
    arguments = docopt(help)
    snmp_sensors = get_snmp_sensors()

    mode = arguments.get("--mode", "parallel")
    group_calls_factor_arg = arguments.get("--group_calls_factor", "1")

    if group_calls_factor_arg and str.isdigit(group_calls_factor_arg):
        group_calls_factor = int(group_calls_factor_arg)

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
        if mode == "iterative":
            snmp_readers += [set_interval(read_all_sensors, (selected_sensors, group_calls_factor, ), 1)]
        else:
            for selected_sensor in selected_sensors:
                snmp_readers += [set_interval(read_all_sensors, ([selected_sensor], ), 1)]

        flusher = set_interval(flush_records, (selected_sensors, ), 30)

        for snmp_reader in snmp_readers:
            snmp_reader.join()

        sys.exit(0)
