from flask import Flask
from flask import request
from flask import jsonify
from core.data.db import *

import time
import threading
from influxdb import InfluxDBClient
import traceback
from threading import Timer

influx_lock = threading.Lock()

NO_PAUSE = -1
# DB_USER = 'root'
# DB_PASSWORD = 'root'
# DB_NAME = 'pidiou'
# OUTPUT_FILE = 'temperatures.json'

DEBUG = True
RECORDS = []

app = Flask(__name__)

influx_lock = threading.Lock()


@app.route("/new_temp_reading", methods=['POST'])
def new_temp_reading():
    global influx_lock
    global RECORDS
    # db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    for key in ["sensor", "t", "v"]:
        if not key in request.json:
            return jsonify({"status": "failure", "reason": "missing \"%s\" parameter" % (key)})

    sensor_name = request.json["sensor"]
    filtered_sensor_name = sensor_name.replace(":", "")
    temperature = float(request.json["v"])

    if temperature > 60 or temperature < 10:
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

    # influx_lock.acquire()
    # failure = False
    # try:
    #     db_client.write_points(data)
    # except:
    #     traceback.print_exc()
    #     failure = True
    #
    # db_client.close()
    # influx_lock.release()

    # if failure:
    #     return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


@app.route("/temperature/list", methods=['POST'])
def temperature_list():
    global influx_lock
    global RECORDS

    # db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    data = []
    for obj in request.json:
        for key in ["sensor", "t", "v"]:
            if key not in obj:
                return jsonify({"status": "failure", "reason": "missing \"%s\" parameter" % (key)})

        sensor_name = obj["sensor"]
        filtered_sensor_name = sensor_name.replace(":", "")
        temperature = float(obj["v"])

        if temperature > 60 or temperature < 10:
            from core.data.db_redis import redis_increment_sensor_error_count
            redis_increment_sensor_error_count(filtered_sensor_name)
            return jsonify({"status": "failure", "reason": "incorrect temperature value %d (%s)" % (temperature, filtered_sensor_name)})

        data += [{
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

    # if len(data) > 0:
    #     influx_lock.acquire()
    #     failure = False
    #     try:
    #         db_client.write_points(data)
    #     except:
    #         traceback.print_exc()
    #         failure = True
    #
    #     db_client.close()
    #     influx_lock.release()

    influx_lock.acquire()
    RECORDS += data
    influx_lock.release()

    # if failure:
    #     return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


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

    print("Running the \"temperature registerer\" server")

    set_interval(flush_records, (None), 30, task_name="influx")

    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)


