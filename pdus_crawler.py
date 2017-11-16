from __future__ import absolute_import, unicode_literals

import threading
import traceback

from influxdb import InfluxDBClient
from pysnmp.hlapi.asyncore import *
import time

#DB_HOST = "192.168.1.8"
DB_HOST = "localhost"
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
OUTPUT_FILE = 'temperatures.json'

DEBUG = True
LAST_TIMESTAMP_INSERTED = {}


def process_one_outlet(outlet_num, outlet_name, varBinds, cbCtx):
    db_client = InfluxDBClient(DB_HOST, 8086, DB_USER, DB_PASSWORD, DB_NAME)

    # outlet_name = cbCtx["outlet_id"]
    outlet_oid = cbCtx["pdu_oid"]+"."+outlet_num

    matching_outlet_value_binding = [x for x in varBinds if str(x[0][0]) == outlet_oid]

    if len(matching_outlet_value_binding) > 0:
        value_binding = matching_outlet_value_binding[0]
        outlet_unit = "W"
        outlet_value = (1.0 * value_binding[0][1])
        outlet_location = outlet_name
        outlet_sensor_name = outlet_name+"_"+cbCtx["pdu_id"]
        outlet_sensor_type = "wattmeter"

        try:
            float(outlet_value)
        except:
            print("something wrong happened here :-(")

        data = [{
            "measurement": "sensors",
            "fields": {
                "value": float(outlet_value)
            },
            "tags": {
                "location": outlet_location,
                "sensor": outlet_sensor_name,
                "unit": outlet_unit,
                "sensor_type": outlet_sensor_type
            }
        }]

        try:
            failure = not db_client.write_points(data, time_precision="s")
        except :
            traceback.print_exc()
            failure = True

        db_client.close()

        insertion_count = 0
        if failure:
            print("[%s] failed to insert rows in the database" % (outlet_name))
            return {"status": "failure", "reason": "could not write in the DB"}
        else:
            insertion_count += 1

        print("[%s] %s rows have been inserted in the database" % (outlet_name, insertion_count))
        return {"status": "success", "update_count": insertion_count}

    else:
        print("[%s] PDU returned no matching value for OID='%s' (%s)" % (outlet_name, outlet_oid, cbCtx))
        return {"status": "failure", "reason": "PDU returned no matching value for OID='%s' (%s)" % (outlet_oid, cbCtx)}


def process_outlets_readings(snmpEngine, sendRequestHandle, errorIndication, errorStatus, errorIndex, varBinds, cbCtx):
    from core.data.pdus import get_outlets

    pdu_id = cbCtx["pdu_id"]

    for (outlet_num, outlet_name) in get_outlets(pdu_id).iteritems():
        process_one_outlet(outlet_num, outlet_name, varBinds, cbCtx)

    return False


def read_outlets_of_given_pdu(pdu_id):
    from core.data.pdus import get_connection_info_for_pdu
    snmpEngine = SnmpEngine()

    connection_info = get_connection_info_for_pdu(pdu_id)
    pdu_ip = connection_info["pdu_ip"]
    pdu_oid = connection_info["pdu_oid"]
    pdu_snmp_length = connection_info["pdu_snmp_length"]

    bulkCmd(snmpEngine,
            CommunityData('public'),
            UdpTransportTarget((pdu_ip, 161)),
            ContextData(),
            0, pdu_snmp_length,
            ObjectType(ObjectIdentity(pdu_oid)),
            lookupMib=False,
            lexicographicMode=False,
            cbFun=process_outlets_readings,
            cbCtx=connection_info)

    snmpEngine.transportDispatcher.runDispatcher()
    return False


NO_PAUSE = -1


def set_interval(f, args, interval_secs):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False

        def run(self):
            while not self.stop_execution:
                try:
                    self.f(self.args)
                except:
                    traceback.print_exc()
                    print("Something bad happened here :-(")
                    pass
                if interval_secs != NO_PAUSE:
                    time.sleep(self.interval)

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval_secs)
    t.start()
    return t


if __name__ == "__main__":
    from core.data.pdus import get_pdus

    print("I will start crawling PDUs")
    last_pdu_reader = None
    for pdu_id in get_pdus():
        # read_outlets_of_given_pdu(pdu_id)
        pdu_reader = set_interval(read_outlets_of_given_pdu, (pdu_id), NO_PAUSE)

        # Add a pause to prevent PDU to get all requests at the same time
        time.sleep(2)

    if last_pdu_reader is not None:
        last_pdu_reader.join()
