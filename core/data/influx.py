from influxdb import InfluxDBClient
from dateutil import parser
from datetime import timedelta
from core.config.config_loader import load_config
import functools

DB_HOST = load_config().get("influx").get("address")
DB_PORT = load_config().get("influx").get("port")
DB_USER = load_config().get("influx").get("user")
DB_PASSWORD = load_config().get("influx").get("password")
DB_NAME = load_config().get("influx").get("db")


def get_influxdb_parameters():

    config_key = "influx"

    return {
        "host": load_config().get(config_key).get("address"),
        "port": load_config().get(config_key).get("port"),
        "user": load_config().get(config_key).get("user"),
        "password": load_config().get(config_key).get("password"),
        "database": load_config().get(config_key).get("db"),
    }


def create_influxdb_connection():
    params = get_influxdb_parameters()
    db_client = InfluxDBClient(params.get("host"),
                               params.get("port"),
                               params.get("user"),
                               params.get("password"),
                               params.get("database"))
    return db_client


def get_influxdb_client():
    return create_influxdb_connection()


def db_sensor_data(sensor_name, start_date=None, end_date=None, zoom_ui=False):
    db_client = get_influxdb_client()

    if zoom_ui:
        extended_start_time_query = "SELECT last(*) " \
                                    "FROM sensors " \
                                    "WHERE sensor = '%s' and time < %s " % (sensor_name, start_date)
        points = list(db_client.query(extended_start_time_query).get_points())
        if points:
            start_date = "'%s'" % (points[0]["time"])
        if not end_date:
            end_date = "now()"
        extended_end_time_query = "SELECT first(*) " \
                                  "FROM sensors " \
                                  "WHERE sensor = '%s' and time > %s " % (sensor_name, end_date)
        points = list(db_client.query(extended_end_time_query).get_points())
        if points:
            end_date = "'%s'" % (points[0]["time"])

    if start_date is None and end_date is None:
        start_date = "now() - 3600s"
        start_date_query = "SELECT last(*) " \
                                  "FROM sensors " \
                                  "WHERE sensor = '%s'" % (sensor_name)
        points = list(db_client.query(start_date_query).get_points())
        if points:
            start_date = "'%s' - 3600s" % (points[0]["time"])
        end_date = "now()"
        pass

    query = "SELECT * " \
            "FROM sensors " \
            "WHERE sensor = '%s' and time >= %s and time <= %s" % (sensor_name, start_date, end_date)
    points = db_client.query(query).get_points()

    result = {
        "sensor_name": sensor_name,
        "start_date": start_date,
        "end_date": end_date,
        "timestamps": [],
        "values": [],
        "is_downsampled": False
    }

    for point in points:
        result["timestamps"].append(point['time'])
        result["values"].append(point['value'])

    db_client.close()

    return result


def db_sensors(sensor_type=None):
    db_client = get_influxdb_client()

    query = "show tag values from sensors with key = sensor"
    if sensor_type is not None:
        query += " where sensor_type = '%s'" % (sensor_type)

    points = db_client.query(query).get_points()

    result = {
        "sensors": []
    }

    for point in points:
        result["sensors"].append(point['value'])

    db_client.close()

    return result


def db_sensor_types():
    db_client = get_influxdb_client()

    query = "show tag values from sensors with key = sensor_type"
    points = db_client.query(query).get_points()

    result = {
        "sensor_types": []
    }

    for point in points:
        result["sensor_types"].append(point['value'])

    db_client.close()

    return result


def db_locations():
    db_client = get_influxdb_client()

    query = "show tag values from sensors with key =~ /location/"
    points = db_client.query(query).get_points()

    result = {
        "locations": []
    }

    for point in points:
        result["locations"].append(point['value'])

    db_client.close()

    return result


def _get_aggregate_serie_name(how):
    if how == "daily":
        return "measurement_downsample_1d"
    elif how == "hourly":
        return "measurement_downsample_1h"
    return "measurement_downsample_1m"


