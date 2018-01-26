import json
import os


def get_nodes_descriptions(site, cluster):
    cluster_configuration_path = "conf/g5k/%s/%s" % (site, cluster)
    if not os.path.isdir(cluster_configuration_path):
        raise NotImplementedError("%s.%s does not seem to have a proper configuration in conf/g5K" % (site, cluster))

    cluster_config_file_path = "%s/cluster.json" % cluster_configuration_path
    power_config_file_path = "%s/power.json" % cluster_configuration_path
    temperature_config_file_path = "%s/temperature.json" % cluster_configuration_path

    result = {}

    # Create nodes entries and populate the entries with rack name and pdus information
    with open(cluster_config_file_path) as cluster_config_file:
        cluster_config = json.load(cluster_config_file)

    # Add power description
    with open(power_config_file_path) as power_config_file:
        power_config = json.load(power_config_file)

    # Add temperature description
    with open(temperature_config_file_path) as temperature_config_file:
        temperature_config = json.load(temperature_config_file)

    return {
        "cluster": cluster_config,
        "power": power_config,
        "temperature": temperature_config
    }


def extract_nodes_configuration(site, cluster):
    nodes_descriptions = get_nodes_descriptions(site, cluster)
    return nodes_descriptions
