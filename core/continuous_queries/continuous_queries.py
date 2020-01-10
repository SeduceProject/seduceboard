# from core.data.influx import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
# from influxdb import InfluxDBClient
from core.data.multitree import get_nodes
from core.data.influx import get_influxdb_client, get_influxdb_parameters
import re


def _extend_description_of_cq(cq, multitree_nodes_cq_ids):
    cq_name = cq.get("name")

    sensor_id = "_".join(cq_name.split("_")[1:-1])
    cq["sensor_id"] = sensor_id

    # Try to find the sensor serie id (used by influxDB)
    m = re.search("sensor = '(.+?)'", cq.get("query"))
    if m:
        cq["influx_sensor_id"] = m.group(1)
    elif "downsample_all" in cq_name:
        cq["influx_sensor_id"] = "*"
    else:
        cq["influx_sensor_id"] = "*"

    if sensor_id in multitree_nodes_cq_ids:
        cq["is_multitree_query"] = True
    else:
        cq["is_multitree_query"] = False

    if "aggregate" in cq_name:
        cq["is_aggregated_query"] = True
    else:
        cq["is_aggregated_query"] = False

    cq_frequency = cq_name.split("_")[-1]
    if cq_frequency in ["30s", "1m", "1h", "1d"]:
        cq["frequency"] = cq_frequency
    else:
        cq["frequency"] = -1
    return True


def list_continuous_queries():
    db_client = get_influxdb_client()

    query = "show continuous queries"

    db_name = get_influxdb_parameters().get("database")

    cqs = list(db_client.query(query, database=db_name).get_points())

    multitree_nodes = get_nodes()
    multitree_nodes_cq_ids = [n.get("id") for n in multitree_nodes if "target" not in n]

    for cq in cqs:
        _extend_description_of_cq(cq, multitree_nodes_cq_ids)

    return cqs


def get_continuous_query_by_name(query_name):
    db_client = get_influxdb_client()

    query = "show continuous queries"

    db_name = get_influxdb_parameters().get("database")

    cqs = list(db_client.query(query, database=db_name).get_points())

    multitree_nodes = get_nodes()
    multitree_nodes_cq_ids = [n.get("id") for n in multitree_nodes if "target" not in n]

    # for cq in cqs:
    cq_candidates = [cq for cq in cqs if cq.get("name") == query_name]

    if not cq_candidates:
        return None

    cq = cq_candidates[0]
    _extend_description_of_cq(cq, multitree_nodes_cq_ids)

    return cq


def cq_generate_update_query(cqname, start, end):
    # Find continuous query
    cq = get_continuous_query_by_name(cqname)

    # Try to find the sensor serie id (used by influxDB)
    search_select_statement = re.search(" BEGIN (.+?) END", cq.get("query"))
    if search_select_statement:
        raw_query = search_select_statement.group(1)

        if raw_query.count("GROUP BY") == 1:
            raw_query = raw_query.replace("GROUP BY", "where time > %ss and time < %ss group by" % (start, end), 1)
        elif raw_query.count("GROUP BY") == 2:
            raw_query = raw_query.replace("GROUP BY", "and   time > %ss and time < %ss group by" % (start, end), 1)
            raw_query = raw_query.replace("GROUP BY", "where time > %ss and time < %ss group by" % (start, end), 1)
        else:
            return None

        return raw_query

    return None


def list_expected_cqs_names():
    expected_cqs_names = []

    # Add aggregated continuous queries
    expected_cqs_names += ["cq_measurement_socomecs_aggregate_1m",
                           "cq_measurement_socomecs_aggregate_1h",
                           "cq_measurement_socomecs_aggregate_1d",
                           "cq_measurement_external_temperature_aggregate_30s",
                           "cq_measurement_external_temperature_aggregate_1m",
                           "cq_measurement_external_temperature_aggregate_1h",
                           "cq_measurement_external_temperature_aggregate_1d",
                           "cq_measurement_wattmeters_aggregate_10s",
                           "cq_measurement_wattmeters_aggregate_1m",
                           "cq_measurement_wattmeters_aggregate_1h",
                           "cq_measurement_wattmeters_aggregate_1d",
                           "cq_measurement_socomecs_aggregate_30s"]

    # Add downsample continuous queries
    expected_cqs_names += ["cq_measurement_downsample_1m",
                           "cq_measurement_downsample_1h",
                           "cq_measurement_downsample_1d",
                           "cq_measurement_downsample_all_1m",
                           "cq_measurement_downsample_all_1h",
                           "cq_measurement_downsample_all_1d"]

    # Add multitrees queries
    multitree_nodes = get_nodes()
    simplified_children = []
    for node in multitree_nodes:
        if "simplified_children" in node:
            simplified_children += node.get("simplified_children")
    for node in multitree_nodes:
        if node.get("id") in simplified_children:
            continue
        if "electrical_mgmt_board" in node.get("id"):
            continue
        expected_cqs_names += ["cq_%s_%s" % (node.get("id"), duration) for duration in ["30s", "1m", "1h", "1d"]]

    return expected_cqs_names