def db_aggregated_sensor_data(sensor_name, start_date=None, end_date=None, how="daily"):
    db_client = get_influxdb_client()

    serie_name = _get_aggregate_serie_name(how)

    criterion = "sensor='%s'" % (sensor_name)

    if not (start_date is None or start_date == "undefined"):
        criterion += "and time >= %s " % (start_date)

    if not (end_date is None or end_date == "undefined"):
        criterion += "and time <= %s " % (end_date)

    query = "SELECT * from %s where %s" % (serie_name, criterion)
    points = db_client.query(query).get_points()

    start_date = -1
    end_date = -1

    timestamps = []
    sums = []
    means = []
    medians = []
    stddevs = []
    counts = []
    mins = []
    maxs = []

    points_as_list = list(points)
    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for point in points_as_list:
        timestamp = point['time']
        if timestamp >= start_date and timestamp <= end_date:
            timestamps.append(point['time'])
            sums.append(point['sum'])
            means.append(point['mean'])
            medians.append(point['median'])
            stddevs.append(point['stddev'])
            counts.append(point['count'])
            mins.append(point['min'])
            maxs.append(point['max'])

    # Add a last empty point to enable streaming on the webapp
    last_empty_date = None

    if end_date != -1:
        if how == "daily":
            last_empty_date = parser.parse(end_date) + timedelta(days=1)
        elif how == "hourly":
            last_empty_date = parser.parse(end_date) + timedelta(hours=1)
        else:
            last_empty_date = parser.parse(end_date) + timedelta(minutes=1)
    if last_empty_date:
        timestamps.append(last_empty_date.isoformat())
        sums.append(None)
        means.append(None)
        medians.append(None)
        stddevs.append(None)
        counts.append(None)
        mins.append(None)
        maxs.append(None)

    result = {
        "start_date": start_date,
        "end_date": end_date,
        "last_empty_timestamp": end_date if last_empty_date is None else last_empty_date,
        "timestamps": timestamps,
        "sums": sums,
        "means": means,
        "medians": medians,
        "stddevs": stddevs,
        "mins": mins,
        "maxs": maxs,
        "counts": counts,
        "is_downsampled": True,
        "sensor_name": sensor_name
    }

    db_client.close()

    return result


def db_rack_side_temperature_data(side, start_date=None, end_date=None, how="daily", only_mean=True):
    from core.config.room_config import get_temperature_sensors_infrastructure

    db_client = get_influxdb_client()

    temperature_infra = get_temperature_sensors_infrastructure()
    back_temperature_sensors = functools.reduce(lambda x,y: x+y, [v.get("sensors") for k, v in temperature_infra.items() if side in k])

    criterion = " or ".join(["sensor='%s'" % s for s in back_temperature_sensors])

    if how == "daily":
        group_by_duration = "1d"
    elif how == "hourly":
        group_by_duration = "1h"
    else:
        group_by_duration = "1m"

    if not (start_date is None or start_date == "undefined"):
        criterion += "and time >= %s " % (start_date)

    if not (end_date is None or end_date == "undefined"):
        criterion += "and time <= %s " % (end_date)

    selected_field = """mean("value"), stddev("value"), median("value"), max("value"), min("value")"""
    if only_mean:
        selected_field = """mean("value")"""

    query = f"""SELECT {selected_field} FROM "sensors" WHERE {criterion} GROUP BY time({group_by_duration})"""
    points = db_client.query(query).get_points()

    start_date = -1
    end_date = -1

    timestamps = []
    means = []
    medians = []
    stddevs = []
    mins = []
    maxs = []

    points_as_list = list(points)
    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for point in points_as_list:
        timestamp = point['time']
        if timestamp >= start_date and timestamp <= end_date:
            timestamps.append(point['time'])
            means.append(point['mean'])
            if not only_mean:
                medians.append(point['median'])
                stddevs.append(point['stddev'])
                mins.append(point['min'])
                maxs.append(point['max'])

    result = {
        "start_date": start_date,
        "end_date": end_date,
        "timestamps": timestamps,
        "means": means,
        "medians": medians,
        "stddevs": stddevs,
        "mins": mins,
        "maxs": maxs,
        "is_downsampled": True,
        "side": side
    }

    db_client.close()

    return result


