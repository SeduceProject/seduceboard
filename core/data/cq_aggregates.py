import logging
from core.config.aggregates_config import AGGREGATES_CONFIG
from influxdb.exceptions import InfluxDBClientError as InfluxDBClientError
from core.data.influx import get_influxdb_client, get_influxdb_parameters


def cqs_recreate_all(force_creation=False):
    db_name = get_influxdb_parameters().get("database")
    db_client = get_influxdb_client()

    query = "show continuous queries"
    # #print(query)
    cqs = list(db_client.query(query, database=db_name).get_points())
    cqs_names = map(lambda x: x["name"], cqs)

    if force_creation:
        logging.debug("Dropping all continuous queries")
        for cq_name in cqs_names:
            query = """DROP CONTINUOUS QUERY %s ON %s""" % (cq_name, db_name)
            logging.debug("Dropping all continuous queries")
            # #print(query)
            db_client.query(query, database=db_name)
            query = """DROP SERIES from %s""" % (cq_name)
            # #print(query)
            logging.debug("Dropping all continuous queries' series")
            db_client.query(query, database=db_name)

    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    cqs_updated = False

    if force_creation or "cq_measurement_downsample_1m" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1m"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_1m" ON "{db_name}"
        BEGIN
            SELECT %s, mean("value") as value INTO "measurement_downsample_1m" FROM "sensors" GROUP BY time(1m), sensor
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_1h" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1h"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_1h" ON "{db_name}"
        BEGIN
            SELECT %s, mean("mean") as value INTO "measurement_downsample_1h" FROM "measurement_downsample_1m" GROUP BY time(1h), sensor
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_1d" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_1d"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_1d" ON "{db_name}"
        BEGIN
            SELECT %s, mean("mean") as value INTO "measurement_downsample_1d" FROM "measurement_downsample_1h" GROUP BY time(1d), sensor
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1m" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1m"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1m" ON "{db_name}"
        BEGIN
            SELECT %s, mean("value") as value INTO "measurement_downsample_all_1m" FROM "sensors" GROUP BY time(1m), sensor_type
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1h" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1h"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1h" ON "{db_name}"
        BEGIN
            SELECT %s, mean("mean") as value INTO "measurement_downsample_all_1h" FROM "measurement_downsample_all_1m" GROUP BY time(1h), sensor_type
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
        cqs_updated = True

    if force_creation or "cq_measurement_downsample_all_1d" not in cqs_names:
        logging.debug("Computing '%s' continuous query" % ("cq_measurement_downsample_all_1d"))
        query = f"""CREATE CONTINUOUS QUERY "cq_measurement_downsample_all_1d" ON "{db_name}"
        BEGIN
            SELECT %s, mean("mean") as value INTO "measurement_downsample_all_1d" FROM "measurement_downsample_all_1h" GROUP BY time(1d), sensor_type
        END""" % (aggregated_fields)
        # #print(query)
        db_client.query(query, database=db_name)
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
            query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
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
            # #print(query)
            db_client.query(query, database=db_name)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every minute)
        cq_name_1m = "cq_measurement_%s_aggregate_1m" % (aggregate_name)
        if force_creation or cq_name_1m not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1m))
            query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1m), sensor_type
            END""" % (cq_name_1m,
                      aggregated_fields,
                      cq_name_1m,
                      cq_name)
            #print(query)
            db_client.query(query, database=db_name)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every hour)
        cq_name_1h = "cq_measurement_%s_aggregate_1h" % (aggregate_name)
        if force_creation or cq_name_1h not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1h))
            query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1h), sensor_type
            END""" % (cq_name_1h,
                      aggregated_fields,
                      cq_name_1h,
                      cq_name)
            #print(query)
            db_client.query(query, database=db_name)
            cqs_updated = True

        # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every day)
        cq_name_1d = "cq_measurement_%s_aggregate_1d" % (aggregate_name)
        if force_creation or cq_name_1d not in cqs_names:
            logging.debug("Computing '%s' continuous query" % (cq_name_1d))
            query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1d), sensor_type
            END""" % (cq_name_1d,
                      aggregated_fields,
                      cq_name_1d,
                      cq_name)
            #print(query)
            db_client.query(query, database=db_name)
            cqs_updated = True

    db_client.close()

    return cqs_updated


def cqs_recompute_data():
    db_name = get_influxdb_parameters().get("database")
    db_client = get_influxdb_client()

    first_value_candidates = list(db_client.query("select first(value) from sensors", database=db_name).get_points())
    if len(first_value_candidates) == 0:
        return False

    first_value = first_value_candidates[0]
    oldest_timestamp = first_value["time"]

    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1m"))
    query = """SELECT %s, mean("value") as value
    INTO "measurement_downsample_1m"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1m), sensor""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1h"))
    query = """SELECT %s, mean("mean") as value
    INTO "measurement_downsample_1h"
    FROM "measurement_downsample_1m"
    WHERE time >= '%s'
    GROUP BY time(1h), sensor""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_1d"))
    query = """SELECT %s, mean("mean") as value
    INTO "measurement_downsample_1d"
    FROM "measurement_downsample_1h"
    WHERE time >= '%s'
    GROUP BY time(1d), sensor""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1m"))
    query = """SELECT %s, mean("value") as value
    INTO "measurement_downsample_all_1m"
    FROM "sensors"
    WHERE time >= '%s'
    GROUP BY time(1m), sensor_type""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1h"))
    query = """SELECT %s, mean("mean") as value
    INTO "measurement_downsample_all_1h"
    FROM "measurement_downsample_all_1m"
    WHERE time >= '%s'
    GROUP BY time(1h), sensor_type""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

    logging.debug("Recomputing '%s' continuous query" % ("measurement_downsample_all_1d"))
    query = """SELECT %s, mean("mean") as value
    INTO "measurement_downsample_all_1d"
    FROM "measurement_downsample_all_1h"
    WHERE time >= '%s'
    GROUP BY time(1d), sensor_type""" % (aggregated_fields, oldest_timestamp)
    #print(query)
    db_client.query(query, database=db_name)

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
        # print(query)
        db_client.query(query, database=db_name)

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
        #print(query)
        db_client.query(query, database=db_name)

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
        #print(query)
        db_client.query(query, database=db_name)

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
        #print(query)
        db_client.query(query, database=db_name)

    db_client.close()

    return True


