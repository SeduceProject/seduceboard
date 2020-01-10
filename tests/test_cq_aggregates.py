import unittest
from unittest import mock
import time
from tests.utils import mock_data


class TestCqAggregates(unittest.TestCase):

    # def setUp(self):
    @classmethod
    @mock_data
    def setUpClass(cls):
        # Init InfluxDB
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client

        db_name = get_influxdb_parameters().get("database")
        db_client = get_influxdb_client()

        if db_name == "pidiou":
            raise Exception("Abort: modifying 'pidiou' database")

        db_client.create_database(db_name)

        # Insert some data
        data = []
        start_timestamp = int(time.time() - 48 * 3600)
        sensors = {
            "wattmeter": ["ecotype-1_pdu-Z1.51", "ecotype-1_pdu-Z1.50"]
        }
        for sensor_type in sensors:
            for sensor in sensors.get(sensor_type):
                for value in range(0, 48 * 3600, 15):
                    data += [{
                        "measurement": "sensors",
                        "fields": {
                            "value": value
                        },
                        "time": start_timestamp + value,
                        "tags": {
                            "location": "room exterior",
                            "sensor": f"{sensor}",
                            "unit": "w",
                            "sensor_type": f"{sensor_type}"
                        }
                    }]
            db_client.write_points(data, time_precision="s", batch_size=8 * 3600)

        cls.start_timestamp = start_timestamp
        cls.end_timestamp = start_timestamp + 48 * 3600

        # Set expected continuous queries
        cls.expected_continuous_queries = [
            {
                'name': 'cq_measurement_downsample_1m',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_1m ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(value) AS value INTO tests.autogen.measurement_downsample_1m FROM tests.autogen.sensors GROUP BY time(1m), sensor END'
            },
            {
                'name': 'cq_measurement_downsample_1h',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_1h ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value INTO tests.autogen.measurement_downsample_1h FROM tests.autogen.measurement_downsample_1m GROUP BY time(1h), sensor END'
            },
            {
                'name': 'cq_measurement_downsample_1d',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_1d ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value INTO tests.autogen.measurement_downsample_1d FROM tests.autogen.measurement_downsample_1h GROUP BY time(1d), sensor END'
            },
            {
                'name': 'cq_measurement_downsample_all_1m',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_all_1m ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(value) AS value INTO tests.autogen.measurement_downsample_all_1m FROM tests.autogen.sensors GROUP BY time(1m), sensor_type END'
            },
            {
                'name': 'cq_measurement_downsample_all_1h',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_all_1h ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value INTO tests.autogen.measurement_downsample_all_1h FROM tests.autogen.measurement_downsample_all_1m GROUP BY time(1h), sensor_type END'
            },
            {
                'name': 'cq_measurement_downsample_all_1d',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_downsample_all_1d ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value INTO tests.autogen.measurement_downsample_all_1d FROM tests.autogen.measurement_downsample_all_1h GROUP BY time(1d), sensor_type END'
            },
            {
                'name': 'cq_measurement_wattmeters_aggregate_10s',
                'query': "CREATE CONTINUOUS QUERY cq_measurement_wattmeters_aggregate_10s ON tests BEGIN SELECT sum(mean) AS value INTO tests.autogen.cq_measurement_wattmeters_aggregate_10s FROM (SELECT mean(value) FROM tests.autogen.sensors WHERE (sensor = 'watt_cooler_b232_1' OR sensor = 'watt_cooler_ext_1') GROUP BY time(10s), sensor) GROUP BY time(10s) END"
            },
            {
                'name': 'cq_measurement_wattmeters_aggregate_1m',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_wattmeters_aggregate_1m ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_wattmeters_aggregate_1m FROM tests.autogen.cq_measurement_wattmeters_aggregate_10s GROUP BY time(1m), sensor_type END'
            },
            {
                'name': 'cq_measurement_wattmeters_aggregate_1h',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_wattmeters_aggregate_1h ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_wattmeters_aggregate_1h FROM tests.autogen.cq_measurement_wattmeters_aggregate_10s GROUP BY time(1h), sensor_type END'
            },
            {
                'name': 'cq_measurement_wattmeters_aggregate_1d',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_wattmeters_aggregate_1d ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_wattmeters_aggregate_1d FROM tests.autogen.cq_measurement_wattmeters_aggregate_10s GROUP BY time(1d), sensor_type END'
            },
            {
                'name': 'cq_measurement_socomecs_aggregate_30s',
                'query': "CREATE CONTINUOUS QUERY cq_measurement_socomecs_aggregate_30s ON tests BEGIN SELECT sum(mean) AS value INTO tests.autogen.cq_measurement_socomecs_aggregate_30s FROM (SELECT mean(value) FROM tests.autogen.sensors WHERE (sensor = 'wattmeter_condensator' OR sensor = 'wattmeter_servers' OR sensor = 'wattmeter_cooling') GROUP BY time(30s), sensor) GROUP BY time(30s) END"
            },
            {
                'name': 'cq_measurement_socomecs_aggregate_1m',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_socomecs_aggregate_1m ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_socomecs_aggregate_1m FROM tests.autogen.cq_measurement_socomecs_aggregate_30s GROUP BY time(1m), sensor_type END'
            },
            {
                'name': 'cq_measurement_socomecs_aggregate_1h',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_socomecs_aggregate_1h ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_socomecs_aggregate_1h FROM tests.autogen.cq_measurement_socomecs_aggregate_30s GROUP BY time(1h), sensor_type END'
            },
            {
                'name': 'cq_measurement_socomecs_aggregate_1d',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_socomecs_aggregate_1d ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_socomecs_aggregate_1d FROM tests.autogen.cq_measurement_socomecs_aggregate_30s GROUP BY time(1d), sensor_type END'
            },
            {
                'name': 'cq_measurement_external_temperature_aggregate_30s',
                'query': "CREATE CONTINUOUS QUERY cq_measurement_external_temperature_aggregate_30s ON tests BEGIN SELECT mean(mean) AS value INTO tests.autogen.cq_measurement_external_temperature_aggregate_30s FROM (SELECT mean(value) FROM tests.autogen.sensors WHERE (location = 'room exterior' AND unit = 'celsius') GROUP BY time(30s), sensor) GROUP BY time(30s) END"
            },
            {
                'name': 'cq_measurement_external_temperature_aggregate_1m',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_external_temperature_aggregate_1m ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_external_temperature_aggregate_1m FROM tests.autogen.cq_measurement_external_temperature_aggregate_30s GROUP BY time(1m), sensor_type END'
            },
            {
                'name': 'cq_measurement_external_temperature_aggregate_1h',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_external_temperature_aggregate_1h ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_external_temperature_aggregate_1h FROM tests.autogen.cq_measurement_external_temperature_aggregate_30s GROUP BY time(1h), sensor_type END'
            },
            {
                'name': 'cq_measurement_external_temperature_aggregate_1d',
                'query': 'CREATE CONTINUOUS QUERY cq_measurement_external_temperature_aggregate_1d ON tests BEGIN SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value) INTO tests.autogen.cq_measurement_external_temperature_aggregate_1d FROM tests.autogen.cq_measurement_external_temperature_aggregate_30s GROUP BY time(1d), sensor_type END'
            }
        ]

        db_client.close()

    # def tearDown(self):
    @classmethod
    @mock_data
    def tearDownClass(cls):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client

        db_name = get_influxdb_parameters().get("database")
        db_client = get_influxdb_client()

        if db_name == "pidiou":
            raise Exception("Abort: modifying 'pidiou' database")

        db_client.drop_database(db_name)
        db_client.close()

    @mock_data
    def test_cqs_recreate_all(self):
        from core.data.cq_aggregates import cqs_recreate_all
        from core.data.influx import get_influxdb_client
        from core.data.influx import get_influxdb_parameters

        result = cqs_recreate_all(force_creation=True)

        self.assertIsNotNone(result)

        db_name = get_influxdb_parameters().get("database")

        db_client = get_influxdb_client()
        influx_continuous_queries = db_client.get_list_continuous_queries()[1][db_name]

        for expected_cq in TestCqAggregates.expected_continuous_queries:
            expected_continuous_query_name = expected_cq.get("name")
            expected_continuous_query_query = expected_cq.get("query")

            influx_continuous_query_candidate = [influx_continuous_query
                                                 for influx_continuous_query in influx_continuous_queries
                                                 if influx_continuous_query["name"] == expected_continuous_query_name]
            self.assertEqual(len(influx_continuous_query_candidate), 1)

            influx_continuous_query = influx_continuous_query_candidate[0]

            self.assertEqual(influx_continuous_query.get("name"), expected_continuous_query_name)
            self.assertEqual(influx_continuous_query.get("query"), expected_continuous_query_query)

    @mock_data
    def test_cqs_recompute_data(self):
        from core.data.cq_aggregates import cqs_recompute_data
        from core.data.influx import get_influxdb_client
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import db_aggregated_sensor_data

        result = db_aggregated_sensor_data("ecotype-1_pdu-Z1.51",
                                  start_date=f"{TestCqAggregates.start_timestamp}s",
                                  end_date=f"{TestCqAggregates.end_timestamp}s",
                                  how="hourly")

        self.assertEqual(len(result.get("means")), 0)

        result = cqs_recompute_data()
        self.assertIsNotNone(result)

        db_name = get_influxdb_parameters().get("database")

        db_client = get_influxdb_client()

        result = db_aggregated_sensor_data("ecotype-1_pdu-Z1.51",
                                  start_date=f"{TestCqAggregates.start_timestamp}s",
                                  end_date=f"{TestCqAggregates.end_timestamp}s",
                                  how="hourly")

        self.assertGreaterEqual(len(result.get("means")), 48)
        self.assertLessEqual(len(result.get("means")), 49)

    @mock_data
    def test_multitree_get_cqs_and_series_names(self):
        pass

    @mock_data
    def test_multitree_drop_cqs_and_series_names(self):
        pass

    @mock_data
    def test_multitree_create_continuous_query(self):
        pass

    @mock_data
    def test_multitree_rebuild_continuous_query(self):
        pass

    @mock_data
    def test_multitree_build_nested_query_and_dependencies(self):
        pass

    @mock_data
    def test_multitree_drop_nested_query_and_dependencies(self):
        pass

    @mock_data
    def test_cq_multitree_recreate_all(self):
        pass


if __name__ == '__main__':
    unittest.main()
