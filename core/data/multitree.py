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


def get_tree(root_node, level=0, use_simplified_children=True):
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
        if "children" in root_node:
            for child in root_node["children"]:
                child_node = get_node_by_id(child)
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
