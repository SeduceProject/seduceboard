import json

JSON_CONFIGURATION_PATH = "conf/config-nantes.json"


def get_pdus():
    with open(JSON_CONFIGURATION_PATH) as data_file:
        json_data = json.load(data_file)
        return [x for x in list(json_data) if "power" in json_data[x]]
    return []


def get_outlets_names(pdu_id):
    with open(JSON_CONFIGURATION_PATH) as data_file:
        json_data = json.load(data_file)
        if pdu_id in json_data and "power" in json_data[pdu_id] and "sensors" in json_data[pdu_id]["power"]:
            return json_data[pdu_id]["power"]["sensors"].values()
    return []


def get_outlets(pdu_id):
    with open(JSON_CONFIGURATION_PATH) as data_file:
        json_data = json.load(data_file)
        if pdu_id in json_data and "power" in json_data[pdu_id] and "sensors" in json_data[pdu_id]["power"]:
            return json_data[pdu_id]["power"]["sensors"]
    return []


def get_connection_info_for_pdu(pdu_id):
    with open(JSON_CONFIGURATION_PATH) as data_file:
        json_data = json.load(data_file)
        if pdu_id in json_data and "power" in json_data[pdu_id]:
            pdu_info = json_data[pdu_id]
            return {
                "pdu_id": pdu_id,
                "pdu_ip": pdu_info["ip"],
                "pdu_oid": pdu_info["power"]["oid"],
                "pdu_nb_values": pdu_info["power"]["nb_values"],
                "pdu_snmp_length": pdu_info["power"]["snmp_length"]
            }
    return {}
