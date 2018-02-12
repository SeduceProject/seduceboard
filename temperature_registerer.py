from flask import Flask
from flask import request
from flask import jsonify
from core.data.db import *

import threading
from influxdb import InfluxDBClient
import traceback

influx_lock = threading.Lock()

DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
OUTPUT_FILE = 'temperatures.json'

DEBUG = True

app = Flask(__name__)

influx_lock = threading.Lock()


@app.route("/new_temp_reading", methods=['POST'])
def new_temp_reading():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

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
    failure = False
    try:
        db_client.write_points(data)
    except:
        traceback.print_exc()
        failure = True

    db_client.close()
    influx_lock.release()

    if failure:
        return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


@app.route("/temperature/list", methods=['POST'])
def temperature_list():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

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

    if len(data) > 0:
        influx_lock.acquire()
        failure = False
        try:
            db_client.write_points(data)
        except:
            traceback.print_exc()
            failure = True

        db_client.close()
        influx_lock.release()

    if failure:
        return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


if __name__ == "__main__":

    print("Running the \"temperature registerer\" server")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)


