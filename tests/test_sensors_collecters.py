import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_sensors_by_collect_method, FakeModbusAgent
import arrow
import requests_mock
import time
import random
from tests.utils import mock_data


class TestFluksoCollecter(unittest.TestCase):

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

        # Create a fake flukso agent

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

        # Stop the fake flukso agent

    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_flukso_sensors
        from bin.sensors_crawler import new_flukso_reading
        from core.data.influx import db_last_sensors_updates

        with requests_mock.Mocker(real_http=True) as m:

            now = int(time.time())
            now_60s_later = now + 60

            fake_response = [
                [ts, random.choice([7, 8])]
                for ts in range(now, now_60s_later)
            ]

            m.get(
                'http://192.168.1.3:8080/sensor/c6a2caade50d7532ee3a3292238fd587?version=1.0&interval=minute&unit=watt',
                json=fake_response)

            parameters = get_influxdb_parameters()
            db_client = get_influxdb_client()

            flukso_sensors = get_flukso_sensors()

            for flukso_sensor in flukso_sensors:
                new_flukso_reading(flukso_sensor)

            last_sensor_updates = db_last_sensors_updates()

            self.assertEqual(len(last_sensor_updates), 1)

            for sensor_reading in last_sensor_updates:
                self.assertIn(sensor_reading.get("sensor"), ['watt_cooler_b232_1'])
                self.assertGreaterEqual(sensor_reading.get("last_value"), 7)
                self.assertLessEqual(sensor_reading.get("last_value"), 8)
                self.assertIn(sensor_reading.get("location"), ['B232'])
                self.assertIn(sensor_reading.get("unit"), ['W'])
                self.assertIn(sensor_reading.get("sensor_type"), ['wattmeter'])

                reading_date = arrow.get(sensor_reading.get("time"))
                self.assertGreaterEqual(reading_date.timestamp, now)
                self.assertLessEqual(reading_date.timestamp, now_60s_later)


class TestSocomecCollecter(unittest.TestCase):

    @mock_data
    def setUp(self):
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
        self.modbus_agent = FakeModbusAgent(port=5021)
        self.modbus_agent.start()

    @mock_data
    def tearDown(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client

        db_name = get_influxdb_parameters().get("database")
        db_client = get_influxdb_client()

        if db_name == "pidiou":
            raise Exception("Abort: modifying 'pidiou' database")

        db_client.drop_database(db_name)
        db_client.close()

        # Stop the fake modbus agent
        self.modbus_agent.stop()

    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_flukso_sensors, get_socomec_sensors
        from bin.sensors_crawler import new_socomec_reading
        from core.data.influx import db_last_sensors_updates

        with requests_mock.Mocker(real_http=True) as m:

            parameters = get_influxdb_parameters()
            db_client = get_influxdb_client()

            socomec_sensors = get_socomec_sensors()

            for socomec_sensor in socomec_sensors:
                new_socomec_reading(socomec_sensor)

            last_sensor_updates = db_last_sensors_updates()

            self.assertEqual(len(last_sensor_updates), 1)

            for sensor_reading in last_sensor_updates:
                self.assertIn(sensor_reading.get("sensor"), ['wattmeter_condensator'])
                self.assertGreaterEqual(sensor_reading.get("last_value"), 42)
                self.assertLessEqual(sensor_reading.get("last_value"), 42)
                self.assertIn(sensor_reading.get("location"), ['B232'])
                self.assertIn(sensor_reading.get("unit"), ['W'])
                self.assertIn(sensor_reading.get("sensor_type"), ['wattmeter'])

                reading_date = arrow.get(sensor_reading.get("time"))
                self.assertLessEqual(abs(reading_date.timestamp - time.time()), 120)


if __name__ == '__main__':
    unittest.main()
