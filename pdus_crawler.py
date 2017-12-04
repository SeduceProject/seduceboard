from __future__ import absolute_import, unicode_literals

import threading
import traceback
import sys
import re

from influxdb import InfluxDBClient
from pysnmp.hlapi.asyncore import *
import time
import threading
from core.data.pdus import get_outlets
from core.data.pdus import get_connection_info_for_pdu
from core.data.pdus import get_outlets
from threading import Timer

from docopt import docopt
from core.data.pdus import get_pdus
from core.data.db import *

NO_PAUSE = -1

DEBUG = True
LAST_TIMESTAMP_INSERTED = {}

RECORDS = []

influx_lock = threading.Lock()


# Following in an example of a snmpv2 request:
# snmpget -v2c -c public 10.44.193.181 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.2 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.3 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.4 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.5 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.6 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.7 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.8 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.9 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.10 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.11 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.12 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.13 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.14 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.15 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.16 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.17 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.1 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.18 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.19 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.20 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.21 1.3.6.1.4.1.318.1.1.26.9.4.3.1.7.22;


def process_one_outlet(outlet_num, outlet_name, timestamp, varBinds, cbCtx):
    outlet_oid = cbCtx["pdu_oid"]+"."+outlet_num

    if outlet_oid in varBinds:
        outlet_unit = "W"
        outlet_value = varBinds[outlet_oid]
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
                "value": float(outlet_value),
            },
            "time": timestamp,
            "tags": {
                "location": outlet_location,
                "sensor": outlet_sensor_name,
                "unit": outlet_unit,
                "sensor_type": outlet_sensor_type
            }
        }]

        insertion_count = 1
        return data

    else:
        print("[%s] PDU returned no matching value for OID='%s' (%s)" % (outlet_name, outlet_oid, cbCtx))
        return []


def process_outlets_readings(snmpEngine, sendRequestHandle, errorIndication, errorStatus, errorIndex, varBinds, cbCtx):
    global influx_lock
    global RECORDS

    pdu_id = cbCtx["pdu_id"]
    timestamp = int(time.time())

    # Build a dictionary that associates oids and their values
    oids_to_values = {}
    for varBind in varBinds:
        oids_to_values[str(varBind[0][0])] = varBind[0][1]._value

    data = []
    for (outlet_num, outlet_name) in get_outlets(pdu_id).iteritems():
        data += process_one_outlet(outlet_num, outlet_name, timestamp, oids_to_values, cbCtx)

    print("[%s] %s rows have been fetch" % (pdu_id, len(data)))

    influx_lock.acquire()
    RECORDS += data
    influx_lock.release()

    return False


def flush_records(args):
    global influx_lock
    global RECORDS
    db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    flush_data = None

    influx_lock.acquire()
    flush_data = RECORDS
    RECORDS = []
    influx_lock.release()

    try:
        failure = not db_client.write_points(flush_data, time_precision="s")
        print("[influx] %s rows have been inserted in the database" % (len(flush_data)))
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    return False


def async_read_outlets_of_given_pdu(pdu_id):
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


def async_read_outlets_of_all_pdus(pdus):
    snmpEngine = SnmpEngine()
    for pdu_id in pdus:
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


def sync_read_outlets_of_all_pdus(pdus):
    global influx_lock
    global RECORDS
    timestamp = int(time.time())
    for pdu_id in pdus:
        # Build a snmpget command
        connection_info = get_connection_info_for_pdu(pdu_id)
        pdu_ip = connection_info["pdu_ip"]
        pdu_oid = connection_info["pdu_oid"]
        pdu_ctxt = {"pdu_id": pdu_id, "pdu_oid": pdu_oid}
        snmpget_cmd = "snmpget -v2c -c public %s " % (pdu_ip)
        for outlet_key, outlet_value in get_outlets(pdu_id).iteritems():
            snmpget_cmd += " %s.%s" % (pdu_oid, outlet_key)
        # Execute the snmpget command
        import subprocess
        snmp_output = subprocess.check_output([x for x in snmpget_cmd.split(" ") if x != ''])
        # Build a dictionary that associates oids and their values
        oids_to_values = {}
        for line in snmp_output.split("\n"):
            line = re.sub(r'.*\.9\.4\.3\.1\.7\.', '', line)
            line = re.sub(r'INTEGER: ', '', line)
            line = line.strip()
            if len(line) == 0:
                continue
            (outlet_oid_suffix, outlet_value) = line.split(" = ")
            outlet_oid = "%s.%s" % (pdu_oid, outlet_oid_suffix)
            oids_to_values[outlet_oid] = float(outlet_value)
        # Prepare a database record for each of the outlets
        data = []
        for outlet_key, outlet_value in get_outlets(pdu_id).iteritems():
            data += process_one_outlet(outlet_key, outlet_value, timestamp, oids_to_values, pdu_ctxt)
        # Put the outlets' consumption values in the list of values that should be inserted in DB
        influx_lock.acquire()
        RECORDS += data
        influx_lock.release()
    return False


def set_interval(f, args, interval_secs, task_name=None):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False

        def run(self):
            start_task_time = time.time()
            try:
                self.f(self.args)
            except:
                traceback.print_exc()
                print("Something bad happened here :-(")
                pass
            end_task_time = time.time()
            print("[sched:%s] took %f seconds to execute the task (starting: %f)" % (task_name, (end_task_time - start_task_time), start_task_time))
            time_to_sleep = (self.interval) - (end_task_time - start_task_time)
            if interval_secs != NO_PAUSE and time_to_sleep > 0:
                Timer(time_to_sleep, self.run).start()
            else:
                self.run()

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval_secs)
    t.start()
    return t


if __name__ == "__main__":

    help = """PDUs crawler

Usage:
  pdus_crawler.py --pdu=<pdu>
  pdus_crawler.py -l

Options:
  -h --help          Show this message and exit.
  -l --list          List PDUs that can be crawled.
"""
    arguments = docopt(help)
    pdus = get_pdus()

    if arguments["--list"]:
        print("Available pdus:")
        for pdu_name in pdus:
            print("  %s" % pdu_name)
        pass
        sys.exit(0)
    else:
        pdu_candidate = arguments["--pdu"]
        if pdu_candidate in pdus:
            print("I will start crawling '%s'" % pdu_candidate)
            last_pdu_reader = None
            set_interval(flush_records, (pdus), 30, task_name="influx")
            time.sleep(0.1)
            # set_interval(async_read_outlets_of_all_pdus, ([pdu_candidate]), 1, task_name="pdus_crawler")
            set_interval(sync_read_outlets_of_all_pdus, ([pdu_candidate]), 1, task_name="pdus_crawler")

            if last_pdu_reader is not None:
                last_pdu_reader.join()
        else:
            print("Could not find a pdu called '%s'" % pdu_candidate)
            sys.exit(1)

