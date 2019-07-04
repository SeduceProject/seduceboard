from flask import Blueprint
from flask import request
import flask_login
from flask import jsonify
from dateutil import parser
from core.data.influx import db_sensor_data
from core.data.influx import db_sensors
from core.data.influx import db_sensor_types
from core.data.multitree import get_tree

from core.data.influx import db_last_temperature_values
from core.data.influx import db_last_sensors_updates
from core.data.influx import db_rack_side_temperature_data
from core.data.multitree import get_datacenter_weighted_tree_consumption_data
from core.data.redis_counters import redis_get_sensors_data
from core.data.redis_counters import redis_increment_sensor_error_count
from core.data.influx import db_get_running_queries
from core.data.influx import db_get_navigation_data
from core.config.room_config import get_temperature_sensors_infrastructure
from core.data.influx import db_wattmeters_data
from core.data.influx import db_datainfo
from core.data.multitree import get_root_nodes
from core.data.influx import db_aggregated_multitree_sensor_data
from core.data.multitree import get_node_by_id
from core.data.multitree import get_sensors_tree
from core.data.influx import db_aggregated_sensor_data
from core.data.influx import db_locations

from core.decorators.profile import profile

webapp_api_blueprint = Blueprint('webapp_api', __name__,
                                 template_folder='templates')


def validate(date_text):
    try:
        parser.parse(date_text)
    except ValueError:
        return False
    return True


@webapp_api_blueprint.route("/sensor_data/<sensor_name>")
def sensor_data(sensor_name):
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


@webapp_api_blueprint.route("/sensors")
@webapp_api_blueprint.route("/sensors/all")
@webapp_api_blueprint.route("/sensors/<sensor_type>")
def sensors(sensor_type=None):
    _sensors = db_sensors(sensor_type=sensor_type)
    return jsonify(_sensors)


@webapp_api_blueprint.route("/sensors_types")
@webapp_api_blueprint.route("/sensor_types")
def sensor_types():
    _sensor_types = db_sensor_types()
    return jsonify(_sensor_types)


@webapp_api_blueprint.route("/multitree/root")
def multitree_root_nodes():
    return jsonify(get_root_nodes())


@webapp_api_blueprint.route("/multitree/query/tree/<node_id>")
def multitree_tree_query(node_id):
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        tree = get_tree(starting_node, False)
        return jsonify(tree)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@webapp_api_blueprint.route("/multitree/query/sensors/<node_id>")
def multitree_sensors_query(node_id):
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        sensors = get_sensors_tree(starting_node)
        return jsonify(sensors)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@webapp_api_blueprint.route("/multitree/query/sensors/<node_id>/data")
def multitree_sensors_data_query(node_id):
    starting_node = get_node_by_id(node_id)
    if starting_node is not None:
        sensors = get_sensors_tree(starting_node)
        return jsonify(sensors)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (node_id)})


@webapp_api_blueprint.route("/locations")
def locations():
    _locations = db_locations()
    return jsonify(_locations)


