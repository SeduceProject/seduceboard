import unittest
from tests.utils import mock_data


class TestInflux(unittest.TestCase):

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
        cls.start_timestamp = 1566368000
        cls.end_timestamp = cls.start_timestamp + 48 * 3600
        cls.sensors = {
            "wattmeter": ["wattmeter1", "wattmeter2"],
            "temperature": ["3b96f85809fc2c27", "3ba6b75809fc0c6f", "3bd10a5909fc6c3b", "3bbefa5809fc2cb3"]
        }
        for sensor_type in cls.sensors:
            for sensor in cls.sensors.get(sensor_type):
                for value in range(0, 48 * 3600, 15):
                    data += [{
                        "measurement": "sensors",
                        "fields": {
                            "value": value
                        },
                        "time": cls.start_timestamp + value,
                        "tags": {
                            "location": "room exterior",
                            "sensor": f"{sensor}",
                            "unit": "celsius",
                            "sensor_type": f"{sensor_type}"
                        }
                    }]
            db_client.write_points(data, time_precision="s", batch_size=8 * 3600)

        # Create few queries in charge of computing aggregated data
        cqs = [
            {
                "name": "cq_measurement_downsample_1m",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(value) AS value"
                         " INTO measurement_downsample_1m"
                         " FROM sensors GROUP BY time(1m), sensor"
            },
            {
                "name": "cq_measurement_downsample_1h",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value"
                         " INTO measurement_downsample_1h "
                         " FROM measurement_downsample_1m GROUP BY time(1h), sensor"
            },
            {
                "name": "cq_measurement_downsample_1d",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value"
                         " INTO measurement_downsample_1d"
                         " FROM measurement_downsample_1h GROUP BY time(1d), sensor"
            },
            {
                "name": "cq_measurement_downsample_all_1m",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(value) AS value"
                         " INTO measurement_downsample_all_1m"
                         " FROM sensors GROUP BY time(1m), sensor_type"
            },
            {
                "name": "cq_measurement_downsample_all_1h",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value"
                         " INTO measurement_downsample_all_1h"
                         " FROM measurement_downsample_all_1m GROUP BY time(1h), sensor_type"
            },
            {
                "name": "cq_measurement_downsample_all_1d",
                "query": "SELECT sum(value), mean(value), stddev(value), count(value), median(value), min(value), max(value), mean(mean) AS value"
                         " INTO measurement_downsample_all_1d"
                         " FROM measurement_downsample_all_1h GROUP BY time(1d), sensor_type"
            }
        ]

        for cq in cqs:
            db_client.create_continuous_query(cq.get("name"), cq.get("query"))

        # Execute the CQs
        for cq in cqs:
            db_client.query(cq.get("query"))

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
    def test_create_influxdb_connection(self):
        from core.data.influx import create_influxdb_connection

        test_failed = True
        try:
            db_client = create_influxdb_connection()
            test_failed = False
        except:
            print("Could not connect to the database")

        self.assertFalse(test_failed)

    @mock_data
    def test_get_influxdb_client(self):
        from core.data.influx import get_influxdb_client

        test_failed = True
        try:
            db_client = get_influxdb_client()
            test_failed = False
        except:
            print("Could not connect to the database")

        self.assertFalse(test_failed)

    @mock_data
    def test_db_sensor_data(self):
        from core.data.influx import db_sensor_data
        sensor_data = db_sensor_data("3b96f85809fc2c27",
                                     start_date=f"{self.start_timestamp}s",
                                     end_date=f"{self.start_timestamp + 1500}s")

        self.assertEqual(len(sensor_data.get("values")), 101)

        sensor_data = db_sensor_data("3b96f85809fc2c27",
                                     start_date=f"{self.start_timestamp + 50}s",
                                     end_date=f"{self.start_timestamp + 120}s")

        self.assertEqual(len(sensor_data.get("values")), 5)

    @mock_data
    def test_db_sensors(self):
        from core.data.influx import db_sensors

        sensors = db_sensors()
        self.assertEqual(len(sensors.get("sensors")), 6)

        sensors = db_sensors(sensor_type="temperature")
        self.assertEqual(len(sensors.get("sensors")), 4)

    @mock_data
    def test_db_sensor_types(self):
        from core.data.influx import db_sensor_types

        sensor_types = db_sensor_types()

        for sensor_type in sensor_types.get("sensor_types"):
            self.assertTrue(sensor_type in ["wattmeter", "temperature"])

    @mock_data
    def test_db_locations(self):
        from core.data.influx import db_locations

        locations = db_locations()

        self.assertListEqual(locations.get("locations"), ["room exterior"])

    @mock_data
    def test__get_aggregate_serie_name(self):
        from core.data.influx import _get_aggregate_serie_name

        aggregate_serie_name = _get_aggregate_serie_name("daily")
        self.assertEqual(aggregate_serie_name, "measurement_downsample_1d")

        aggregate_serie_name = _get_aggregate_serie_name("hourly")
        self.assertEqual(aggregate_serie_name, "measurement_downsample_1h")

        aggregate_serie_name = _get_aggregate_serie_name("else")
        self.assertEqual(aggregate_serie_name, "measurement_downsample_1m")

    @mock_data
    def test_db_aggregated_sensor_data(self):
        from core.data.influx import db_aggregated_sensor_data
        from math import floor

        aggregated_sensor_data = db_aggregated_sensor_data("3b96f85809fc2c27",
                                                           start_date=f"{TestInflux.start_timestamp - 24 * 3600}s",
                                                           end_date=f"{TestInflux.start_timestamp + 1 * 3600}s",
                                                           how="daily")

        self.assertListEqual(aggregated_sensor_data.get("sums"), [569145.1595744682, None])
        self.assertListEqual(aggregated_sensor_data.get("mins"), [1387.659574468085, None])
        self.assertListEqual(aggregated_sensor_data.get("counts"), [18, None])

        aggregated_sensor_data = db_aggregated_sensor_data("3b96f85809fc2c27",
                                                           start_date=f"{TestInflux.start_timestamp}s",
                                                           end_date=f"{TestInflux.start_timestamp + 12 * 3600}s",
                                                           how="hourly")

        self.assertEqual(aggregated_sensor_data.get("sums")[0], 275850)
        self.assertEqual(aggregated_sensor_data.get("sums")[-2], 2651850)
        self.assertEqual(aggregated_sensor_data.get("mins")[0], 2827.5)
        self.assertEqual(aggregated_sensor_data.get("mins")[-2], 42427.5)
        self.assertEqual(aggregated_sensor_data.get("counts")[0], 60)
        self.assertEqual(aggregated_sensor_data.get("counts")[-2], 60)

        aggregated_sensor_data = db_aggregated_sensor_data("3b96f85809fc2c27",
                                                           start_date=f"{TestInflux.start_timestamp}s",
                                                           end_date=f"{TestInflux.start_timestamp + 3 * 3600}s",
                                                           how="minutely")

        self.assertEqual(aggregated_sensor_data.get("sums")[0], 270)
        self.assertEqual(aggregated_sensor_data.get("sums")[-2], 43230)
        self.assertEqual(aggregated_sensor_data.get("mins")[0], 45)
        self.assertEqual(aggregated_sensor_data.get("mins")[-2], 10785)
        self.assertEqual(aggregated_sensor_data.get("counts")[0], 4)
        self.assertEqual(aggregated_sensor_data.get("counts")[-2], 4)

    @mock_data
    def test_db_rack_side_temperature_data(self):
        from core.data.influx import db_rack_side_temperature_data
        from core.config.room_config import get_temperature_sensors_infrastructure

        infra = get_temperature_sensors_infrastructure()

        rack_side_temperature_data = db_rack_side_temperature_data("back",
                                                                   start_date=f"{TestInflux.start_timestamp}s",
                                                                   end_date=f"{TestInflux.start_timestamp + 3 * 3600}s",
                                                                   how="minutely",
                                                                   only_mean=False)

        self.assertEqual(rack_side_temperature_data.get("timestamps")[0], "2019-08-21T06:13:00Z")
        self.assertEqual(rack_side_temperature_data.get("timestamps")[-1], "2019-08-21T09:13:00Z")

        self.assertEqual(rack_side_temperature_data.get("means")[0], 15)
        self.assertEqual(rack_side_temperature_data.get("means")[-1], 10792.5)

        self.assertEqual(rack_side_temperature_data.get("maxs")[0], 30)
        self.assertEqual(rack_side_temperature_data.get("maxs")[-1], 10800)

    @mock_data
    def test_db_dump_all_aggregated_data(self):
        from core.data.influx import db_dump_all_aggregated_data

        all_aggregated_data = db_dump_all_aggregated_data(start_date=f"{TestInflux.start_timestamp}s",
                                                          end_date=f"{TestInflux.start_timestamp + 3 * 3600}s",
                                                          group_by="1h")

        for sensor_type in self.sensors:
            for sensor in self.sensors.get(sensor_type):

                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("timestamps")[0], "2019-08-21T06:00:00Z")
                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("timestamps")[-1], "2019-08-21T09:00:00Z")

                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("means")[0], 1395)
                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("means")[-1], 10402.5)

                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("maxs")[0], 2790)
                self.assertEqual(all_aggregated_data.get("sensors_data").get(sensor).get("maxs")[-1], 10800)

    @mock_data
    def test__get_aggregate_multitree_serie_name(self):
        from core.data.influx import _get_aggregate_multitree_serie_name

        aggregate_multitree_serie_name = _get_aggregate_multitree_serie_name("wattmeter1", how="daily")
        self.assertEqual(aggregate_multitree_serie_name, "cq_wattmeter1_1d")

        aggregate_multitree_serie_name = _get_aggregate_multitree_serie_name("wattmeter1", how="hourly")
        self.assertEqual(aggregate_multitree_serie_name, "cq_wattmeter1_1h")

        aggregate_multitree_serie_name = _get_aggregate_multitree_serie_name("wattmeter1", how="minutely")
        self.assertEqual(aggregate_multitree_serie_name, "cq_wattmeter1_1m")

        print(aggregate_multitree_serie_name)

    @mock_data
    def test__get_datainfo_serie_name(self):
        from core.data.influx import _get_datainfo_serie_name

        datainfo_serie_name = _get_datainfo_serie_name("daily")
        self.assertEqual(datainfo_serie_name, "measurement_downsample_all_1d")

        datainfo_serie_name = _get_datainfo_serie_name("hourly")
        self.assertEqual(datainfo_serie_name, "measurement_downsample_all_1h")

        datainfo_serie_name = _get_datainfo_serie_name("minutely")
        self.assertEqual(datainfo_serie_name, "measurement_downsample_all_1m")

    @mock_data
    def test_db_datainfo(self):
        from core.data.influx import db_datainfo

        datainfo = db_datainfo(start_date=f"{TestInflux.start_timestamp}s")

        self.assertTrue(datainfo.get("range").get("timestamps")[0], "2019-08-22T00:00:00Z")
        self.assertTrue(datainfo.get("range").get("timestamps")[-1], "2019-08-24T00:00:00+00:00")

        self.assertTrue(datainfo.get("range").get("last_empty_timestamp"), "2019-08-24T00:00:00+00:00")

        self.assertListEqual(datainfo.get("range").get("maxs"), [148597.5, 148597.5, 172415.89285714287, 172415.89285714287, None])

    @mock_data
    def test_db_get_navigation_data(self):
        from core.data.influx import db_get_navigation_data

        navigation_data = db_get_navigation_data("wattmeter", start_date=f"{TestInflux.start_timestamp}s")

        self.assertTrue(navigation_data.get("range").get("timestamps")[0], "2019-08-22T00:00:00Z")
        self.assertTrue(navigation_data.get("range").get("timestamps")[-1], "2019-08-23T00:00:00Z")

        self.assertTrue(navigation_data.get("range").get("last_empty_timestamp"), "2019-08-23T00:00:00Z")

        self.assertListEqual(navigation_data.get("range").get("maxs"), [148597.5, 172415.89285714287])

    @mock_data
    def test_db_get_sensors_with_tags(self):
        from core.data.influx import db_get_sensors_with_tags

        sensors_with_tags = db_get_sensors_with_tags()

        self.assertListEqual(list(sensors_with_tags.keys()), ['3b96f85809fc2c27', '3ba6b75809fc0c6f', '3bbefa5809fc2cb3', '3bd10a5909fc6c3b', 'wattmeter1', 'wattmeter2'])

        self.assertEqual(sensors_with_tags.get('3b96f85809fc2c27').get("location"), "room\\ exterior")
        self.assertEqual(sensors_with_tags.get('3b96f85809fc2c27').get("sensor"), "3b96f85809fc2c27")
        self.assertEqual(sensors_with_tags.get('3b96f85809fc2c27').get("sensor_type"), "temperature")
        self.assertEqual(sensors_with_tags.get('3b96f85809fc2c27').get("unit"), "celsius")

    @mock_data
    def test_db_oldest_point_in_serie(self):
        from core.data.influx import db_oldest_point_in_serie

        oldest_point_in_serie = db_oldest_point_in_serie("wattmeter1")
        self.assertEqual(oldest_point_in_serie.get("time"), "2019-08-21T06:13:20Z")

        oldest_point_in_serie = db_oldest_point_in_serie("*")
        self.assertEqual(oldest_point_in_serie.get("time"), "2019-08-21T06:13:20Z")


if __name__ == '__main__':
    unittest.main()
