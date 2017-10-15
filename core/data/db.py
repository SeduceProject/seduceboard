from influxdb import InfluxDBClient
from dateutil import parser
from datetime import timedelta

DB_HOST = "192.168.1.8"
DB_PORT = 8086
# DB_HOST = "127.0.0.1"
# DB_PORT = 8096
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
OUTPUT_FILE = 'temperatures.json'


def db_sensor_data(sensor_name, start_date, end_date, zoom_ui=False):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    if zoom_ui:
        extended_start_time_query = "SELECT last(*) " \
                                    "FROM sensors " \
                                    "WHERE sensor = '%s' and time < %s " % (sensor_name, start_date)
        points = list(db_client.query(extended_start_time_query).get_points())
        if points:
            start_date = "'%s'" % (points[0]["time"])

        extended_end_time_query = "SELECT first(*) " \
                                  "FROM sensors " \
                                  "WHERE sensor = '%s' and time > %s " % (sensor_name, end_date)
        points = list(db_client.query(extended_end_time_query).get_points())
        if points:
            end_date = "'%s'" % (points[0]["time"])

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

    return result


def db_sensors(start_date, sensor_type=None):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = "show tag values from sensors with key = sensor"
    if sensor_type is not None:
        query += " where sensor_type = '%s'" % (sensor_type)

    points = db_client.query(query).get_points()

    result = {
        "since": start_date,
        "sensors": []
    }

    for point in points:
        result["sensors"].append(point['value'])

    return result


def db_sensor_types():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = "show tag values from sensors with key = sensor_type"
    points = db_client.query(query).get_points()

    result = {
        "sensor_types": []
    }

    for point in points:
        result["sensor_types"].append(point['value'])

    return result


def db_locations():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = "show tag values from sensors with key =~ /location/"
    points = db_client.query(query).get_points()

    result = {
        "locations": []
    }

    for point in points:
        result["locations"].append(point['value'])

    return result


def _get_aggregate_serie_name(how):
    if how == "daily":
        return "measurement_downsample_1d"
    elif how == "hourly":
        return "measurement_downsample_1h"
    return "measurement_downsample_1m"


def db_aggregated_sensor_data(sensor_name, start_date=None, how="daily"):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    serie_name = _get_aggregate_serie_name(how)

    if not start_date:
        query = "SELECT * from %s where sensor='%s'" % (serie_name, sensor_name)
    else:
        query = "SELECT * from %s where time >= %s and sensor='%s'" % (serie_name, start_date, sensor_name)
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

    return result


def _get_datainfo_serie_name(how):
    if how == "daily":
        return "measurement_downsample_all_1d"
    elif how == "hourly":
        return "measurement_downsample_all_1h"
    return "measurement_downsample_all_1m"


def db_datainfo(start_date=None, how="daily"):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

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

    return result


def db_get_navigation_data(sensor_type, start_date=None, how="daily"):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

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
    query = "SELECT last(*) from sensors where sensor_type='%s'" % (sensor_type)
    points = list(db_client.query(query).get_points())
    if points:
        last_empty_date = points[0]['time']
        timestamps.append(last_empty_date)
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

    return result


def db_wattmeters_data(sensor_type, start_date=None, how="daily"):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    data_set = "cq_measurement_%s_aggregate_1m" % (sensor_type)
    if how == "hourly":
        data_set = "cq_measurement_%s_aggregate_1h" % (sensor_type)
    if how == "daily":
        data_set = "cq_measurement_%s_aggregate_1d" % (sensor_type)

    if not start_date:
        query = "SELECT * from %s" % (data_set)
    else:
        query = "SELECT * from %s where time >= %s" % (data_set, start_date)
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
        if how == "hourly":
            last_empty_date = parser.parse(end_date) + timedelta(hours=1)
        elif how == "daily":
            last_empty_date = parser.parse(end_date) + timedelta(days=1)
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

    return result


def db_last_sensors_updates():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = "select last(*), location, unit, sensor_type, sensor from sensors group by sensor"
    points = db_client.query(query).get_points()

    result = []

    for point in points:
        result += [{
            "time": point["time"],
            "last_value": point["last_value"],
            "location": point["location"],
            "unit": point["unit"],
            "sensor_type": point["sensor_type"],
            "sensor": point["sensor"],
        }]

    return result


def db_get_running_queries():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = "show queries"
    points = db_client.query(query).get_points()

    return points
