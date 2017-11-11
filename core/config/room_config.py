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
        "name": "wattmeter_b232",
        "info": "wattmeter B232 (socomec)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "location": "B232",
        "coordinates": {
            "x": "93%",
            "y": "85%"
        }
    },
    {
        "name": "wattmeter_servers",
        "info": "wattmeter servers (socomec)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "wattmeter_b232",
        "index": 0
    },
    {
        "name": "wattmeter_cooling",
        "info": "wattmeter cooling (socomec)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "wattmeter_b232",
        "index": 1
    },
    {
        "name": "wattmeter_condensator",
        "info": "wattmeter condensator (socomec)",
        "unit": "W",
        "sensor_type": "wattmeter",
        "parent": "wattmeter_b232",
        "index": 2
    }
]


def get_temperature_sensors_from_csv_files():
    import csv
    from os import listdir
    from os.path import isfile, join
    mypath = "conf/racks"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    result = []
    for file in onlyfiles:
        with open(mypath+"/"+file, 'rU') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            next(spamreader)
            for row in spamreader:
                if "index,Adresse Mac" not in row:
                    result += [row[1].replace(":", "")]
    return result


def get_temperature_sensors_infrastructure():
    import csv
    from os import listdir
    from os.path import isfile, join
    mypath = "conf/racks"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    result = {}
    for file in onlyfiles:
        rack_name = ".".join(file.split(".")[:-1])
        rack_description = {
            "rack": rack_name,
            "sensors": [],
            "positions": {},
            "positions_index": {}
        }
        with open(mypath+"/"+file, 'rU') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            next(spamreader)
            for row in spamreader:
                if "index,Adresse Mac,position" not in row:
                    sensor_name = row[1].replace(":", "")
                    rack_description["sensors"] += [sensor_name ]
                    rack_description["positions"][sensor_name] = int(row[2])
                    rack_description["positions_index"][int(row[2])] = sensor_name
        result[rack_name] = rack_description
    return result

CSV_TEMPERATURE_SENSORS_INITIALIZED = False

SENSOR_ARRAYS_COORDINATES = {
    "z1.1.front": {
        "x": "79.5%",
        "y": "74%"
    },
    "z1.1.back": {
        "x": "79.5%",
        "y": "25%"
    },
    "z1.2.front": {
        "x": "70.75%",
        "y": "74%"
    },
    "z1.2.back": {
        "x": "70.75%",
        "y": "25%"
    },
    "z1.3.front": {
        "x": "62%",
        "y": "74%"
    },
    "z1.3.back": {
        "x": "62%",
        "y": "25%"
    },
    "z1.4.front": {
        "x": "53.25%",
        "y": "74%"
    },
    "z1.4.back": {
        "x": "53.25%",
        "y": "25%"
    },
    "z1.5.front": {
        "x": "44.5%",
        "y": "74%"
    },
    "z1.5.back": {
        "x": "44.5%",
        "y": "25%"
    }
}

if not CSV_TEMPERATURE_SENSORS_INITIALIZED:
    CSV_TEMPERATURE_SENSORS_INITIALIZED = True

    temperature_infrastructure = get_temperature_sensors_infrastructure()
    for sensor_array_name in temperature_infrastructure:
        if sensor_array_name not in SENSOR_ARRAYS_COORDINATES:
            continue
        sensor_array_obj = temperature_infrastructure[sensor_array_name]
        if len(sensor_array_obj["positions_index"]) == 0:
            continue
        coordinate = SENSOR_ARRAYS_COORDINATES[sensor_array_name]
        ROOM_CONFIG += [{
            "name": "temp.%s" % sensor_array_name,
            "info": "An array of temperature sensors watching servers of rack %s" % sensor_array_name,
            "unit": "T",
            "sensor_type": "temperature",
            "location": "B232",
            "coordinates": {
                "x": coordinate["x"],
                "y": coordinate["y"]
            }
        }]

        # Add each sensor of the sensor array
        sorted_sensors_id = [sensor_array_obj["positions_index"][x] for x in sorted(sensor_array_obj["positions_index"].keys())]
        for sensor_id in sorted_sensors_id:
            ROOM_CONFIG += [{
                "name": sensor_id,
                "info": "Temperature sensor %s" % sensor_id,
                "unit": "T",
                "sensor_type": "temperature",
                "parent": "temp.%s" % sensor_array_name,
                "index": 1
            }]

if not CSV_TEMPERATURE_SENSORS_INITIALIZED:
    CSV_TEMPERATURE_SENSORS_INITIALIZED = True

    temperature_infrastructure = get_temperature_sensors_infrastructure()
    for sensor_array_name in temperature_infrastructure:
        if sensor_array_name not in SENSOR_ARRAYS_COORDINATES:
            continue
        sensor_array_obj = temperature_infrastructure[sensor_array_name]
        if len(sensor_array_obj["positions_index"]) == 0:
            continue
        coordinate = SENSOR_ARRAYS_COORDINATES[sensor_array_name]
        ROOM_CONFIG += [{
            "name": "temp.%s" % sensor_array_name,
            "info": "An array of temperature sensors watching servers of rack %s" % sensor_array_name,
            "unit": "T",
            "sensor_type": "temperature",
            "location": "B232",
            "coordinates": {
                "x": coordinate["x"],
                "y": coordinate["y"]
            }
        }]

        # Add each sensor of the sensor array
        sorted_sensors_id = [sensor_array_obj["positions_index"][x] for x in sorted(sensor_array_obj["positions_index"].keys())]
        for sensor_id in sorted_sensors_id:
            ROOM_CONFIG += [{
                "name": sensor_id,
                "info": "Temperature sensor %s" % sensor_id,
                "unit": "T",
                "sensor_type": "temperature",
                "parent": "temp.%s" % sensor_array_name,
                "index": 1
            }]

PDUS_SENSORS_INITIALIZED = False

if not PDUS_SENSORS_INITIALIZED:
    from core.data.pdus import get_pdus, get_outlets, get_outlets_names
    for pdu_id in get_pdus():
        rack_name = pdu_id.split("-")[1].lower()
        coordinate = SENSOR_ARRAYS_COORDINATES[rack_name[:-1]+".back"]

        last_digit = rack_name[-1:]
        y = coordinate["y"]
        if last_digit == "1":
            x = str(float(coordinate["x"].replace("%", "")) - 3.0) + "%"
        else:
            x = str(float(coordinate["x"].replace("%", "")) + 3.0) + "%"

        ROOM_CONFIG += [{
            "name": pdu_id,
            "info": "PDU (%s) of rack %s" % (pdu_id, rack_name),
            "unit": "W",
            "sensor_type": "wattmeter",
            "location": "B232",
            "coordinates": {
                "x": x,
                "y": y
            }
        }]

        outlets = get_outlets(pdu_id)
        for outlet_num in outlets:
            outlet_ressource_name = outlets[outlet_num]
            pdu_name = "%s.%s" % (outlet_ressource_name, pdu_id)
            print(pdu_name)
            ROOM_CONFIG += [{
                "name": outlet_ressource_name,
                "info": "PDU outlet #%s of PDU %s" % (outlet_num, pdu_id),
                "unit": "W",
                "sensor_type": "wattmeter",
                "parent": pdu_id,
                "index": 1
            }]
