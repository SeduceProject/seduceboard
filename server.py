from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from influxdb import InfluxDBClient
import time
from dateutil import parser
from datetime import timedelta
import random
import logging

# HOST = "192.168.1.8"
HOST = "127.0.0.1"
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
OUTPUT_FILE = 'temperatures.json'

DEBUG = True

app = Flask(__name__)


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@app.route("/sensor_data/<sensor_name>")
def sensor_data(sensor_name):
    from core.data.db import db_sensor_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date
        else:
            raise Exception("Invalid 'start_date' parameter: %s" % (start_date))

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date
        else:
            raise Exception("Invalid 'end_date' parameter: %s" % (end_date))

    zoom_ui = "zoom_ui" in request.args

    _sensor_data = db_sensor_data(sensor_name, start_date, end_date, zoom_ui)
    return jsonify(_sensor_data)


@app.route("/sensors")
@app.route("/sensors/all")
@app.route("/sensors/<sensor_type>")
def sensors(sensor_type=None):
    from core.data.db import db_sensors

    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date
    else:
        last_week_epoch = time.time() - (7 * 24 * 3600)
        start_date = "%s" % last_week_epoch

    _sensors = db_sensors(start_date, sensor_type=sensor_type)
    return jsonify(_sensors)


@app.route("/sensors_types")
@app.route("/sensor_types")
def sensor_types():
    from core.data.db import db_sensor_types

    _sensor_types = db_sensor_types()
    return jsonify(_sensor_types)


@app.route("/multitree/root")
def multitree_root_nodes():
    from core.data.multitree import get_root_nodes
    return jsonify(get_root_nodes())


@app.route("/multitree/query/tree/<node_id>")
def multitree_tree_query(node_id):
    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_tree
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        tree = get_tree(starting_node)
        return jsonify(tree)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@app.route("/multitree/query/sensors/<node_id>")
def multitree_sensors_query(node_id):
    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_sensors_tree
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        sensors = get_sensors_tree(starting_node)
        return jsonify(sensors)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@app.route("/locations")
def locations():
    from core.data.db import db_locations

    _locations = db_locations()
    return jsonify(_locations)


@app.route("/sensor_data/<sensor_name>/aggregated")
@app.route("/sensor_data/<sensor_name>/aggregated/<how>")
def aggregated_sensor_data(sensor_name, how="daily"):
    from core.data.db import db_aggregated_sensor_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _aggregated_sensor_data = db_aggregated_sensor_data(sensor_name=sensor_name, start_date=start_date, how=how)
    return jsonify(_aggregated_sensor_data)


@app.route("/data/<how>")
def datainfo(how="daily"):
    from core.data.db import db_datainfo

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _datainfo = db_datainfo(start_date=start_date, how=how)
    return jsonify(_datainfo)


@app.route("/data/hardcoded/<sensor_type>/<how>")
def wattmeters_data(sensor_type, how="daily"):
    from core.data.db import db_wattmeters_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _wattmeters_data = db_wattmeters_data(sensor_type=sensor_type, start_date=start_date, how=how)
    return jsonify(_wattmeters_data)


@app.route("/ui/data/navigation/<sensor_type>/<how>")
def get_navigation_data(sensor_type, how="daily"):
    from core.data.db import db_get_navigation_data

    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _navigation_data = db_get_navigation_data(sensor_type, start_date, how)
    return jsonify(_navigation_data)


@app.route("/monitoring/queries")
def queries():
    from core.data.db import db_get_running_queries

    queries = db_get_running_queries()
    return jsonify(queries)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/wattmeters_all.html")
def wattmeters():
    return render_template("graphics/wattmeters_all.html")


@app.route("/wattmeters_aggregated.html")
def wattmeters_aggregated():
    return render_template("graphics/wattmeters_aggregated.html")


@app.route("/socomecs_aggregated.html")
def socomecs_aggregated():
    return render_template("graphics/socomecs_aggregated.html")


@app.route("/last_sensors_updates")
def last_sensors_updates():
    from core.data.db import db_last_sensors_updates
    last_updates = db_last_sensors_updates()
    return jsonify(last_updates)


@app.route("/sensors.html")
def web_sensors():
    from core.data.sensors import get_sensors_arrays_with_children
    from core.data.db import db_last_sensors_updates
    last_updates = db_last_sensors_updates()
    sensors_arrays_with_children = get_sensors_arrays_with_children()
    for sensors_array in sensors_arrays_with_children:
        for child in sensors_array["children"]:
            child_last_update = filter(lambda x: x["sensor"] == child["name"], last_updates)
            if len(child_last_update) > 0:
                child["last_update"] = child_last_update[0]
            else:
                child["last_update"] = None
    return render_template("sensors.html", last_updates=last_updates, sensors_arrays_with_children=sensors_arrays_with_children)


@app.route("/measurements/wattmeters.html")
def measurements_wattmeters():
    return render_template("measurements_wattmeters.html")


@app.route("/measurements/thermometers.html")
def measurements_thermometers():
    return render_template("measurements_thermometers.html")


@app.route("/measurements/socomecs.html")
def measurements_socomecs():
    return render_template("measurements_socomecs.html")


@app.route("/room_overview.html")
@app.route("/room_overview.html/<sensors_array_name>")
@app.route("/room_overview.html/<sensors_array_name>/<selected_sensor>")
@app.route("/room_overview.html/by_selected/<selected_sensor>")
def room_overview(sensors_array_name=None, selected_sensor=None):
    from core.data.sensors import get_sensors_arrays, get_sensor_by_name
    sensors_arrays = get_sensors_arrays()
    sensors_array = None
    sensor = None
    if selected_sensor is not None:
        sensor = get_sensor_by_name(selected_sensor)
        if sensors_array_name is None:
            sensors_array_name = sensor["parent"]
    if sensors_array_name is not None:
        sensors_array = get_sensor_by_name(sensors_array_name)
    return render_template("room_overview.html",
                           sensors_arrays=sensors_arrays,
                           selected_sensors_array=sensors_array,
                           selected_sensor=sensor)


# @app.route("/sensors_array.html")
@app.route("/sensors_array.html/<sensors_array_name>")
@app.route("/sensors_array.html/<sensors_array_name>/<selected_sensor>")
def sensors_array(sensors_array_name, selected_sensor=None):
    from core.data.sensors import get_sensors_in_sensor_array
    sensors = map(lambda x: x["name"], get_sensors_in_sensor_array(sensors_array_name))
    return render_template("sensors_array.html",
                           sensors=sensors,
                           sensors_array_name=sensors_array_name,
                           selected_sensor=selected_sensor)


if __name__ == "__main__":
    from core.data.cq_aggregates import cqs_recreate_all, cqs_recompute_data, cq_multitree_recreate_all

    logging.basicConfig(level=logging.DEBUG)

    # Will check if continuous queries have already been created
    print("Checking continuous queries")
    continuous_queries_updated = cqs_recreate_all(force_creation=False)
    if continuous_queries_updated:
        print("Recomputing data of continuous queries")
        cqs_recompute_data()
    # cq_multitree_recreate_all(True)
    # cq_multitree_recreate_all(False)

    print("Running the \"API/Web\" program")
    app.jinja_env.auto_reload = DEBUG
    app.run(host="0.0.0.0", port=8081, debug=DEBUG, threaded=True)
