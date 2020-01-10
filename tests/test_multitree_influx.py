import unittest
from unittest import mock
from tests.utils import _get_influxdb_parameters, _get_multitree_config, _get_sensors_by_collect_method, FakeModbusAgent, _get_temperature_sensors_infrastructure, _get_configuration_path
import arrow
import requests_mock
import time
from tests.utils import mock_data


class TestMultitreeInflux(unittest.TestCase):

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

        # Create few queries in charge of computing aggregated data
        from core.data.cq_aggregates import cq_multitree_recreate_all
        cq_multitree_recreate_all(recreate_all=True)

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
                            "unit": "celsius",
                            "sensor_type": f"{sensor_type}"
                        }
                    }]
            db_client.write_points(data, time_precision="s", batch_size=8 * 3600)

        # Update data of the continuous queries
        cq_multitree_recreate_all(recreate_all=False)

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

    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_aggregated_multitree_sensor_data(self, fa):
    #     from core.data.influx import db_aggregated_multitree_sensor_data
    #
    #     aggregated_multitree_sensor_data = db_aggregated_multitree_sensor_data("wattmeter1",
    #                                                                            start_date=f"{self.start_timestamp}s",
    #                                                                            end_date=f"{self.start_timestamp + 3 * 3600}s")
    #     print(aggregated_multitree_sensor_data)

    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_wattmeters_data(self, fa):
    #     from core.data.influx import db_wattmeters_data
    #
    #     wattmeters_data = db_wattmeters_data()
    #     pass

    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_last_sensors_updates(self, fa):
    #     from core.data.influx import db_last_sensors_updates
    #
    #     last_sensors_updates = db_last_sensors_updates()
    #
    #     print(last_sensors_updates)

    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_last_temperature_values(self, fa):
    #     from core.data.influx import db_last_temperature_values
    #
    #     last_temperature_values = db_last_temperature_values()
    #     print(last_temperature_values)

    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_last_temperature_mean(self, fa):
    #     pass
    #
    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_multitree_last_wattmeter_value(self, fa):
    #     pass
    #
    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_multitree_last_wattmeter_query(self, fa):
    #     pass
    #
    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_multitree_last_wattmeter_all_in_one_query(self, fa):
    #     pass
    #
    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_db_get_running_queries(self, fa):
    #     pass
    #
    # @mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters)
    # def test_influx_run_query(self, fa):
    #     pass

    @mock_data
    def test_get_root_nodes(self):
        from core.data.multitree import get_root_nodes
        root_nodes = get_root_nodes()

        self.assertEqual(len(root_nodes), 1)

        self.assertEqual(root_nodes[0].get("id"), "datacenter")
        self.assertListEqual(root_nodes[0].get("children"), ["cluster"])
        self.assertEqual(root_nodes[0].get("root", False), True)

    @mock_data
    def test_get_nodes(self):
        from core.data.multitree import get_nodes
        import yaml

        nodes = get_nodes()

        self.assertEqual(len(nodes), 11)

    @mock_data
    def test_get_node_by_id(self):
        from core.data.multitree import get_node_by_id

        node = get_node_by_id("ecotype_1")

        self.assertEqual(node.get("id"), "ecotype_1")
        self.assertEqual(node.get("name"), "ecotype-1")
        self.assertEqual(node.get("children"), ["ecotype_1_Z1_51", "ecotype_1_Z1_50"])

    @mock_data
    def test_get_tree(self):
        from core.data.multitree import get_root_nodes, get_tree

        root_nodes = get_root_nodes()
        tree = get_tree(root_nodes[0])

        self.assertIsNotNone(tree)

        self.assertEqual(tree["level"], 0)
        self.assertEqual(tree["node"], {'id': 'datacenter', 'name': 'Datacenter', 'children': ['cluster'], 'root': True})
        self.assertEqual(len(tree["children"]), 1)

        self.assertListEqual([child["node"]["id"] for child in tree["children"]], ["cluster"])

    @mock_data
    def test_get_sensors_tree(self):
        from core.data.multitree import get_root_nodes, get_sensors_tree

        root_nodes = get_root_nodes()
        sensors_tree = get_sensors_tree(root_nodes[0])

        self.assertIsNotNone(sensors_tree)
        self.assertListEqual(sensors_tree, ['cluster_hardware'])

    @mock_data
    def test__get_last_node_consumption(self):
        from core.data.multitree import _get_last_node_consumption

        last_node_consumption = _get_last_node_consumption({"id": "servers"})

        self.assertIsNotNone(last_node_consumption)

        consumption_difference = abs(last_node_consumption - 345570)
        self.assertLessEqual(consumption_difference, 100)

    @mock_data
    def test__get_last_node_consumption_query(self):
        from core.data.multitree import _get_last_node_consumption_query

        last_node_consumption_query = _get_last_node_consumption_query({"id": "servers"})
        self.assertEqual(last_node_consumption_query[0], "SELECT last(*) from cq_servers_1m where time > now() - 1d")
        self.assertEqual(last_node_consumption_query[1], "cq_servers_1m")

    @mock_data
    def test__get_consumption_index(self):
        from core.data.multitree import _get_consumption_index

        consumption_index = _get_consumption_index({"id": "servers"})

        self.assertIsNotNone(consumption_index)
        # self.assertEqual(consumption_index, 0)

    @mock_data
    def test__get_weighted_tree_consumption_data(self):
        from core.data.multitree import _get_weighted_tree_consumption_data

        weighted_tree_consumption_data = _get_weighted_tree_consumption_data({"id": "servers"})

        self.assertIsNotNone(weighted_tree_consumption_data)

    @mock_data
    def test_get_datacenter_weighted_tree_consumption_data(self):
        from core.data.multitree import get_datacenter_weighted_tree_consumption_data

        datacenter_weighted_tree_consumption_data = get_datacenter_weighted_tree_consumption_data()

        leaf_consumptions = [pdu_cons.get("consumption")
                             for cluster_cons in datacenter_weighted_tree_consumption_data.get("children")
                             for hardware_cluster_cons in cluster_cons.get("children")
                             for servers_cons in hardware_cluster_cons.get("children")
                             for ecotype_1_cons in servers_cons.get("children")
                             for pdu_cons in ecotype_1_cons.get("children")]

        self.assertIsNotNone(datacenter_weighted_tree_consumption_data)
        self.assertAlmostEqual(sum(leaf_consumptions), datacenter_weighted_tree_consumption_data["consumption"])


if __name__ == '__main__':
    unittest.main()