def db_dump_all_aggregated_data(start_date=None, end_date=None, group_by="1h"):
    db_client = get_influxdb_client()

    if start_date is None or start_date == "undefined":
        start_date = "now()-1d"

    if end_date is None or end_date == "undefined":
        end_date = "now()"

    criterions = []
    criterions += ["time >= %s " % (start_date)]
    criterions += ["time <= %s " % (end_date)]

    where_clause = " and ".join(criterions)

    query = """select mean("value"), max("value") from sensors where %s group by time(%s), sensor""" % (where_clause, group_by)
    query_result = db_client.query(query)
    points = query_result.get_points()

    start_date = -1
    end_date = -1

    sensors_data = {}
    timestamps = []
    means = []

    points_as_list = list(points)

    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for serie in query_result.raw.get("series"):
        sensor_name = serie.get("tags").get("sensor")

        sensors_data[sensor_name] = {
            "timestamps": [x[0] for x in serie.get("values")],
            "means": [x[1] for x in serie.get("values")],
            "maxs": [x[2] for x in serie.get("values")]
        }

    result = {
        "start_date": start_date,
        "end_date": end_date,
        "timestamps": timestamps,
        "means": means,
        "sensors_data": sensors_data,
        "is_downsampled": True,
    }

    db_client.close()

    return result


def _get_aggregate_multitree_serie_name(name, how):
    if how == "daily":
        return "cq_%s_1d" % name
    elif how == "hourly":
        return "cq_%s_1h" % name
    return "cq_%s_1m" % name


def db_aggregated_multitree_sensor_data(sensor_name, start_date=None, end_date=None, how="daily"):
    db_client = get_influxdb_client()

    serie_name = _get_aggregate_multitree_serie_name(sensor_name, how)

    time_range_criterion = ""
    if (start_date is not None and start_date != "undefined") or (end_date is not None and end_date != "undefined"):
        time_range_criterion = " where "
        time_criterions = []
        if start_date is not None:
            time_criterions += [" time >= %s " % start_date]
        if end_date is not None:
            time_criterions += [" time <= %s " % end_date]
        time_range_criterion += " and ".join(time_criterions)

    query = "SELECT * from %s %s" % (serie_name, time_range_criterion)
    points = db_client.query(query).get_points()

    start_date = -1
    end_date = -1

    timestamps = []
    sums = []
    means = []
    medians = []
    stddevs = []
    counts = []
    mins = []
    maxs = []

    points_as_list = list(points)
    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for point in points_as_list:
        timestamp = point['time']
        if timestamp >= start_date and timestamp <= end_date:
            timestamps.append(point['time'])
            sums.append(point['sum'])
            means.append(point['mean'])
            medians.append(point['median'])
            stddevs.append(point['stddev'])
            counts.append(point['count'])
            mins.append(point['min'])
            maxs.append(point['max'])

    # Add a last empty point to enable streaming on the webapp
    last_empty_date = None

    if end_date != -1:
        if how == "daily":
            last_empty_date = parser.parse(end_date) + timedelta(days=1)
        elif how == "hourly":
            last_empty_date = parser.parse(end_date) + timedelta(hours=1)
        else:
            last_empty_date = parser.parse(end_date) + timedelta(minutes=1)
    if last_empty_date:
        timestamps.append(last_empty_date.isoformat())
        sums.append(None)
        means.append(None)
        medians.append(None)
        stddevs.append(None)
        counts.append(None)
        mins.append(None)
        maxs.append(None)

    result = {
        "start_date": start_date,
        "end_date": end_date,
        "last_empty_timestamp": end_date if last_empty_date is None else last_empty_date,
        "timestamps": timestamps,
        "sums": sums,
        "means": means,
        "medians": medians,
        "stddevs": stddevs,
        "mins": mins,
        "maxs": maxs,
        "counts": counts,
        "is_downsampled": True,
        "sensor_name": sensor_name
    }

    db_client.close()

    return result


