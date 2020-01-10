import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_sensors_by_collect_method, FakeModbusAgent
import arrow
import requests_mock
import time
from tests.utils import mock_data

class TestModbusCollecter(unittest.TestCase):

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

        # Create a fake modbus agent
        cls.modbus_agent = FakeModbusAgent()
        cls.modbus_agent.start()

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

        # Stop the fake modbus agent
        cls.modbus_agent.stop()

    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_modbus_sensors
        from bin.modbus_crawler import new_modbus_reading
        from core.data.influx import db_last_sensors_updates

        with requests_mock.Mocker(real_http=True) as m:

            parameters = get_influxdb_parameters()
            db_client = get_influxdb_client()

            modbus_sensors = get_modbus_sensors()

            for modbus_sensor in modbus_sensors:
                new_modbus_reading(modbus_sensor)

            last_sensor_updates = db_last_sensors_updates()

            self.assertEqual(len(last_sensor_updates), 1)

            for sensor_reading in last_sensor_updates:
                self.assertIn(sensor_reading.get("sensor"), ['inrow_group_cool_output'])
                self.assertGreaterEqual(sensor_reading.get("last_value"), 4200)
                self.assertLessEqual(sensor_reading.get("last_value"), 4200)
                self.assertIn(sensor_reading.get("location"), ["not\\ specified"])
                self.assertIn(sensor_reading.get("unit"), ['W'])
                self.assertIn(sensor_reading.get("sensor_type"), ['wattmeter'])

                reading_date = arrow.get(sensor_reading.get("time"))
                self.assertLessEqual(abs(reading_date.timestamp - time.time()), 120)


if __name__ == '__main__':
    unittest.main()
