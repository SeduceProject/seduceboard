import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_sensors_by_collect_method
import time
import arrow
from tests.utils import mock_data


class TestSnmpCollecter(unittest.TestCase):

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

        # Create a SNMP agent
        from tests.utils import FakeSnmpAgent

        cls.snmp_agent = FakeSnmpAgent()
        cls.snmp_agent.start()

        while not cls.snmp_agent.snmpEngine is not None:
            time.sleep(1)

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

        # Stop the SNMP agent
        cls.snmp_agent.stop()


    @mock_data
    def test_adding_new_reading(self):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_snmp_sensors
        from bin.snmp_crawler import read_all_sensors, flush_records
        from core.data.influx import db_last_sensors_updates

        parameters = get_influxdb_parameters()
        db_client = get_influxdb_client()

        snmp_sensors = get_snmp_sensors()

        read_all_sensors(snmp_sensors)
        flush_records(None)

        last_sensor_updates = db_last_sensors_updates()

        self.assertEqual(len(last_sensor_updates), 4)

        for sensor_reading in last_sensor_updates:
            self.assertIn(sensor_reading.get("sensor"), ['ecotype-1_pdu-Z1.50', 'ecotype-2_pdu-Z1.50', 'ecotype-1_pdu-Z1.51', 'ecotype-2_pdu-Z1.51'])
            self.assertGreaterEqual(sensor_reading.get("last_value"), 120)
            self.assertLessEqual(sensor_reading.get("last_value"), 140)
            self.assertIn(sensor_reading.get("location"), ['ecotype-1', 'ecotype-2'])
            self.assertIn(sensor_reading.get("unit"), ['W'])

            reading_date = arrow.get(sensor_reading.get("time"))
            self.assertLessEqual(abs(reading_date.timestamp - time.time()), 120)


if __name__ == '__main__':
    unittest.main()