def _get_datainfo_serie_name(how):
    if how == "daily":
        return "measurement_downsample_all_1d"
    elif how == "hourly":
        return "measurement_downsample_all_1h"
    return "measurement_downsample_all_1m"


def db_datainfo(start_date=None, how="daily"):
    db_client = get_influxdb_client()

    serie_name = _get_datainfo_serie_name(how)

    if not start_date:
        query = "SELECT * from %s" % (serie_name)
    else:
        query = "SELECT * from %s where time >= %s" % (serie_name, start_date)
    points = db_client.query(query).get_points()

    start_date = -1
    end_date = -1

    timestamps = []
    sums = []
    means = []
    medians = []
    stddevs = []
    counts = []
    mins = []
    maxs = []

    points_as_list = list(points)
    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for point in points_as_list:
        timestamp = point['time']
        if timestamp >= start_date and timestamp <= end_date:
            timestamps.append(point['time'])
            sums.append(point['sum'])
            means.append(point['mean'])
            medians.append(point['median'])
            stddevs.append(point['stddev'])
            counts.append(point['count'])
            mins.append(point['min'])
            maxs.append(point['max'])

    # Add a last empty point to enable streaming on the webapp
    last_empty_date = None

    if end_date != -1:
        if how == "daily":
            last_empty_date = parser.parse(end_date) + timedelta(days=1)
        elif how == "hourly":
            last_empty_date = parser.parse(end_date) + timedelta(hours=1)
        else:
            last_empty_date = parser.parse(end_date) + timedelta(minutes=1)
    if last_empty_date:
        timestamps.append(last_empty_date.isoformat())
        sums.append(None)
        means.append(None)
        medians.append(None)
        stddevs.append(None)
        counts.append(None)
        mins.append(None)
        maxs.append(None)

    result = {
        "range": {
            "start_date": start_date,
            "end_date": end_date,
            "last_empty_timestamp": end_date if last_empty_date is None else last_empty_date,
            "timestamps": timestamps,
            "sums": sums,
            "means": means,
            "medians": medians,
            "stddevs": stddevs,
            "counts": counts,
            "mins": mins,
            "maxs": maxs
        }
    }

    db_client.close()

    return result


def db_get_navigation_data(sensor_type, start_date=None, how="daily"):
    db_client = get_influxdb_client()

    serie_name = _get_datainfo_serie_name(how)

    if not start_date:
        query = "SELECT * from %s where sensor_type='%s'" % (serie_name, sensor_type)
    else:
        query = "SELECT * from %s where time >= %s and sensor_type='%s'" % (serie_name, start_date, sensor_type)
    points = db_client.query(query).get_points()

    start_date = -1
    end_date = -1

    timestamps = []
    sums = []
    means = []
    medians = []
    stddevs = []
    counts = []
    mins = []
    maxs = []

    points_as_list = list(points)
    for point in points_as_list:
        timestamp = point['time']
        if point['mean'] is not None:
            if start_date == -1 or start_date > timestamp:
                start_date = timestamp
            if end_date == -1 or end_date < timestamp:
                end_date = timestamp

    for point in points_as_list:
        timestamp = point['time']
        if timestamp >= start_date and timestamp <= end_date:
            timestamps.append(point['time'])
            sums.append(point['sum'])
            means.append(point['mean'])
            medians.append(point['median'])
            stddevs.append(point['stddev'])
            counts.append(point['count'])
            mins.append(point['min'])
            maxs.append(point['max'])

    # Add a last empty point to enable streaming on the webapp
    query = "SELECT last(*) from sensors where sensor_type='%s' and time > now() - 1d" % (sensor_type)
    points = list(db_client.query(query).get_points())
    last_empty_date = None
    if points:
        last_empty_date = points[0]['time']
        timestamps.append(last_empty_date)
        sums.append(sums[-1] if sums else -1)
        means.append(means[-1] if means else -1)
        medians.append(medians[-1] if medians else -1)
        stddevs.append(stddevs[-1] if stddevs else -1)
        counts.append(counts[-1] if counts else -1)
        mins.append(mins[-1] if mins else -1)
        maxs.append(maxs[-1] if maxs else -1)

    result = {
        "range": {
            "start_date": start_date,
            "end_date": end_date,
            "last_empty_timestamp": end_date if last_empty_date is None else last_empty_date,
            "timestamps": timestamps,
            "sums": sums,
            "means": means,
            "medians": medians,
            "stddevs": stddevs,
            "counts": counts,
            "mins": mins,
            "maxs": maxs
        }
    }

    db_client.close()

    return result


