import unittest
import time
import json
import numpy
from tests.utils import _load_sensors_data
from tests.utils import mock_data


class TestWebappApi(unittest.TestCase):

    @classmethod
    @mock_data
    def setUpClass(cls):
        # Init InfluxDB
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client
        from core.config.crawlers_config import get_sensors_by_collect_method
        from core.config.room_config import get_temperature_sensors_infrastructure

        db_name = get_influxdb_parameters().get("database")
        db_client = get_influxdb_client()

        if db_name == "pidiou":
            raise Exception("Abort: modifying 'pidiou' database")

        db_client.drop_database(db_name)
        db_client.create_database(db_name)

        # Create few queries in charge of computing aggregated data
        from core.data.cq_aggregates import cq_multitree_recreate_all, cqs_recompute_data
        cq_multitree_recreate_all(recreate_all=True)

        # Insert some data
        data = []
        start_timestamp = int(time.time() - 12 * 3600)

        all_sensors = _load_sensors_data()
        sensors = [*all_sensors.get("temperature").values()]\
                  + [*all_sensors.get("socomec").values()]\
                  + [*all_sensors.get("flukso").values()]\
                  + [*all_sensors.get("pdus").values()]

        count = 0
        for timestamp in range(start_timestamp, start_timestamp + 12 * 3600, 15):
            count += 1
            for sensor in sensors:

                sensor_type = sensor.get("sensor_type")
                unit = sensor.get("unit")
                sensor_name = sensor.get("name")

                if sensor_type == "temperature":
                    value = 10 + (count % 20)
                else:
                    value = 100 + (count % 30)

                data += [{
                    "measurement": "sensors",
                    "fields": {
                        "value": value
                    },
                    "time": timestamp,
                    "tags": {
                        "location": "room exterior",
                        "sensor": f"{sensor_name}",
                        "unit": unit,
                        "sensor_type": f"{sensor_type}"
                    }
                }]
        db_client.write_points(data, time_precision="s")

        # Update data of the continuous queries
        cq_multitree_recreate_all(recreate_all=False)
        cqs_recompute_data()
        db_client.close()

        # Launch web-app
        from core.misc import ensure_admin_user_exists
        import logging
        from bin.app import app, db, login_manager

        login_manager._login_disabled = True

        logging.basicConfig(level=logging.DEBUG)
        # Create DB
        print("Creating database")
        db.create_all()

        cls.app = app
        cls.test_client = app.test_client()


    @classmethod
    @mock_data
    def tearDownClass(cl):
        from core.data.influx import get_influxdb_parameters
        from core.data.influx import get_influxdb_client

        db_name = get_influxdb_parameters().get("database")
        db_client = get_influxdb_client()

        if db_name == "pidiou":
            raise Exception("Abort: modifying 'pidiou' database")

        db_client.drop_database(db_name)
        db_client.close()

    @mock_data
    def test_validate(self):
        pass

    @mock_data
    def test_sensor_data(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            sensors_arrays = get_sensors_arrays_with_children()
            for sensors_array_key, sensors_array in sensors_arrays.items():
                for child in sensors_array.get("children"):
                    child_name = child.get("name")
                    response = self.test_client.get(flask.url_for('webapp_api.sensor_data', sensor_name=child_name), follow_redirects=True)
                    self.assertEqual(response.status_code, 200)

                    json_dict = json.loads(response.data)
                    self.assertEqual(len(json_dict.get("values")), 241)

                    if child.get("sensor_type") == "temperature":
                        self.assertGreaterEqual(numpy.mean(json_dict.get("values")), 10)
                        self.assertLessEqual(numpy.mean(json_dict.get("values")), 30)
                    else:
                        self.assertGreaterEqual(numpy.mean(json_dict.get("values")), 100)
                        self.assertLessEqual(numpy.mean(json_dict.get("values")), 130)

    @mock_data
    def test_sensors(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.sensors'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_dict = json.loads(response.data)

            sensors_arrays = get_sensors_arrays_with_children()
            for sensors_array_key, sensors_array in sensors_arrays.items():
                for child in sensors_array.get("children"):
                    child_name = child.get("name")

                    self.assertIn(child_name, json_dict.get("sensors"))

    @mock_data
    def test_sensor_types(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.sensor_types'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_dict = json.loads(response.data)

            sensors_arrays = get_sensors_arrays_with_children()
            for sensors_array_key, sensors_array in sensors_arrays.items():
                for child in sensors_array.get("children"):
                    child_sensor_type = child.get("sensor_type")

                    self.assertIn(child_sensor_type, json_dict.get("sensor_types"))

    @mock_data
    def test_multitree_root_nodes(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.multitree_root_nodes'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            for dictionnary in json_response:
                self.assertDictEqual(dictionnary, {'children': ['cluster'], 'id': 'datacenter', 'name': 'Datacenter', 'root': True})

    @mock_data
    def test_multitree_tree_query(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.multitree_tree_query', node_id="ecotype_1"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertDictEqual({'children': [{'children': [], 'level': 1,
                                                'node': {'id': 'ecotype_1_Z1_51', 'name': 'ecotype-1-Z1.51',
                                                         'target': 'ecotype-1_pdu-Z1.51'}, 'root_node': False},
                                               {'children': [], 'level': 1,
                                                'node': {'id': 'ecotype_1_Z1_50', 'name': 'ecotype-1-Z1.50',
                                                         'target': 'ecotype-1_pdu-Z1.50'}, 'root_node': False}],
                                  'level': 0,
                                  'node': {'children': ['ecotype_1_Z1_51', 'ecotype_1_Z1_50'], 'id': 'ecotype_1',
                                           'name': 'ecotype-1'}, 'root_node': True}, json_response)

    @mock_data
    def test_multitree_sensors_query(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.multitree_sensors_query', node_id="ecotype_1"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            for sensor in ['ecotype-1_pdu-Z1.51', 'ecotype-1_pdu-Z1.50']:
                self.assertIn(sensor, json_response)

    @mock_data
    def test_multitree_sensors_data_query(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.multitree_sensors_data_query', node_id="ecotype_1"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            for sensor in ['ecotype-1_pdu-Z1.51', 'ecotype-1_pdu-Z1.50']:
                self.assertIn(sensor, json_response)

    @mock_data
    def test_locations(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.locations'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)
            self.assertDictEqual({'locations': ['room exterior']}, json_response)

    @mock_data
    def test_aggregated_sensor_data(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.aggregated_sensor_data', sensor_name='ecotype-1_pdu-Z1.50', how="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("means")), 13)

    @mock_data
    def test_aggregated_rack_side_temperatures(self):
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.aggregated_rack_side_temperatures', side='front', how="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("means")), 13)

    @mock_data
    def test_dump_all_aggregated_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.dump_all_aggregated_data', group_by="1h"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            sensors_arrays = get_sensors_arrays_with_children()
            for sensors_array_key, sensors_array in sensors_arrays.items():
                for child in sensors_array.get("children"):
                    child_name = child.get("name")

                    self.assertIn(child_name, json_response.get("sensors_data"))

                    child_means = json_response.get("sensors_data").get(child_name).get("means")
                    self.assertEqual(len(child_means), 25)
                    self.assertEqual(len([v for v in child_means if v is not None]), 13)

    @mock_data
    def test_aggregated_multitree_sensor_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.aggregated_multitree_sensor_data', sensor_name="ecotype_1", how="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("means")), 13)

    @mock_data
    def test_datainfo(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.datainfo', how="daily"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("range").get("means")), 5)
            self.assertGreaterEqual(len(json_response.get("range").get("means")), 3)

    @mock_data
    def test_pue_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.pue_data', how="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("means")), 13)

            self.assertAlmostEqual(numpy.mean(json_response.get("means")), 1.0)

    @mock_data
    def test_external_temperature_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.external_temperature_data', how="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("means")), 13)

            self.assertGreaterEqual(numpy.mean(json_response.get("means")[0:-1]), 19.0)
            self.assertLessEqual(numpy.mean(json_response.get("means")[0:-1]), 20.0)

    @mock_data
    def test_get_navigation_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.get_navigation_data', sensor_type="wattmeter", aggregation_preferences="hourly"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertLessEqual(len(json_response.get("range").get("means")), 14)
            self.assertGreaterEqual(len(json_response.get("range").get("means")), 13)

            self.assertGreaterEqual(numpy.mean(json_response.get("range").get("means")[0:-1]), 114.0)
            self.assertLessEqual(numpy.mean(json_response.get("range").get("means")[0:-1]), 115.0)

    # @mock_data
    # def test_queries(self):
    #     pass

    @mock_data
    def test_last_sensors_updates(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.last_sensors_updates'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            sensors_arrays = get_sensors_arrays_with_children()
            for sensors_array_key, sensors_array in sensors_arrays.items():
                for child in sensors_array.get("children"):
                    child_name = child.get("name")

                    [child_last_reading] = [reading for reading in json_response if reading.get("sensor") == child_name]

                    if child.get("sensor_type") == "temperature":
                        self.assertGreaterEqual(child_last_reading.get("last_value"), 10)
                        self.assertLessEqual(child_last_reading.get("last_value"), 30)
                    else:
                        self.assertGreaterEqual(child_last_reading.get("last_value"), 100)
                        self.assertLessEqual(child_last_reading.get("last_value"), 130)

    @mock_data
    def test_weighted_tree_consumption_data(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.weighted_tree_consumption_data'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertGreaterEqual(json_response.get("total_consumption"), 4 * 100)
            self.assertLessEqual(json_response.get("total_consumption"), 4 * 130)

    @mock_data
    def test_rack_temperature_sensors(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.rack_temperature_sensors'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            self.assertDictEqual(json_response, {
                'room.top': {'positions': {'28b8fb2909000003': 1}, 'positions_index': {'1': '28b8fb2909000003'},
                             'rack': 'room.top', 'sensors': ['28b8fb2909000003']},
                'z1.5.back': {'positions': {'3b96f85809fc2c27': 30, '3ba6b75809fc0c6f': 32},
                              'positions_index': {'30': '3b96f85809fc2c27', '32': '3ba6b75809fc0c6f'},
                              'rack': 'z1.5.back', 'sensors': ['3b96f85809fc2c27', '3ba6b75809fc0c6f']},
                'z1.5.front': {'positions': {'3bbefa5809fc2cb3': 32, '3bd10a5909fc6c3b': 30},
                               'positions_index': {'30': '3bd10a5909fc6c3b', '32': '3bbefa5809fc2cb3'},
                               'rack': 'z1.5.front', 'sensors': ['3bd10a5909fc6c3b', '3bbefa5809fc2cb3']}})

    @mock_data
    def test_rack_temperature_sensors_last_values(self):
        import flask
        from core.data.sensors import get_sensors_arrays_with_children

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get(flask.url_for('webapp_api.rack_temperature_sensors_last_values'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            json_response = json.loads(response.data)

            for sensor_array in ["room.top", "z1.5.back", "z1.5.front"]:
                last_temperatures = json_response.get(sensor_array).get("last_temperatures")

                for temperature_reading in last_temperatures:
                    self.assertGreaterEqual(temperature_reading.get("last_value"), 10)
                    self.assertLessEqual(temperature_reading.get("last_value"), 30)

    # @mock_data
    # def test_rack_temperature_sensors_errors_last_values(self):
    #     pass
    #
    # @mock_data
    # def test_rack_temperature_errors_incr(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
