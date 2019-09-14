from __future__ import absolute_import, unicode_literals

import traceback
import sys
import re

import time
import threading
from core.config.crawlers_config import get_snmp_sensors
from threading import Timer
import subprocess

from docopt import docopt
from core.data.influx import *

NO_PAUSE = -1

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


def read_one_snmp_sensor(sensor_config):
    global influx_lock
    global RECORDS

    sensor_name = sensor_config.get("name")
    print("Crawling '%s'" % sensor_name)

    timestamp = int(time.time())

    sensor_ip = sensor_config["ip"]
    sensor_oid = sensor_config["oid"]
    sensor_index = sensor_config["index"]

    sensor_unit = sensor_config.get("unit")
    sensor_type = sensor_config.get("sensor_type")

    snmpget_cmd = "snmpget -v2c -c public %s " % (sensor_ip)
    snmpget_cmd += " %s.%s" % (sensor_oid, sensor_index)

    # Execute the snmpget command
    snmp_output = subprocess.check_output([x for x in snmpget_cmd.split(" ") if x != ''])
    snmp_output_str = snmp_output.decode("utf8")

    # Find the values returned by snmpget
    sensor_value = None
    for line in snmp_output_str.split("\n"):

        address_and_type, value = snmp_output_str.split(": ")

        if "INTEGER" in address_and_type:
            outlet_value = value
        elif "STRING" in address_and_type:
            outlet_value = value.replace("\"", "")
        else:
            continue

        sensor_value = float(outlet_value)
        print(sensor_value)

    # Prepare a database record for each of the outlets
    data = []

    if "pdu" in sensor_config.get("name"):
        location, pdu_short_id = sensor_config.get("name").split("_pdu-")
    else:
        location = sensor_config.get("name")

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

        readers = []
        for sensor_config in snmp_sensors:
            if pdu_candidate not in sensor_config.get("name"):
                continue

            last_pdu_reader = None
            time.sleep(0.1)
            reader = set_interval(read_one_snmp_sensor, (sensor_config), 1)
            readers += [reader]

        flusher = set_interval(flush_records, (snmp_sensors), 30)
        readers += [flusher]

        for reader in readers:
            reader.join()

        sys.exit(0)
