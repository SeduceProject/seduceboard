import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_sensors_by_collect_method
import time
import arrow
from tests.utils import mock_data


class TestTemperatureRegisterer(unittest.TestCase):

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
        db_client.close()

        # Create a TemperatureRegister agent
        from tests.utils import FakeTemperatureRegistererAgent

        cls.fake_temperature_registerer = FakeTemperatureRegistererAgent()
        cls.fake_temperature_registerer.start()

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

        # Stop the TemperatureRegister agent
        cls.fake_temperature_registerer.stop()


    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from bin.temperature_registerer import flush_records
        from core.data.influx import db_last_sensors_updates

        parameters = get_influxdb_parameters()
        db_client = get_influxdb_client()

        import requests
        requests.post("http://127.0.0.1:5500/temperature/list", json=[{
            "sensor": "3b96f85809fc2c27",
            "v": 42.1
        },{
            "sensor": "3ba6b75809fc0c6f",
            "v": 42.2
        }])

        time.sleep(2)

        last_sensor_updates = db_last_sensors_updates()

        self.assertEqual(len(last_sensor_updates), 2)

        for sensor_reading in last_sensor_updates:
            self.assertIn(sensor_reading.get("sensor"), ['3b96f85809fc2c27', '3ba6b75809fc0c6f'])
            self.assertGreaterEqual(sensor_reading.get("last_value"), 42.1)
            self.assertLessEqual(sensor_reading.get("last_value"), 42.2)
            self.assertIn(sensor_reading.get("location"), ["room\\ exterior"])
            self.assertIn(sensor_reading.get("unit"), ['celsius'])
            self.assertIn(sensor_reading.get("sensor_type"), ['temperature'])

            reading_date = arrow.get(sensor_reading.get("time"))
            self.assertLessEqual(abs(reading_date.timestamp - time.time()), 120)


if __name__ == '__main__':
    unittest.main()
