from flask import Flask
from flask import request
from flask import jsonify
from core.data.db import *

import threading
from influxdb import InfluxDBClient

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

    if int(request.json["v"]) > 84:
        return jsonify({"status": "failure", "reason": "incorrect temperature value"})

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": request.json["v"]
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
        failure = True

    db_client.close()
    influx_lock.release()

    if failure:
        return jsonify({"status": "failure", "reason": "could not write in the DB"})

    return jsonify({"status": "success", "update_count": len(data)})


if __name__ == "__main__":

    print("Running the \"temperature registerer\" server")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8080, debug=DEBUG, threaded=True)