# def db_wattmeters_data(sensor_type, start_date=None, how="daily"):
#     db_client = get_influxdb_client()
#
#     data_set = "cq_measurement_%s_aggregate_1m" % (sensor_type)
#     if how == "hourly":
#         data_set = "cq_measurement_%s_aggregate_1h" % (sensor_type)
#     if how == "daily":
#         data_set = "cq_measurement_%s_aggregate_1d" % (sensor_type)
#
#     if not start_date:
#         query = "SELECT * from %s" % (data_set)
#     else:
#         query = "SELECT * from %s where time >= %s" % (data_set, start_date)
#     points = db_client.query(query).get_points()
#
#     start_date = -1
#     end_date = -1
#
#     timestamps = []
#     sums = []
#     means = []
#     medians = []
#     stddevs = []
#     counts = []
#     mins = []
#     maxs = []
#
#     points_as_list = list(points)
#     for point in points_as_list:
#         timestamp = point['time']
#         if point['mean'] is not None:
#             if start_date == -1 or start_date > timestamp:
#                 start_date = timestamp
#             if end_date == -1 or end_date < timestamp:
#                 end_date = timestamp
#
#     for point in points_as_list:
#         timestamp = point['time']
#         if timestamp >= start_date and timestamp <= end_date:
#             timestamps.append(point['time'])
#             sums.append(point['sum'])
#             means.append(point['mean'])
#             medians.append(point['median'])
#             stddevs.append(point['stddev'])
#             counts.append(point['count'])
#             mins.append(point['min'])
#             maxs.append(point['max'])
#
#     # Add a last empty point to enable streaming on the webapp
#     last_empty_date = None
#
#     if end_date != -1:
#         if how == "hourly":
#             last_empty_date = parser.parse(end_date) + timedelta(hours=1)
#         elif how == "daily":
#             last_empty_date = parser.parse(end_date) + timedelta(days=1)
#         else:
#             last_empty_date = parser.parse(end_date) + timedelta(minutes=1)
#     if last_empty_date:
#         timestamps.append(last_empty_date.isoformat())
#         sums.append(None)
#         means.append(None)
#         medians.append(None)
#         stddevs.append(None)
#         counts.append(None)
#         mins.append(None)
#         maxs.append(None)
#
#     result = {
#         "range": {
#             "start_date": start_date,
#             "end_date": end_date,
#             "last_empty_timestamp": end_date if last_empty_date is None else last_empty_date,
#             "timestamps": timestamps,
#             "sums": sums,
#             "means": means,
#             "medians": medians,
#             "stddevs": stddevs,
#             "counts": counts,
#             "mins": mins,
#             "maxs": maxs
#         }
#     }
#
#     db_client.close()
#
#     return result


def db_get_sensors_with_tags():
    db_client = get_influxdb_client()

    query = "show series from sensors"
    points = db_client.query(query).get_points()

    raw_results = [s.get("key") for s in points]
    series = {}
    for result in raw_results:
        serie_type, *properties_raw = result.split(",")

        serie_dict = {}
        for prop in properties_raw:
            key, value = prop.split("=")
            serie_dict[key] = value

        series[serie_dict.get("sensor")] = serie_dict
    db_client.close()

    return series


