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

        cls.modbus_agent_little_endian = FakeModbusAgent(port=5021, endian="little")
        cls.modbus_agent_little_endian.start()

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
        cls.modbus_agent_little_endian.stop()

    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_modbus_sensors
        from bin.modbus_crawler import new_modbus_reading
        from core.data.influx import db_last_sensors_updates

        expected_values = {
            "inrow_group_cool_output": 4200,    # big_endian_int32
            "inrow_group_cool_output2": 1200,   # little_endian_uint32
            "inrow_group_cool_output3": 6400,   # big_endian_int16
            "inrow_group_cool_output4": 12800,  # little_endian_uint16
            "inrow_group_cool_output5": 25600,  # big_endian_float32
            "inrow_group_cool_output_little": 4200,  # big_endian_int32
            "inrow_group_cool_output2_little": 1200,  # little_endian_uint32
            "inrow_group_cool_output3_little": 6400,  # big_endian_int16
            "inrow_group_cool_output4_little": 12800,  # little_endian_uint16
            "inrow_group_cool_output5_little": 25600,  # big_endian_float32
        }

        # with requests_mock.Mocker(real_http=True) as m:

        parameters = get_influxdb_parameters()
        db_client = get_influxdb_client()

        modbus_sensors = get_modbus_sensors()

        for modbus_sensor in modbus_sensors:
            new_modbus_reading(modbus_sensor)

        last_sensor_updates = db_last_sensors_updates()

        self.assertEqual(len(last_sensor_updates), len(list(expected_values.keys())))

        for sensor_reading in last_sensor_updates:

            expected_value = expected_values.get(sensor_reading.get("sensor"))

            self.assertIn(sensor_reading.get("sensor"), list(expected_values.keys()))
            self.assertGreaterEqual(sensor_reading.get("last_value"), expected_value)
            self.assertLessEqual(sensor_reading.get("last_value"), expected_value)
            self.assertIn(sensor_reading.get("location"), ["not\\ specified"])
            self.assertIn(sensor_reading.get("unit"), ['W'])
            self.assertIn(sensor_reading.get("sensor_type"), ['wattmeter'])

            reading_date = arrow.get(sensor_reading.get("time"))
            self.assertLessEqual(abs(reading_date.timestamp - time.time()), 120)


if __name__ == '__main__':
    unittest.main()
