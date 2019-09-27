from flask import Flask
from flask import request
from flask import jsonify
from core.data.influx import *
import threading
from core.data.redis_counters import redis_increment_sensor_error_count
import sys
import time
import threading
from influxdb import InfluxDBClient
import traceback
from threading import Timer

DEBUG = True
RECORDS = []

app = Flask(__name__)

influx_lock = threading.Lock()

TIME_LAST_UPDATE = None
FLUSH_FREQUENCY_SECONDS = 1.0


@app.route("/temperature/list", methods=['POST'])
def temperature_list():
    global influx_lock
    global RECORDS
    global TIME_LAST_UPDATE

    data = []
    for obj in request.json:
        for key in ["sensor", "t", "v"]:
            if key not in obj:
                return jsonify({"status": "failure", "reason": "missing \"%s\" parameter" % (key)})

        sensor_name = obj["sensor"]
        filtered_sensor_name = sensor_name.replace(":", "")
        temperature = float(obj["v"])
        timestamp = int(time.time())

        if temperature > 75 or temperature < -10:
            redis_increment_sensor_error_count(filtered_sensor_name)
            return jsonify({"status": "failure", "reason": "incorrect temperature value %d (%s)" % (temperature, filtered_sensor_name)})

        data += [{
            "measurement": "sensors",
            "fields": {
                "value": temperature
            },
            "time": timestamp,
            "tags": {
                "location": "room exterior",
                "sensor": filtered_sensor_name,
                "unit": "celsius",
                "sensor_type": "temperature"
            }
        }]

    now = time.time()
    influx_lock.acquire()
    RECORDS += data
    if TIME_LAST_UPDATE is None or now - TIME_LAST_UPDATE > FLUSH_FREQUENCY_SECONDS:
        flush_records()
        TIME_LAST_UPDATE = now
    influx_lock.release()

    return jsonify({"status": "success", "update_count": len(data)})


def flush_records():
    global influx_lock
    global RECORDS
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    flush_data = None

    flush_data = RECORDS[:]
    RECORDS = []

    try:
        failure = not db_client.write_points(flush_data, time_precision="s")
        print("[influx] %s rows have been inserted in the database" % (len(flush_data)))
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    return False


if __name__ == "__main__":

    print("Running the \"temperature registerer\" server")

    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)

    sys.exit()