def multitree_get_cqs_and_series_names(cq_name):

    series = []
    cqs = []

    aggregate_frequency = "30s"

    # CQ for summing data collected periodically according to a sensor type
    cq_name_freq = "%s_%s" % (cq_name, aggregate_frequency)
    cqs += [cq_name_freq]
    series += [cq_name_freq]

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every minute)
    cq_name_1m = "%s_1m" % (cq_name)
    cqs += [cq_name_1m]
    series += [cq_name_1m]

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every hour)
    cq_name_1h = "%s_1h" % (cq_name)
    cqs += [cq_name_1h]
    series += [cq_name_1h]

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every day)
    cq_name_1d = "%s_1d" % (cq_name)
    cqs += [cq_name_1d]
    series += [cq_name_1d]

    return {
        "cqs": cqs,
        "series": series
    }


def multitree_drop_cqs_and_series_names(cq_name):
    db_name = get_influxdb_parameters().get("database")
    db_client = get_influxdb_client()

    multitree_data = multitree_get_cqs_and_series_names(cq_name)
    series = multitree_data["series"]
    cqs = multitree_data["cqs"]

    for cq_name in cqs:
        query = """DROP CONTINUOUS QUERY %s ON %s""" % (cq_name, db_name)
        logging.debug("Dropping all continuous queries")
        #print(query)
        try:
            db_client.query(query, database=db_name)
        except InfluxDBClientError:
            print("cq \"%s\" was already destroyed" % (cq_name))
    for serie_name in series:
        query = """DROP SERIES from %s""" % (serie_name)
        #print(query)
        logging.debug("Dropping all continuous queries' series")
        try:
            db_client.query(query, database=db_name)
        except InfluxDBClientError:
            print("serie %s was already destroyed" % (serie_name))

    db_client.close()


