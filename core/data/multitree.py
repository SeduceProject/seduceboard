from core.config.multitree_config import MULTITREE_CONFIG


def get_root_nodes():
    return [node for node in MULTITREE_CONFIG if "root" in node and node["root"]]


def get_nodes():
    return [node for node in MULTITREE_CONFIG]


def get_node_by_id(node_id):
    candidates = [node for node in MULTITREE_CONFIG if node["id"] == node_id]
    if len(candidates) > 0:
        return candidates[0]
    return None


def get_tree(root_node, level=0, use_simplified_children=False):
    result = {
        "node": root_node,
        "level": level,
        "children": []
    }

    if use_simplified_children and "simplified_children" in root_node:
        for child in root_node["simplified_children"]:
            child_node = get_node_by_id(child)
            child_tree = get_tree(child_node, level+1, use_simplified_children)
            result["children"] += [child_tree]
    else:
        if root_node is None:
            print("ici")
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
    from core.data.db import db_multitree_last_wattmeter_value
    return db_multitree_last_wattmeter_value(node_id)


def _get_weighted_tree_consumption_data(root_node, level=0, total_consumption=None):

    current_node_consumption = _get_last_node_consumption(root_node)
    if total_consumption is None:
        total_consumption = current_node_consumption

    if total_consumption > 0:
        radius = (100.0 * current_node_consumption) / total_consumption
    else:
        radius = 5
    if radius < 5:
        radius = 5
    if radius > 100:
        radius = 100
    result = {
        "node": root_node,
        "name": root_node["name"],
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
            child_tree = _get_weighted_tree_consumption_data(child_node, level+1, total_consumption=total_consumption)
            result["children"] += [child_tree]

    return result


def get_datacenter_weighted_tree_consumption_data():
    datacenter_root_node = [rn for rn in get_root_nodes() if rn["id"] == "datacenter"]

    if len(datacenter_root_node) > 0:
        return _get_weighted_tree_consumption_data(root_node=datacenter_root_node[0])
    return {}
