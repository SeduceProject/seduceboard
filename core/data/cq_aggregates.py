from core.config.aggregates_config import AGGREGATES_CONFIG
from core.data.db import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from influxdb import InfluxDBClient
import logging


def cqs_recreate_all(force_creation=False):
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    cqs = list(db_client.query("show continuous queries", database=DB_NAME).get_points())
    cqs_names = map(lambda x: x["name"], cqs)

    if force_creation:
        logging.debug("Dropping all continuous queries")
        for cq_name in cqs_names:
            query = """DROP CONTINUOUS QUERY %s ON %s""" % (cq_name, DB_NAME)
            logging.debug("Dropping all continuous queries")
            db_client.query(query, database=DB_NAME)
            query = """DROP SERIES from %s""" % (cq_name)
            logging.debug("Dropping all continuous queries' series")
            db_client.query(query, database=DB_NAME)

    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    cqs_updated = False

    if force_creation or "cq_measurement_downsample_1m" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1m"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_1m" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_1m" FROM "sensors" GROUP BY time(1m), sensor
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_1h" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1h"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_1h" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_1h" FROM "sensors" GROUP BY time(1h), sensor
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_1d" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1d"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_1d" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_1d" FROM "sensors" GROUP BY time(1d), sensor
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1m" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1m"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1m" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_all_1m" FROM "sensors" GROUP BY time(1m), sensor_type
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1h" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1h"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1h" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_all_1h" FROM "sensors" GROUP BY time(1h), sensor_type
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1d" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1d"))
        query = """CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1d" ON "pidiou"
        BEGIN
            SELECT %s INTO "measurement_downsample_all_1d" FROM "sensors" GROUP BY time(1d), sensor_type
        END""" % (aggregated_fields)
        db_client.query(query, database=DB_NAME)
        cqs_updated = True

    for aggregate_name in AGGREGATES_CONFIG:
        aggregate_type = AGGREGATES_CONFIG[aggregate_name]["type"]
        filter_expression = AGGREGATES_CONFIG[aggregate_name]["filter_expression"]
        aggregate_function_level1 = AGGREGATES_CONFIG[aggregate_name]["aggregate_function_level1"]
        aggregate_function_level2 = AGGREGATES_CONFIG[aggregate_name]["aggregate_function_level2"]
        aggregate_frequency = AGGREGATES_CONFIG[aggregate_name]["aggregate_frequency"]

        # CQ for summing data collected periodically according to a sensor type
        cq_name = "cq_measurement_%s_aggregate_%s" % (aggregate_name, aggregate_frequency)
        if force_creation or cq_name not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name))
            query = """CREATE CONTINUOUS QUERY "%s" ON "pidiou"
            BEGIN
                select %s(%s) as value
                INTO "%s"
                from (
                    select %s(value)
                    from sensors
                    where (%s)
                    group by time(%s), sensor
                    )
                group by time(%s)
            END""" % (cq_name,
                      aggregate_function_level1,
                      aggregate_function_level2,
                      cq_name,
                      aggregate_function_level2,
                      filter_expression,
                      aggregate_frequency,
                      aggregate_frequency)
            db_client.query(query, database=DB_NAME)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every minute)
        cq_name_1m = "cq_measurement_%s_aggregate_1m" % (aggregate_name)
        if force_creation or cq_name_1m not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1m))
            query = """CREATE CONTINUOUS QUERY "%s" ON "pidiou"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1m), sensor_type
            END""" % (cq_name_1m,
                      aggregated_fields,
                      cq_name_1m,
                      cq_name)
            db_client.query(query, database=DB_NAME)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every hour)
        cq_name_1h = "cq_measurement_%s_aggregate_1h" % (aggregate_name)
        if force_creation or cq_name_1h not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1h))
            query = """CREATE CONTINUOUS QUERY "%s" ON "pidiou"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1h), sensor_type
            END""" % (cq_name_1h,
                      aggregated_fields,
                      cq_name_1h,
                      cq_name)
            db_client.query(query, database=DB_NAME)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every day)
        cq_name_1d = "cq_measurement_%s_aggregate_1d" % (aggregate_name)
        if force_creation or cq_name_1d not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1d))
            query = """CREATE CONTINUOUS QUERY "%s" ON "pidiou"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1d), sensor_type
            END""" % (cq_name_1d,
                      aggregated_fields,
                      cq_name_1d,
                      cq_name)
            db_client.query(query, database=DB_NAME)
            cqs_updated = True

    return cqs_updated


