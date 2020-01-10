import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_multitree_config, _get_sensors_by_collect_method, _get_temperature_sensors_infrastructure, _load_sensors_arrays_data, _load_sensors_data
import arrow
import requests_mock
import time
from tests.utils import mock_data


class TestWebapp(unittest.TestCase):

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
        from core.data.cq_aggregates import cq_multitree_recreate_all
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
    def test_sensors(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            sensors_arrays = get_sensors_arrays_with_children()

            response = self.test_client.get('/sensors.html', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            response_txt = str(response.data)

            for sensors_array_key, sensors_array in sensors_arrays.items():
                sensors_array_name = sensors_array.get("name")
                self.assertIn(flask.url_for('webapp.room_overview', sensors_array_name=sensors_array_name), response_txt)
                for child in sensors_array.get("children"):
                    child_name = child.get("name")
                    self.assertIn(flask.url_for('webapp.room_overview', selected_sensor=child_name), response_txt)

    @mock_data
    def test_index(self):
        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get('/', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_txt = str(response.data)
            self.assertIn("<title> Seduce Dashboard </title>", response_txt)

    @mock_data
    def test_measurements_wattmeters(self):
        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get('/measurements/wattmeters.html', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_txt = str(response.data)
            self.assertIn("""navigator_data_url: "/ui/data/navigation/wattmeter/daily%2Chourly""", response_txt)

    @mock_data
    def test_measurements_thermometers(self):
        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get('/measurements/thermometers.html', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_txt = str(response.data)
            self.assertIn("""navigator_data_url: "/ui/data/navigation/temperature/daily%2Chourly""", response_txt)

    @mock_data
    def test_weighted_tree_consumption(self):
        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get('/weighted_tree_consumption', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_txt = str(response.data)
            self.assertIn("""<script type="text/javascript" src="/static/js/weighted_tree_consumption.js"></script>""", response_txt)

    @mock_data
    def test_rack_temperature_overview(self):
        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            response = self.test_client.get('/rack_temperature_overview.html', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_txt = str(response.data)
            self.assertIn("""function update_temperature_tables() {""", response_txt)

    # @mock_data
    # def test_rack_temperature_errors_clear(self):
    #     with self.__class__.app.app_context(), self.__class__.app.test_request_context():
    #         response = self.test_client.get('/rack_temperature_errors_clear.html', follow_redirects=True)
    #         self.assertEqual(response.status_code, 200)
    #         response_txt = str(response.data)
    #         self.assertIn("""function update_temperature_tables() {""", response_txt)
    #
    # @mock_data
    # def test_rack_temperature_errors_overview(self):
    #     with self.__class__.app.app_context(), self.__class__.app.test_request_context():
    #         response = self.test_client.get('/rack_temperature_overview.html/errors', follow_redirects=True)
    #         self.assertEqual(response.status_code, 200)
    #         response_txt = str(response.data)
    #         self.assertIn("""function update_temperature_tables() {""", response_txt)

    @mock_data
    def test_room_overview(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        sensors_arrays = get_sensors_arrays_with_children()

        all_sensors = _load_sensors_data()
        sensors = [*all_sensors.get("temperature").values()] \
                  + [*all_sensors.get("socomec").values()] \
                  + [*all_sensors.get("flukso").values()] \
                  + [*all_sensors.get("pdus").values()]

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            for sensors_array_key, sensors_array in sensors_arrays.items():
                sensors_array_name = sensors_array.get("name")

                response = self.test_client.get(flask.url_for('webapp.room_overview', sensors_array_name=sensors_array_name), follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                response_txt = str(response.data)

                self.assertIn(f"""<iframe style="border: none; width: 100%;" id="mapIframe" src="/sensors_array.html/{ sensors_array_name }" onload="iframeLoaded()"></iframe>""",
                              response_txt)
                for child in sensors_array.get("children"):
                    child_name = child.get("name")
                    response = self.test_client.get(
                        flask.url_for('webapp.room_overview', selected_sensor=child_name),
                        follow_redirects=True)
                    self.assertEqual(response.status_code, 200)
                    response_txt = str(response.data)

                    self.assertIn(
                        f"""<iframe style="border: none; width: 100%;" id="mapIframe" src="/sensors_array.html/{ sensors_array_name }/{ child_name }" onload="iframeLoaded()"></iframe>""",
                        response_txt)

    @mock_data
    def test_sensors_array(self):
        from core.data.sensors import get_sensors_arrays_with_children
        import flask

        sensors_arrays = get_sensors_arrays_with_children()

        all_sensors = _load_sensors_data()
        sensors = [*all_sensors.get("temperature").values()] \
                  + [*all_sensors.get("socomec").values()] \
                  + [*all_sensors.get("flukso").values()] \
                  + [*all_sensors.get("pdus").values()]

        with self.__class__.app.app_context(), self.__class__.app.test_request_context():
            for sensors_array_key, sensors_array in sensors_arrays.items():
                sensors_array_name = sensors_array.get("name")

                response = self.test_client.get(flask.url_for('webapp.sensors_array', sensors_array_name=sensors_array_name), follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                response_txt = str(response.data)

                self.assertIn(f"""<title>View sensor array linked to {sensors_array_name}</title>""",
                              response_txt)
                for child in sensors_array.get("children"):
                    child_name = child.get("name")
                    response = self.test_client.get(
                        flask.url_for('webapp.sensors_array', sensors_array_name=sensors_array_name, selected_sensor=child_name),
                        follow_redirects=True)
                    self.assertEqual(response.status_code, 200)
                    response_txt = str(response.data)

                    self.assertIn(
                        f"""data-marker="station" data-labelpos="e">{child_name}</li>""",
                        response_txt)


if __name__ == '__main__':
    unittest.main()
