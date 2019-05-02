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
    timestamp = int(time.time())

    sensor_name = sensor_config.get("name")
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
        line = re.sub(r'.*\.9\.4\.3\.1\.7\.', '', line)
        line = re.sub(r'INTEGER: ', '', line)
        line = line.strip()
        if len(line) == 0:
            continue
        (outlet_oid_suffix, outlet_value) = line.split(" = ")
        sensor_value = float(outlet_value)

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


def set_interval(f, args, interval_secs, task_name=None):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False
            self.daemon = True

        def run(self):
            start_task_time = time.time()
            try:
                self.f(self.args)
            except:
                traceback.print_exc()
                print("Something bad happened here :-(")
                pass
            end_task_time = time.time()
            print("[sched:%s] took %f seconds to execute the task (starting: %f)" % (task_name, (end_task_time - start_task_time), start_task_time))
            time_to_sleep = (self.interval) - (end_task_time - start_task_time)
            if interval_secs != NO_PAUSE and time_to_sleep > 0:
                Timer(time_to_sleep, self.run).start()
            else:
                self.run()

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval_secs)
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

            print("I will start crawling '%s'" % pdu_candidate)
            last_pdu_reader = None
            time.sleep(0.1)
            reader = set_interval(read_one_snmp_sensor, (sensor_config), 1, task_name="pdus_crawler")
            readers += [reader]

            break

        flusher = set_interval(flush_records, (snmp_sensors), 30, task_name="influx")
        readers += [flusher]

        for reader in readers:
            reader.join()

        sys.exit(0)
