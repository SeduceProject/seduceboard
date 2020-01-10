# from core.config.multitree_config import MULTITREE_CONFIG, MULTITREE_INDEX
from core.data.influx import db_multitree_last_wattmeter_value
from core.data.influx import db_multitree_last_wattmeter_query
from core.data.influx import db_multitree_last_wattmeter_all_in_one_query
import yaml


MULTITREE_CONFIG = None


def get_multitree_config():
    global MULTITREE_CONFIG
    if MULTITREE_CONFIG is None:
        with open("conf/multitree.yaml") as f:
            yaml_as_dict = yaml.load(f)
            MULTITREE_CONFIG = yaml_as_dict
    return MULTITREE_CONFIG


def get_multitree_index():
    return get_multitree_config()


def get_root_nodes():
    return [node for node in get_multitree_config().values() if "root" in node and node["root"]]


def get_nodes():
    return [node for node in get_multitree_config().values()]


def get_node_by_id(node_id):
    multitree_index = get_multitree_index()
    if node_id in multitree_index:
        return multitree_index[node_id]

    candidates = [node for node in get_multitree_config().values() if node["id"] == node_id]
    if len(candidates) > 0:
        return candidates[0]
    return None


def get_tree(root_node, level=0, use_simplified_children=False):
    result = {
        "node": root_node,
        "level": int(level),
        "root_node": level==0,
        "children": []
    }

    if use_simplified_children and "simplified_children" in root_node:
        for child in root_node["simplified_children"]:
            child_node = get_node_by_id(child)
            child_tree = get_tree(child_node, level+1, use_simplified_children)
            result["children"] += [child_tree]
    else:
        if "children" in root_node:
            for child in root_node["children"]:
                child_node = get_node_by_id(child.replace("-", "_"))
                child_tree = get_tree(child_node, level+1, use_simplified_children)
                result["children"] += [child_tree]

    return result


def get_sensors_tree(root_node, level=0, use_simplified_children=True):
    result = []

    if "children" not in root_node or len(root_node["children"]) == 0:
        result += []

    if "target" in root_node:
        result += [root_node["target"]]

    if use_simplified_children and "simplified_children" in root_node:
        result += root_node["simplified_children"]
    else:
        if "children" in root_node:
            for child in root_node["children"]:
                child_node = get_node_by_id(child)
                sensors = get_sensors_tree(child_node, level+1, use_simplified_children)
                result += sensors

    return result


def _get_last_node_consumption(node_id):
    return db_multitree_last_wattmeter_value(node_id)


def _get_last_node_consumption_query(node_id):
    return db_multitree_last_wattmeter_query(node_id)


def _get_consumption_index(root_node, level=0, result=None):
    if result is None:
        result = {
            "queries": [],
            "cq_names": []
        }
    (current_node_consumption_query, cq_name) = _get_last_node_consumption_query(root_node)
    result["queries"] += [current_node_consumption_query]
    result["cq_names"] += [cq_name]

    if "children" in root_node:
        for child in root_node["children"]:
            child_node = get_node_by_id(child.replace("-", "_"))
            _get_consumption_index(child_node, level+1, result=result)

    if level == 0:
        return db_multitree_last_wattmeter_all_in_one_query(result)

    return None


def _get_weighted_tree_consumption_data(root_node, level=0, total_consumption=None, consumption_index=None):
    cq_root_node_1m = "cq_%s_1m" % root_node["id"]

    if consumption_index is None:
        current_node_consumption = _get_last_node_consumption(root_node)
    else:
        if cq_root_node_1m in consumption_index:
            current_node_consumption = consumption_index[cq_root_node_1m]
        else:
            current_node_consumption = 0

    if total_consumption is None:
        total_consumption = current_node_consumption

    current_node_consumption_percentage = (1.0 * current_node_consumption) / total_consumption
    if current_node_consumption_percentage > 1.0:
        current_node_consumption_percentage = 1.0
    elif current_node_consumption_percentage < 0.0:
        current_node_consumption_percentage = 0.0

    if current_node_consumption_percentage > 0.0:
        import math
        factor = 0.97 * math.sin(current_node_consumption_percentage * (math.pi / 2.0)) + 0.03
        radius = factor * 100.0
    else:
        radius = 1.0

    root_node_name = root_node.get("name", root_node.get("id"))

    result = {
        "node": root_node,
        "name": root_node_name,
        "id": root_node["id"],
        "level": level,
        "consumption": current_node_consumption,
        "total_consumption": total_consumption,
        "h": radius,
        "children": []
    }

    if "children" in root_node:
        for child in root_node["children"]:
            child_node = get_node_by_id(child.replace("-", "_"))
            child_tree = _get_weighted_tree_consumption_data(child_node, level+1, total_consumption=total_consumption, consumption_index=consumption_index)
            result["children"] += [child_tree]

    return result


def get_datacenter_weighted_tree_consumption_data():
    datacenter_root_node = get_node_by_id("datacenter")

    if datacenter_root_node:
        consumption_index = _get_consumption_index(datacenter_root_node)
        return _get_weighted_tree_consumption_data(root_node=datacenter_root_node, consumption_index=consumption_index)
    return {}
