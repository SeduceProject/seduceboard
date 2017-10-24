ROOM_CONFIG = [
    {
        "name": "watt_cooler_ext",
        "info": "Flukso exterior",
        "unit": "W",
        "sensor_type": "wattmeter",
        "location": "cooler_electrical_board",
        "coordinates": {
            "x": "50%",
            "y": "-5%"
        }
    },
    {
        "name": "watt_cooler_ext_1",
        "info": "Flukso exterior (clamp1)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "watt_cooler_ext",
        "index": 0
    },
    {
        "name": "watt_cooler_ext_2",
        "info": "Flukso exterior (clamp2)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "watt_cooler_ext",
        "index": 1
    },
    {
        "name": "watt_cooler_b232",
        "info": "Flukso B232",
        "unit": "W",
        "sensor_type": "wattmeter",
        "location": "B232",
        "coordinates": {
            "x": "93%",
            "y": "45%"
        }
    },
    {
        "name": "watt_cooler_b232_1",
        "info": "Flukso B232 (clamp1)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "watt_cooler_b232",
        "index": 0
    },
    {
        "name": "watt_cooler_b232_2",
        "info": "Flukso B232 (clamp2) - orange",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "watt_cooler_b232",
        "index": 1
    },
    {
        "name": "watt_cooler_b232_3",
        "info": "Flukso B232 (clamp3) - blue",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "watt_cooler_b232",
        "index": 2
    },
    {
        "name": "socomec_b232",
        "info": "Socomec B232",
        "unit": "W",
        "sensor_type": "socomec",
        "location": "B232",
        "coordinates": {
            "x": "93%",
            "y": "85%"
        }
    },
    {
        "name": "socomec_servers",
        "info": "Socomec servers",
        "unit": "W",
        "sensor_type": "socomec",
        "parent": "socomec_b232",
        "index": 0
    },
    {
        "name": "socomec_cooling",
        "info": "Socomec cooling",
        "unit": "W",
        "sensor_type": "socomec",
        "parent": "socomec_b232",
        "index": 1
    },
    {
        "name": "socomec_condensator",
        "info": "Socomec condensator",
        "unit": "W",
        "sensor_type": "socomec",
        "parent": "socomec_b232",
        "index": 2
    },
    # External temperature sensor
    {
        "name": "moteino_1",
        "info": "An array of temperature sensors connected to Moteino #1",
        "unit": "T",
        "sensor_type": "temperature",
        "location": "B232",
        "coordinates": {
            "x": "62%",
            "y": "8%"
        }
    },
    {
        "name": "28:ff:7e:a3:00:17:05:1b",
        "info": "Temperature sensor %s" % ("28:ff:7e:a3:00:17:05:1b"),
        "unit": "T",
        "sensor_type": "temperature",
        "parent": "moteino_1",
        "index": 0
    },
    {
        "name": "28:ff:04:a8:00:17:03:82",
        "info": "Temperature sensor %s" % ("28:ff:04:a8:00:17:03:82"),
        "unit": "T",
        "sensor_type": "temperature",
        "parent": "moteino_1",
        "index": 1
    },
    {
        "name": "28:ff:03:cb:00:17:04:48",
        "info": "Temperature sensor %s" % ("28:ff:03:cb:00:17:04:48"),
        "unit": "T",
        "sensor_type": "temperature",
        "parent": "moteino_1",
        "index": 2
    },
    {
        "name": "28:ff:12:e2:00:17:04:1a",
        "info": "Temperature sensor %s" % ("28:ff:12:e2:00:17:04:1a"),
        "unit": "T",
        "sensor_type": "temperature",
        "parent": "moteino_1",
        "index": 3
    },
    {
        "name": "28:ff:5c:e3:00:17:04:de",
        "info": "Temperature sensor %s" % ("28:ff:5c:e3:00:17:04:de"),
        "unit": "T",
        "sensor_type": "temperature",
        "parent": "moteino_1",
        "index": 4
    }
]

candidates = filter(lambda x: x["name"] == "fake_temparature_sensors_array", ROOM_CONFIG)
if len(candidates) == 0:
    import random

    def generate_random_mac_address():
        return [0x00, 0x16, 0x3e, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xff)]

    def format_mac_address(mac):
        return ':'.join(map(lambda x: "%02x" % x, mac))

    coordinates = [
        {
            "x": "44.5%",
            "y": "25%"
        },
        {
            "x": "44.5%",
            "y": "74%"
        },
        {
            "x": "53.25%",
            "y": "25%"
        },
        {
            "x": "53.25%",
            "y": "74%"
        },
        {
            "x": "62%",
            "y": "25%"
        },
        {
            "x": "62%",
            "y": "74%"
        },
        {
            "x": "70.75%",
            "y": "25%"
        },
        {
            "x": "70.75%",
            "y": "74%"
        },
        {
            "x": "79.5%",
            "y": "25%"
        },
        {
            "x": "79.5%",
            "y": "74%"
        }
    ]

    array_number = 0
    for coordinate in coordinates:
        sensor_array_name = "tmp_sensors_array_%i" % array_number
        fake_temperature_sensors_array = {
            "name": sensor_array_name,
            "info": "A fake array of temperature sensors (%i)" % array_number,
            "unit": "T",
            "sensor_type": "temperature",
            "location": "B232",
            "coordinates": coordinate
        }
        mac_index_tuple2s = map(lambda x: (x, format_mac_address(generate_random_mac_address())), range(0, 48))
        fake_temp_sensors = map(lambda (index, mac): {
            "name": mac,
            "info": "Temperature sensor %s" % (mac),
            "unit": "T",
            "sensor_type": "temperature",
            "parent": sensor_array_name,
            "index": index
        }, mac_index_tuple2s)
        ROOM_CONFIG += [fake_temperature_sensors_array]
        ROOM_CONFIG += fake_temp_sensors

        array_number += 1
