from serial import Serial
import sys
import time
import re
import os
import threading
from threading import Timer
import traceback
import json

from docopt import docopt
from core.data.pdus import get_pdus, get_outlets, get_outlets_names
from core.data.db import *

BAUDRATE = 9600
NO_PAUSE = -1

RECORDS = []
influx_lock = threading.Lock()


def process_one_temperature_reading(msg):
    global RECORDS

    temperature_data = json.loads(msg)
    temperature = temperature_data["v"]
    sensor_name = temperature_data["sensor"]
    filtered_sensor_name = sensor_name.replace(":", "")

    if temperature >= 84:
        return []

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": temperature
        },
        "tags": {
            "location": "room exterior",
            "sensor": filtered_sensor_name,
            "unit": "celsius",
            "sensor_type": "temperature"
        }
    }]

    influx_lock.acquire()
    RECORDS += data
    influx_lock.release()

    return data


def flush_records(args):
    global influx_lock
    global RECORDS

    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    flush_data = None

    influx_lock.acquire()
    flush_data = RECORDS
    RECORDS = []
    influx_lock.release()

    try:
        failure = not db_client.write_points(flush_data, time_precision="s")
        print("[influx] %s rows have been inserted in the database" % (len(flush_data)))
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    return False


def set_interval(f, args, interval_secs, task_name=None):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False

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

    help = """Temperature serial crawler

    Usage:
      temperature_serial_crawler.py --serial=<serial>
      temperature_serial_crawler.py --list-serial

    Options:
      -h --help        Show this message and exit.
      --list-serial    List serial ports that can be crawled.
    """
    arguments = docopt(help)

    if arguments["--list-serial"]:
        files = [f for f in os.listdir('/dev') if re.match(r'.*tty(\.|.*USB|.*usb).*', f)]
        print("Available serial ports:")
        for file in files:
            print("  /dev/%s" % file)
        pass
        sys.exit(0)
    else:
        # Launch the background function that will be in charge of saving
        # data to the database
        set_interval(flush_records, ("Nothing"), 30, task_name="influx")

        serial_device_path = arguments["--serial"]

        with Serial(port=serial_device_path, baudrate=BAUDRATE, timeout=1, writeTimeout=1) as serial_port:
            if serial_port.isOpen():
                while True:
                    msg = serial_port.readline()
                    if """{"sensor":}""" in msg:
                        process_one_temperature_reading(msg)
    sys.exit(0)
