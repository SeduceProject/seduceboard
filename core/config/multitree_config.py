MULTITREE_CONFIG = [
    {
        "id": "datacenter",
        "name": "Datacenter",
        "children": ["cluster", "room"],
        "root": True
    },
    {
        "id": "cluster",
        "name": "Cluster",
        "children": ["cooling_cluster", "hardware_cluster"]
    },
    {
        "id": "room",
        "name": "Room",
        "children": ["cooling_room"]
    },
    {
        "id": "cooling_cluster",
        "name": "Cooling cluster",
        "children": ["cluster_cooling", "cluster_condensator"]
    },
    {
        "id": "cooling_room",
        "name": "Cooling Room",
        "children": ["room_cooling_fan", "room_cooling_roof_unit"]
    },
    {
        "id": "hardware_cluster",
        "name": "Hardware cluster",
        "simplified_children": ["cluster_hardware"],
        "children": ["network_switches", "servers"]
    },
    {
        "id": "network_switches",
        "name": "Network switches",
        "children": []
    },
    {
        "id": "servers",
        "name": "Servers",
        "children": []
    },
    # B232 sensors
    {
        "id": "room_cooling_roof_unit",
        "name": "Roof cooling generator unit",
        "target": "watt_cooler_b232_1"
    },
    {
        "id": "room_cooling_fan",
        "name": "Cooling fan",
        "target": "watt_cooler_ext_1"
    },
    # Bouillonnantes.g5k sensors
    {
        "id": "cluster_hardware",
        "name": "Hardware",
        "target": "wattmeter_servers"
    },
    {
        "id": "cluster_cooling",
        "name": "Cooling",
        "target": "wattmeter_cooling"
    },
    {
        "id": "cluster_condensator",
        "name": "Condensator",
        "target": "wattmeter_condensator"
    },
    # {
    #     "id": "cluster_hardware",
    #     "name": "Hardware",
    #     "target": "socomec_servers"
    # },
    # {
    #     "id": "cluster_cooling",
    #     "name": "Cooling",
    #     "target": "socomec_cooling"
    # },
    # {
    #     "id": "cluster_condensator",
    #     "name": "Condensator",
    #     "target": "socomec_condensator"
    # }
]

MULTITREE_INDEX = {

}

PDUS_SENSORS_INITIALIZED = False

if not PDUS_SENSORS_INITIALIZED:
    from core.data.pdus import get_pdus, get_outlets, get_outlets_names

    hardware_resources = {}

    for pdu_id in get_pdus():
        rack_name = pdu_id.split("-")[1].lower()

        last_digit = rack_name[-1:]

        outlets = get_outlets(pdu_id)
        for outlet_num in sorted(outlets, key=lambda x: int(x)):
            hardware_resource_name = outlets[outlet_num]
            outlet_ressource_name = outlets[outlet_num]+"-"+rack_name.upper()
            outlet_serie_name = outlets[outlet_num] + "_pdu-" + rack_name.upper()
            pdu_name = "%s.%s" % (outlet_ressource_name, pdu_id)

            if hardware_resource_name not in hardware_resources:
                hardware_resources[hardware_resource_name] = {}

            hardware_resources[hardware_resource_name][outlet_ressource_name] = outlet_serie_name

    for hardware_resource_name in hardware_resources:
        for outlet_ressource_name in hardware_resources[hardware_resource_name]:
            outlet_node = {
                "id": outlet_ressource_name.replace("-", "_").replace(".", "_"),
                "name": outlet_ressource_name,
                "target": hardware_resources[hardware_resource_name][outlet_ressource_name]
            }
            MULTITREE_CONFIG += [outlet_node]

        ressource_node = {
            "id": hardware_resource_name.replace("-", "_"),
            "name": hardware_resource_name,
            "children": [x.replace("-", "_").replace(".", "_") for x in hardware_resources[hardware_resource_name].keys()]
        }
        MULTITREE_CONFIG += [ressource_node]

        servers_node = [x for x in MULTITREE_CONFIG if x["id"] == "servers"][0]
        network_switches_node = [x for x in MULTITREE_CONFIG if x["id"] == "network_switches"][0]

        if hardware_resource_name != "electrical_mgmt_board":
            if "switch" in hardware_resource_name:
                network_switches_node["children"] += [hardware_resource_name]
            else:
                servers_node["children"] += [hardware_resource_name]

    PDUS_SENSORS_INITIALIZED = True

    # Create an Index of nodes that are members of the multitree
    for node in MULTITREE_CONFIG:
        MULTITREE_INDEX[node["id"]] = node