def db_last_sensors_updates():
    db_client = get_influxdb_client()

    series = db_get_sensors_with_tags()

    query = "SELECT last(*) from sensors where time > now() - 36600s group by sensor"
    rs = db_client.query(query)

    result = []

    for point in rs.raw.get("series"):
        sensor = point.get("tags").get("sensor")
        [[time, last_value]] = point.get("values")

        corresponding_serie = series.get(sensor)

        result += [{
            "time": time,
            "last_value": last_value,
            "location": corresponding_serie.get("location"),
            "unit": corresponding_serie.get("unit"),
            "sensor_type": corresponding_serie.get("sensor_type"),
            "sensor": corresponding_serie.get("sensor"),
        }]

    db_client.close()

    return result


def db_oldest_point_in_serie(serie_name):
    db_client = get_influxdb_client()

    series = db_get_sensors_with_tags()

    if serie_name == "*":
        query = """SELECT time, location, sensor, sensor_type, unit, value from sensors ORDER BY ASC LIMIT 1"""
    else:
        query = """SELECT first(*) from sensors where sensor='%s'""" % (serie_name)
    rs = db_client.query(query)

    result = []

    for point in rs.raw.get("series"):

        if serie_name == "*":
            [[time, location, sensor, sensor_type, unit, first_value]] = point.get("values")
        else:
            corresponding_serie = series.get(serie_name)

            [[time, first_value]] = point.get("values")
            location = corresponding_serie.get("location")
            unit = corresponding_serie.get("unit")
            sensor_type = corresponding_serie.get("sensor_type")
            sensor = corresponding_serie.get("sensor")


        result = {
            "time": time,
            "first_value": first_value,
            "location": location,
            "unit": unit,
            "sensor_type": sensor_type,
            "sensor": sensor,
        }

    db_client.close()

    return result


def db_last_temperature_values():
    db_client = get_influxdb_client()

    series = db_get_sensors_with_tags()

    query = """SELECT last(*) from sensors WHERE sensor_type = 'temperature' and time > now() - 1d group by sensor"""
    rs = db_client.query(query)

    result = []

    for point in rs.raw.get("series"):
        sensor = point.get("tags").get("sensor")
        [[time, last_value]] = point.get("values")

        corresponding_serie = series.get(sensor)

        result += [{
            "time": time,
            "last_value": last_value,
            "location": corresponding_serie.get("location"),
            "unit": corresponding_serie.get("unit"),
            "sensor_type": corresponding_serie.get("sensor_type"),
            "sensor": corresponding_serie.get("sensor"),
        }]

    db_client.close()

    return result


def db_last_temperature_mean():
    db_client = get_influxdb_client()

    query = """select mean(*) from sensors where time > now() - 1h and sensor_type='temperature' group by time(1m)"""
    points = list(db_client.query(query).get_points())

    result = points[-1].get("mean_value")

    db_client.close()

    return result


def db_multitree_last_wattmeter_value(multitree_node):
    db_client = get_influxdb_client()

    cq_name = "cq_%s_1m" % (multitree_node["id"])

    query = "SELECT last(*) from %s where time > now() - 1d" % (cq_name)
    points = db_client.query(query).get_points()

    for point in points:
        return point["last_mean"]

    db_client.close()

    return 0


def db_multitree_last_wattmeter_query(multitree_node):
    cq_name = "cq_%s_1m" % (multitree_node["id"])

    query = "SELECT last(*) from %s where time > now() - 1d" % (cq_name)

    return (query, cq_name)


def db_multitree_last_wattmeter_all_in_one_query(queries):
    db_client = get_influxdb_client()
    result = {}

    all_in_one_query = "select last(*) from %s where time > now() - 1d" % (",".join(queries.get("cq_names")))

    points = db_client.query(all_in_one_query)

    for cq_name, result_set in points.items():
        cq_values = list(result_set)
        if len(cq_name) >= 2 and  len(cq_values) >= 1:
            result[cq_name[0]] = cq_values[0].get("last_mean")

    db_client.close()

    return result


def db_get_running_queries():
    db_client = get_influxdb_client()

    query = "show queries"
    points = db_client.query(query).get_points()

    db_client.close()

    return points


def influx_run_query(query):
    db_client = get_influxdb_client()

    points = db_client.query(query).get_points()

    db_client.close()

    return points
