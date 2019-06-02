import flask
import flask_login
import time
from dateutil import parser

from flask import Blueprint
from flask import render_template
from core.decorators.admin_login_required import admin_login_required
from core.decorators.profile import profile

from core.misc import _display_time
from core.data.sensors import get_sensors_arrays_with_children
from core.data.influx import db_last_sensors_updates

from core.data.multitree import get_node_by_id, _get_last_node_consumption
from core.data.influx import db_last_temperature_mean
from core.data.influx import db_aggregated_multitree_sensor_data
from core.data.influx import db_sensor_data

from core.data.sensors import get_sensors_in_sensor_array
from core.data.redis_counters import redis_clear_error_count

from core.data.sensors import get_sensors_arrays, get_sensor_by_name, get_sensors_array_by_name, get_sensors_array_from_sensor_name
from core.data.influx import db_last_temperature_values

from core.config.room_config import get_temperature_sensors_infrastructure
from core.data.redis_counters import redis_get_sensors_data

import numpy as np

webapp_blueprint = Blueprint('webapp', __name__,
                             template_folder='templates')


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@webapp_blueprint.route("/")
@flask_login.login_required
def index():
    datacenter_node = get_node_by_id("datacenter")
    cluster_hardware = get_node_by_id("hardware_cluster")
    datacenter_consumption = _get_last_node_consumption(datacenter_node)
    cluster_hardware_consumption = _get_last_node_consumption(cluster_hardware)
    #
    # pue_ratio = datacenter_consumption / cluster_hardware_consumption

    _datacenter_data = db_aggregated_multitree_sensor_data(sensor_name="datacenter", start_date="now()-8d",
                                                           end_date="now()", how="hourly")
    _cluster_data = db_aggregated_multitree_sensor_data(sensor_name="hardware_cluster", start_date="now()-8d",
                                                        end_date="now()", how="hourly")
    _pue_data = {
        "end_date": _cluster_data.get("end_date"),
        "start_date": _cluster_data.get("start_date"),
        "means": [x / y for (x, y) in zip(_datacenter_data.get("means"), _cluster_data.get("means")) if
                  x != None and y != None]
    }
    pue_ratio = np.mean(_pue_data.get("means"))

    last_temperature_mean = db_last_temperature_mean()

    # Last external temperature value
    extenal_temperature_sensors = get_temperature_sensors_infrastructure().get("room.top", {}).get("sensors", [])
    if len(extenal_temperature_sensors) > 0:
        extenal_temperature_sensor = extenal_temperature_sensors[-1]
        # Exponential backoff to_find the last temperature
        search_interval = 30
        last_external_temperature_mean = None
        while last_external_temperature_mean is None and search_interval < 24 * 60:
            start_date = "now() - %sm" % search_interval
            end_date = "now() - %sm" % (search_interval - 30)
            last_temperatures = db_sensor_data(extenal_temperature_sensor, start_date=start_date, end_date=end_date)
            last_temperatures_values = last_temperatures.get("values", [])
            if len(last_temperatures_values) > 0:
                last_external_temperature_mean = last_temperatures_values[-1]
            else:
                search_interval = search_interval * 2
    else:
        last_external_temperature_mean = "No external temperature sensor"

    return render_template("index.html.jinja2",
                           pue_ratio=pue_ratio,
                           datacenter_consumption=datacenter_consumption,
                           cluster_hardware_consumption=cluster_hardware_consumption,
                           last_temperature_mean=last_temperature_mean,
                           last_external_temperature_mean=last_external_temperature_mean)


@webapp_blueprint.route("/sensors.html")
@flask_login.login_required
def sensors():
    last_updates = db_last_sensors_updates()
    sensors_arrays_with_children = get_sensors_arrays_with_children()
    now_time = time.time()

    for (sensors_array_name, sensors_array) in sensors_arrays_with_children.items():
        for child in sensors_array["children"]:
            child_last_update = [x for x in last_updates if x.get("sensor") == child.get("name")]
            if len(child_last_update) > 0:
                last_update_since_epoch = int(
                    time.mktime(parser.parse(child_last_update[0]["time"]).timetuple())) - time.timezone
                time_since_last_update_secs = now_time - last_update_since_epoch
                displayed_time_text = _display_time(time_since_last_update_secs)
                child_last_update[0]["nice_last_udpate_text"] = displayed_time_text
                child["last_update"] = child_last_update[0]
            else:
                child["last_update"] = None
    return render_template("sensors.html.jinja2",
                           last_updates=last_updates,
                           sensors_arrays_with_children=sensors_arrays_with_children)


