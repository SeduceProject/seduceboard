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
        "target": "watt_cooler_232_1"
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