def multitree_create_continuous_query(cq_name, sub_query_sets):
    db_name = get_influxdb_parameters().get("database")
    db_client = get_influxdb_client()

    # Generate a a criterion
    filter_expression = " or ".join(map(lambda x: """sensor='%s' """ % (x), sub_query_sets))

    aggregate_frequency = "30s"
    aggregate_function_level1 = "sum"
    aggregate_function_level2 = "mean"
    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    # CQ for summing data collected periodically according to a sensor type
    cq_name_freq = "%s_%s" % (cq_name, aggregate_frequency)
    logging.debug("Computing '%s' continuous query" % (cq_name))
    query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
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
            END""" % (cq_name_freq,
                      aggregate_function_level1,
                      aggregate_function_level2,
                      cq_name_freq,
                      aggregate_function_level2,
                      filter_expression,
                      aggregate_frequency,
                      aggregate_frequency)
    #print(query)
    db_client.query(query, database=db_name)
    cqs_updated = True

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every minute)
    cq_name_1m = "%s_1m" % (cq_name)
    logging.debug("Computing '%s' continuous query" % (cq_name_1m))
    query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1m), sensor_type
            END""" % (cq_name_1m,
                      aggregated_fields,
                      cq_name_1m,
                      cq_name_freq)
    #print(query)
    db_client.query(query, database=db_name)
    cqs_updated = True

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every hour)
    cq_name_1h = "%s_1h" % (cq_name)
    logging.debug("Computing '%s' continuous query" % (cq_name_1h))
    query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1h), sensor_type
            END""" % (cq_name_1h,
                      aggregated_fields,
                      cq_name_1h,
                      cq_name_freq)
    #print(query)
    db_client.query(query, database=db_name)
    cqs_updated = True

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view (aggregate every day)
    cq_name_1d = "%s_1d" % (cq_name)
    logging.debug("Computing '%s' continuous query" % (cq_name_1d))
    query = f"""CREATE CONTINUOUS QUERY "%s" ON "{db_name}"
            BEGIN
                SELECT %s INTO "%s" FROM "%s" GROUP BY time(1d), sensor_type
            END""" % (cq_name_1d,
                      aggregated_fields,
                      cq_name_1d,
                      cq_name_freq)
    #print(query)
    db_client.query(query, database=db_name)

    db_client.close()

    return True


def multitree_rebuild_continuous_query(cq_name, sub_query_sets):
    db_name = get_influxdb_parameters().get("database")
    db_client = get_influxdb_client()

    # Generate a a criterion
    filter_expression = " or ".join(map(lambda x: """sensor='%s' """ % (x), sub_query_sets))

    first_value_candidates = list(db_client.query("select first(value) from sensors", database=db_name).get_points())
    if len(first_value_candidates) == 0:
        return False

    first_value = first_value_candidates[0]
    oldest_timestamp = first_value["time"]
    aggregate_frequency = "30s"
    aggregate_function_level1 = "sum"
    aggregate_function_level2 = "mean"
    aggregated_fields = """sum("value"), mean("value"), stddev("value"), count("value"), median("value"), min("value"), max("value")"""

    # CQ for making an average data periodically collected for the current aggregate
    cq_name_freq = "%s_%s" % (cq_name, aggregate_frequency)
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
                                    cq_name_freq,
                                    aggregate_function_level2,
                                    filter_expression,
                                    oldest_timestamp,
                                    aggregate_frequency,
                                    oldest_timestamp,
                                    aggregate_frequency)
    #print(query)
    db_client.query(query, database=db_name)

    # CQ for aggregating data from cq_measurement_wattmeters_aggregate_10s view
    cq_name_1m = "%s_1m" % (cq_name)
    logging.debug("Recomputing '%s' continuous query" % (cq_name_1m))
    query = """SELECT %s
            INTO "%s_1m"
            FROM "%s"
            WHERE time >= '%s'
            GROUP BY time(1m), sensor_type""" % (aggregated_fields,
                                                 cq_name,
                                                 cq_name_freq,
                                                 oldest_timestamp)
    # #print(query)
    db_client.query(query, database=db_name)

    cq_name_1h = "%s_1h" % (cq_name)
    logging.debug("Recomputing '%s' continuous query" % (cq_name_1h))
    query = """SELECT %s
            INTO "%s_1h"
            FROM "%s"
            WHERE time >= '%s'
            GROUP BY time(1h), sensor_type""" % (aggregated_fields,
                                                 cq_name,
                                                 cq_name_freq,
                                                 oldest_timestamp)
    # #print(query)
    db_client.query(query, database=db_name)

    cq_name_1d = "%s_1d" % (cq_name)
    logging.debug("Recomputing '%s' continuous query" % (cq_name_1d))
    query = """SELECT %s
            INTO "%s_1d"
            FROM "%s"
            WHERE time >= '%s'
            GROUP BY time(1d), sensor_type""" % (aggregated_fields,
                                                 cq_name,
                                                 cq_name_freq,
                                                 oldest_timestamp)
    # #print(query)
    db_client.query(query, database=db_name)

    db_client.close()

    return True


def multitree_build_nested_query_and_dependencies(node, recreate_all):
    from core.data.multitree import get_root_nodes, get_tree, get_node_by_id

    current_node = node["node"] if "node" in node else node
    current_tree = get_tree(current_node)

    cq_name = "cq_%s" % (current_node["id"])
    sub_query_sets = []

    if "target" in current_node:
        sub_query_sets = [current_node["target"]]
    else:
        if False and "simplified_children" in current_node:
            for child in current_node["simplified_children"]:
                child_node = get_node_by_id(child)
                infos = multitree_build_nested_query_and_dependencies(child_node, recreate_all)
                sub_query_sets += infos["sub_query_sets"]
        else:
            for child in current_tree["children"]:
                infos = multitree_build_nested_query_and_dependencies(child, recreate_all)
                sub_query_sets += infos["sub_query_sets"]

    pseudo_query = "insert into %s * from sensors where sensor in [%s]" % (cq_name, ",".join(sub_query_sets))
    # #print(pseudo_query)

    if recreate_all:
        multitree_create_continuous_query(cq_name, sub_query_sets)
    else:
        multitree_rebuild_continuous_query(cq_name, sub_query_sets)

    return {"query_name": cq_name, "sub_query_sets": sub_query_sets}


def multitree_drop_nested_query_and_dependencies(node, recreate_all):
    from core.data.multitree import get_root_nodes, get_tree, get_node_by_id

    current_node = node["node"] if "node" in node else node
    current_tree = get_tree(current_node)
    cq_name = "cq_%s" % (current_node["id"])
    sub_query_sets = []

    if "target" in current_node:
        sub_query_sets = [current_node["target"]]
    else:
        if "simplified_children" in current_node:
            for child in current_node["simplified_children"]:
                child_node = get_node_by_id(child)
                infos = multitree_drop_nested_query_and_dependencies(child_node, recreate_all)
                sub_query_sets += infos["sub_query_sets"]

        for child in current_tree["children"]:
            infos = multitree_drop_nested_query_and_dependencies(child, recreate_all)
            sub_query_sets += infos["sub_query_sets"]

    pseudo_query = "drop %s *" % (cq_name)
    # #print(pseudo_query)

    multitree_drop_cqs_and_series_names(cq_name)

    return {"query_name": cq_name, "sub_query_sets": sub_query_sets}


def cq_multitree_recreate_all(recreate_all=False):
    from core.data.multitree import get_root_nodes

    if recreate_all:
        for root_node in get_root_nodes():
            multitree_drop_nested_query_and_dependencies(root_node, recreate_all)

    for root_node in get_root_nodes():
        multitree_build_nested_query_and_dependencies(root_node, recreate_all)
    return True
