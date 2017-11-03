from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

import threading

from natsort import natsorted, ns
from influxdb import InfluxDBClient

import time
from datetime import timedelta
from dateutil import parser

influx_lock = threading.Lock()

DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
OUTPUT_FILE = 'temperatures.json'

DEBUG = True

app = Flask(__name__)

influx_lock = threading.Lock()

#
# @app.route("/register.php")
# def register():
#     db_client = InfluxDBClient('localhost', 8086, DB_USER, DB_PASSWORD, DB_NAME)
#
#     rack = request.args.get("rack")
#     temp_sensors = natsorted(filter(lambda k: "temp" in k, request.args))
#
#     if temp_sensors:
#         for temp_sensor in temp_sensors:
#             value = request.args.get(temp_sensor)
#             data = [{
#                 "measurement": "sensors",
#                 "fields": {
#                     "value": value
#                 },
#                 "tags": {
#                     "location": rack,
#                     "sensor": temp_sensor,
#                     "unit": "celsius",
#                     "sensor_type": "temperature"
#                 }
#             }]
#             try:
#                 db_client.write_points(data)
#             except:
#                 return jsonify({"status": "failure", "reason": "could not write in the DB"})
#     return jsonify({"status": "success", "update_count": len(temp_sensors)})


@app.route("/new_temp_reading", methods=['POST'])
def new_temp_reading():
    db_client = InfluxDBClient('localhost', 8086, DB_USER, DB_PASSWORD, DB_NAME)

    for key in ["sensor", "t", "v"]:
        if not key in request.json:
            return jsonify({"status": "failure", "reason": "missing \"%s\" parameter" % (key)})

    sensor_name = request.json["sensor"]
    filtered_sensor_name = sensor_name.replace(":", "")

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": request.json["v"]
        },
        "tags": {
            "location": "room exterior",
            # "sensor": "temp_ext_%s" % (request.json["sensor"]),
            "sensor": filtered_sensor_name,
            "unit": "celsius",
            "sensor_type": "temp"
        }
    }]

    influx_lock.acquire()
    failure = False
    try:
        db_client.write_points(data)
    except:
        failure = True

    db_client.close()
    influx_lock.release()

    if failure:
        return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


if __name__ == "__main__":

    print("Running the \"data register\" server")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8080, debug=DEBUG, threaded=True)


