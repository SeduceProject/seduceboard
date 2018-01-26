import sys
import time
import re
import os
import threading
from threading import Timer
import traceback
import json
import requests
from lxml import html

from docopt import docopt
from flask import jsonify
from core.data.db import *
from datetime import datetime


RECORDS = []
influx_lock = threading.Lock()
NO_PAUSE = -1


def process_one_temperature_reading(msg):
    global RECORDS

    try:
        temperature_data = json.loads(msg)
    except:
        print("Could not load JSON data from '%s'" % (msg))
        return []

    temperature = float(temperature_data["v"])
    sensor_name = temperature_data["sensor"]
    filtered_sensor_name = sensor_name.replace(":", "")

    if temperature > 84 or temperature < 10:
        from core.data.db_redis import redis_increment_sensor_error_count
        redis_increment_sensor_error_count(filtered_sensor_name)
        return jsonify({"status": "failure", "reason": "incorrect temperature value %d (%s)" % (temperature, filtered_sensor_name)})

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


def parse_float(str_value):
    try:
        return float(str_value)
    except:
        pass
    return None


if __name__ == "__main__":

    help = """Temperature orange crawler

    Usage:
      temperature_orange_crawler.py --ip=<ip>

    Options:
      -h --help        Show this message and exit.
    """
    arguments = docopt(help)

    # Launch the background function that will be in charge of saving
    # data to the database
    set_interval(flush_records, ("Nothing"), 30, task_name="influx")

    ip = arguments["--ip"]

    while True:
        response = requests.get("http://%s/?command=TableDisplay&table=Table1&records=100" % ip)
        response_text = response.text
        tree = html.fromstring(response_text.encode('utf8').strip())
        table_elements = tree.xpath('//table')

        if len(table_elements) == 1:
            table_dom = table_elements[0]

            tr_elements = table_dom.xpath('.//tr')
            row_num = 0
            for tr_element in tr_elements:
                row_timestamp_str = None
                row_time = None
                row_time_since_epoch = None

                th_elements = tr_element.xpath('.//th')
                td_elements = tr_element.xpath('.//td')

                if len(th_elements) > 0:
                    index = 0
                    row_index = {}
                    for th_element in th_elements:
                        row_index[index] = th_element.text
                        index += 1
                else:
                    column_num = 0
                    for td_element in td_elements:
                        if column_num == 0:
                            row_timestamp_str = td_element.text
                            row_time = datetime.strptime(row_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                            row_time_since_epoch = (row_time - datetime(1970, 1, 1)).total_seconds()
                        else:
                            column_label = row_index[column_num]
                            value = parse_float(td_element.text)
                            if value is not None:
                                print("%s %s -> %s" % (row_time_since_epoch, column_label, value))
                                pass
                        column_num += 1
                row_num += 1
    sys.exit(0)