@webapp_blueprint.route("/measurements/wattmeters.html")
@flask_login.login_required
def measurements_wattmeters():
    return render_template("measurements_wattmeters.html.jinja2")


@webapp_blueprint.route("/measurements/thermometers.html")
@flask_login.login_required
def measurements_thermometers():
    return render_template("measurements_thermometers.html.jinja2")


@webapp_blueprint.route("/weighted_tree_consumption")
@flask_login.login_required
def weighted_tree_consumption():
    return render_template("weighted_tree_consumption.html.jinja2")


@webapp_blueprint.route("/rack_temperature_overview.html")
@flask_login.login_required
def rack_temperature_overview():
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    last_temperature_values = db_last_temperature_values()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        sensor_array["last_temperatures"] = \
            [x for x in last_temperature_values if x["sensor"] in sensor_array["sensors"]]

    return render_template("rack_temperature_overview.html.jinja2",
                           temperature_sensors_infrastructure=temperature_sensors_infrastructure)


@webapp_blueprint.route("/rack_temperature_errors_clear.html")
@admin_login_required
def rack_temperature_errors_clear():
    redis_clear_error_count()
    return flask.redirect(flask.url_for("webapp.rack_temperature_errors_overview"))


@webapp_blueprint.route("/rack_temperature_overview.html/errors")
@webapp_blueprint.route("/rack_temperature_overview_errors.html")
@admin_login_required
def rack_temperature_errors_overview():
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    temperature_errors_data = redis_get_sensors_data()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        last_errors = []
        for sensor_name in sensor_array["sensors"]:
            if sensor_name in temperature_errors_data and "error_count" in temperature_errors_data[sensor_name]:
                error_count = temperature_errors_data[sensor_name]["error_count"]
            else:
                error_count = 0
            last_errors += [{"sensor": sensor_name, "last_value": error_count}]

        sensor_array["last_temperatures"] = last_errors

    return render_template("rack_temperature_errors_overview.html.jinja2",
                           temperature_sensors_infrastructure=temperature_sensors_infrastructure)


@webapp_blueprint.route("/room_overview.html")
@webapp_blueprint.route("/room_overview.html/<sensors_array_name>")
@webapp_blueprint.route("/room_overview.html/<sensors_array_name>/<selected_sensor>")
@webapp_blueprint.route("/room_overview.html/by_selected/<selected_sensor>")
@flask_login.login_required
def room_overview(sensors_array_name=None, selected_sensor=None):
    sensors_arrays = get_sensors_arrays()
    sensors_array = None
    sensor = None

    if selected_sensor is not None:
        sensor = get_sensor_by_name(selected_sensor)
        if sensors_array_name is None:
            sensors_array = get_sensors_array_from_sensor_name(sensor.get("name"))
            sensors_array_name = sensors_array.get("name")
    if sensors_array_name is not None:
        sensors_array = get_sensors_array_by_name(sensors_array_name)
    return render_template("room_overview.html.jinja2",
                           sensors_arrays=sensors_arrays,
                           selected_sensors_array=sensors_array,
                           selected_sensor=sensor)


@webapp_blueprint.route("/sensors_array.html/<sensors_array_name>")
@webapp_blueprint.route("/sensors_array.html/<sensors_array_name>/<selected_sensor>")
@flask_login.login_required
def sensors_array(sensors_array_name, selected_sensor=None):
    sensors = [sensor.get("name") for sensor in get_sensors_in_sensor_array(sensors_array_name)]
    return render_template("sensors_array.html.jinja2",
                           sensors=sensors,
                           sensors_array_name=sensors_array_name,
                           selected_sensor=selected_sensor)