def cqs_recompute_data():
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    first_value_candidates = list(db_client.query("select first(value) from sensors", database=DB_NAME).get_points())
    if len(first_value_candidates) == 0:
        return False

    first_value = first_value_candidates[0]
    oldest_timestamp = first_value["time"]

    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1m"))
    query = """SELECT %s
    INTO "measurement_downsample_1m"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1m), sensor""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1h"))
    query = """SELECT %s
    INTO "measurement_downsample_1h"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1h), sensor""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1d"))
    query = """SELECT %s
    INTO "measurement_downsample_1d"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1d), sensor""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1m"))
    query = """SELECT %s
    INTO "measurement_downsample_all_1m"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1m), sensor_type""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1h"))
    query = """SELECT %s
    INTO "measurement_downsample_all_1h"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1h), sensor_type""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1d"))
    query = """SELECT %s
    INTO "measurement_downsample_all_1d"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1d), sensor_type""" % (aggregated_fields, oldest_timestamp)
    db_client.query(query, database=DB_NAME)

    for aggregate_name in AGGREGATES_CONFIG:
        aggregate_type = AGGREGATES_CONFIG[aggregate_name]["type"]
        filter_expression = AGGREGATES_CONFIG[aggregate_name]["filter_expression"]
        aggregate_function_level1 = AGGREGATES_CONFIG[aggregate_name]["aggregate_function_level1"]
        aggregate_function_level2 = AGGREGATES_CONFIG[aggregate_name]["aggregate_function_level2"]
        aggregate_frequency = AGGREGATES_CONFIG[aggregate_name]["aggregate_frequency"]

        # CQ for making an average data periodically collected for the current aggregate
        cq_name = "cq_measurement_%s_aggregate_%s" % (aggregate_name, aggregate_frequency)
        logging.debug("Recomputing '%s' continuous query" % (cq_name))
        query = """select %s(%s) as value
        INTO "%s"
        from (
            select %s(value)
            from sensors
            where (%s) and time > '%s'
            group by time(%s), sensor
            )
        where time > '%s'
        group by time(%s)""" % (aggregate_function_level1,
                                aggregate_function_level2,
                                cq_name,
                                aggregate_function_level2,
                                filter_expression,
                                oldest_timestamp,
                                aggregate_frequency,
                                oldest_timestamp,
                                aggregate_frequency)
        db_client.query(query, database=DB_NAME)

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view
        cq_name_1m = "cq_measurement_%s_aggregate_1m" % (aggregate_name)
        logging.debug("Recomputing '%s' continuous query" % (cq_name_1m))
        query = """SELECT %s
        INTO "cq_measurement_%s_aggregate_1m"
        FROM "%s"
        WHERE time >= '%s'
        GROUP BY time(1m), sensor_type""" % (aggregated_fields,
                                             aggregate_name,
                                             cq_name,
                                             oldest_timestamp)
        db_client.query(query, database=DB_NAME)

        cq_name_1h = "cq_measurement_%s_aggregate_1h" % (aggregate_name)
        logging.debug("Recomputing '%s' continuous query" % (cq_name_1h))
        query = """SELECT %s
        INTO "cq_measurement_%s_aggregate_1h"
        FROM "%s"
        WHERE time >= '%s'
        GROUP BY time(1h), sensor_type""" % (aggregated_fields,
                                             aggregate_name,
                                             cq_name,
                                             oldest_timestamp)
        db_client.query(query, database=DB_NAME)

        cq_name_1d = "cq_measurement_%s_aggregate_1d" % (aggregate_name)
        logging.debug("Recomputing '%s' continuous query" % (cq_name_1d))
        query = """SELECT %s
        INTO "cq_measurement_%s_aggregate_1d"
        FROM "%s"
        WHERE time >= '%s'
        GROUP BY time(1d), sensor_type""" % (aggregated_fields,
                                             aggregate_name,
                                             cq_name,
                                             oldest_timestamp)
        db_client.query(query, database=DB_NAME)

    return True