@webapp_api_blueprint.route("/sensor_data/<sensor_name>/aggregated")
@webapp_api_blueprint.route("/sensor_data/<sensor_name>/aggregated/<how>")
def aggregated_sensor_data(sensor_name, how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date

    _aggregated_sensor_data = db_aggregated_sensor_data(sensor_name=sensor_name, start_date=start_date,
                                                        end_date=end_date, how=how)
    return jsonify(_aggregated_sensor_data)


@webapp_api_blueprint.route("/rack/<side>/temperatures/aggregated")
@webapp_api_blueprint.route("/rack/<side>/temperatures/aggregated/<how>")
def aggregated_rack_side_temperatures(side, how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date

    _aggregated_sensor_data = db_rack_side_temperature_data(side=side,
                                                            start_date=start_date,
                                                            end_date=end_date,
                                                            how=how)
    return jsonify(_aggregated_sensor_data)

@webapp_api_blueprint.route("/multitree_sensor_data/<sensor_name>/aggregated")
@webapp_api_blueprint.route("/multitree_sensor_data/<sensor_name>/aggregated/<how>")
def aggregated_multitree_sensor_data(sensor_name, how="minutely"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    end_date = None
    if "end_date" in request.args:
        end_date = request.args["end_date"]
        if validate(end_date):
            end_date = "'%s'" % end_date

    _aggregated_sensor_data = db_aggregated_multitree_sensor_data(sensor_name=sensor_name, start_date=start_date,
                                                                  end_date=end_date, how=how)
    return jsonify(_aggregated_sensor_data)


@webapp_api_blueprint.route("/data/<how>")
def datainfo(how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _datainfo = db_datainfo(start_date=start_date, how=how)
    return jsonify(_datainfo)


@webapp_api_blueprint.route("/data/hardcoded/<sensor_type>/<how>")
def wattmeters_data(sensor_type, how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _wattmeters_data = db_wattmeters_data(sensor_type=sensor_type, start_date=start_date, how=how)
    return jsonify(_wattmeters_data)


@webapp_api_blueprint.route("/data/generated/pue/<how>")
def pue_data(how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    _datacenter_data = db_aggregated_multitree_sensor_data(sensor_name="datacenter", start_date=start_date,
                                                           end_date="now()", how=how)
    _cluster_data = db_aggregated_multitree_sensor_data(sensor_name="hardware_cluster", start_date=start_date,
                                                        end_date="now()", how=how)
    _pue_data = {
        "end_date": _cluster_data.get("end_date"),
        "start_date": _cluster_data.get("start_date"),
        "means": [x / y for (x, y) in zip(_datacenter_data.get("means"), _cluster_data.get("means")) if
                  x != None and y != None],
        "timestamps": _cluster_data.get("timestamps"),
    }
    return jsonify(_pue_data)


@webapp_api_blueprint.route("/data/generated/external_temperature/<how>")
def external_temperature_data(how="daily"):
    start_date = None
    if "start_date" in request.args:
        start_date = request.args["start_date"]
        if validate(start_date):
            start_date = "'%s'" % start_date

    # Last external temperature value
    extenal_temperature_sensors = get_temperature_sensors_infrastructure().get("room.top", {}).get("sensors", [])
    if len(extenal_temperature_sensors) > 0:
        external_temperature_sensor = extenal_temperature_sensors[-1]
        sensor_data = db_aggregated_sensor_data(external_temperature_sensor, start_date, end_date="now()", how=how)
    else:
        sensor_data = {}

    return jsonify(sensor_data)


@webapp_api_blueprint.route("/ui/data/navigation/<sensor_type>/<aggregation_preferences>")
def get_navigation_data(sensor_type, aggregation_preferences="daily,hourly"):

    if "," in aggregation_preferences:
        aggregation_preferences = aggregation_preferences.split(",")
    else:
        aggregation_preferences = [aggregation_preferences]

    for time_periodicity in aggregation_preferences:
        start_date = None
        if "start_date" in request.args:
            start_date = request.args["start_date"]
            if validate(start_date):
                start_date = "'%s'" % start_date

        _navigation_data = db_get_navigation_data(sensor_type, start_date, time_periodicity)

        if len(_navigation_data['range']['timestamps']) > 10:
            return jsonify(_navigation_data)

    return jsonify({})


@webapp_api_blueprint.route("/monitoring/queries")
def queries():
    queries = db_get_running_queries()
    return jsonify(queries)


@webapp_api_blueprint.route("/last_sensors_updates")
def last_sensors_updates():
    last_updates = db_last_sensors_updates()
    return jsonify(last_updates)


@webapp_api_blueprint.route("/weighted_tree_consumption_data")
@flask_login.login_required
def weighted_tree_consumption_data():
    return jsonify(get_datacenter_weighted_tree_consumption_data())


@webapp_api_blueprint.route("/rack_temperature/sensors")
@flask_login.login_required
def rack_temperature_sensors():
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    return jsonify(temperature_sensors_infrastructure)


@webapp_api_blueprint.route("/rack_temperature/sensors/last_values")
@flask_login.login_required
def rack_temperature_sensors_last_values():
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    last_temperature_values = db_last_temperature_values()

    for sensor_array_name in temperature_sensors_infrastructure:
        sensor_array = temperature_sensors_infrastructure[sensor_array_name]
        sensor_array["last_temperatures"] = \
            [x for x in last_temperature_values if x["sensor"] in sensor_array["sensors"]]

    return jsonify(temperature_sensors_infrastructure)


@webapp_api_blueprint.route("/rack_temperature_errors/sensors/last_values")
@flask_login.login_required
def rack_temperature_sensors_errors_last_values():
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

    return jsonify(temperature_sensors_infrastructure)


@webapp_api_blueprint.route("/rack_temperature_overview.html/errors/increment/<sensor_name>")
@flask_login.login_required
def rack_temperature_errors_incr(sensor_name):
    redis_increment_sensor_error_count(sensor_name)
    sensors_data = redis_get_sensors_data()

    return jsonify(sensors_data)
