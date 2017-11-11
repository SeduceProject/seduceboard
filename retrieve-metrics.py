#!/usr/bin/python

# bash command: snmpwalk -mALL -v1 -cpublic grimani-pdu1 iso.3.6.1.4.1.318.1.1.26.9.4.3.1.7 > toto

import datetime
from influxdb import InfluxDBClient
import json
import os
from pysnmp.hlapi.asyncore import *
import sys
import time

# Variables
# Query only few devices (e.g., PDU), do not add sensor names in this variable
DEVICE_FILTER = []
#DEVICE_FILTER = [ 'grimani-pdu1', 'graphene-pdu7' ]
# Record metrics only for few sensors (e.g. nodes), do not add device names in this variable
SENSOR_FILTER = []
#SENSOR_FILTER = [ 'grisou-30', 'grimani-2', 'grele-11' ]
# Number of measure to retrieve before stopping (0: infinite)
NB_MEASURE = 0
# Threshold to sum consumption values with the same timestamp (in seconds)
SUM_THRESHOLD = 2 
# Frequency of the measurements in seconds (minimum: 1s)
MONITORING_PERIOD = 1
# Number of errors before ignoring the PDU
NB_ERRORS = 4
# Database configuration
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pidiou'
# Write errors to the LOG_FILE
DEBUG = True

# Functions
def log(msg):
    if DEBUG:
        print msg
        f = open(LOG_FILE, 'a')
        f.write('%s - %s\n' % (datetime.datetime.now(), msg))
        f.close()

def cooling_points(identifier, timestamp, cons):
    return  {
                'measurement': 'cooling_0',
                'tags': {
                    'identifier': identifier,
                    'site': "nantes"
                },
                'time': timestamp,
                'fields': {
                    'value': cons
                }
            }

def node_points(cluster, pdu, node, timestamp, cons):
    return  {
                'measurement': 'node_0',
                'tags': {
                    'cluster': cluster,
                    'identifier': node,
                    'pdu': pdu,
                    'site': "nantes"
                },
                'time': timestamp,
                'fields': {
                    'nb_sources': nodes[node]['source'],
                    'value': cons
                }
            }

def pdu_points(cluster, pdu, timestamp, cons):
    return  {
                'measurement': 'pdu_0',
                'tags': {
                    'cluster': cluster,
                    'identifier': pdu,
                    'site': "nantes"
                    },
                'time': timestamp,
                'fields': {
                    'value': cons
                }
            }

# Need another key in my JSON configuration file
def pcooling(sensor, config, values):
    return cooling(sensor, config, values)

def cooling(sensor, config, values):
    json_body = []
    for idx, sname in config['sensors'].iteritems():
        if values[idx] >= 0:
            json_body.append(cooling_points(sname, config['timestamp'], values[idx]))
        else:
            log('[%s - %s]: Negative value for index %s' % (sensor, sname, idx))
    return json_body

def power(sensor, config, values):
    json_body = []
    if config['nb_values'] == 1:
        # The PDU monitors the global consumption of all nodes
        cluster = sensor.split('-')
        if len(cluster) > 1 and len(cluster[0]) > 3:
            # A valid cluster name consists of at least 4 characters (ex, edel)
            cluster_name = cluster[0]
        else:
            cluster_name = 'unknown'
        # Insert the consumption into the database
        if values.values()[0] >= 0:
            json_body.append(pdu_points(cluster_name, sensor, config['timestamp'], values.values()[0]))
        else:
            log('[%s]: Negative value for the global consumption' % sensor)
    else:
        # The PDU monitors the consumption of every node
        for idx, sname in config['sensors'].iteritems():
            # Insert consumptions into the database
            cluster = sname.split('-')
            if len(cluster) > 1 and len(cluster[0]) > 3:
                # A valid cluster name consists of at least 4 characters (ex, edel)
                cluster_name = cluster[0]
            else:
                cluster_name = 'unknown'
            if idx in values and values[idx] >= 0:
                json_body.append(node_points(cluster_name, sensor, sname, config['timestamp'], values[idx]))
                # Aggregate consumptions for nodes with multiple power supplies
                node = nodes[sname]
                node['consumptions'][sensor] = [ config['timestamp'], values[idx] ]
                if node['source'] > 1 and len(node['consumptions']) == node['source']:
                    save_value = True
                    # Check the timestamp of the values
                    my_timestamps = []
                    my_values = []
                    for val in node['consumptions'].values():
                        my_timestamps.append(val[0])
                        my_values.append(val[1])
                    min_t = min(my_timestamps)
                    for t in my_timestamps:
                        if t - min_t > SUM_THRESHOLD:
                            save_value = False
                    if save_value:
                        config['timestamp'] = min_t
                        cons = sum(my_values)
                        node['consumptions'] = {}
                        json_body.append(node_points(cluster_name, 'aggregated', sname,
                            config['timestamp'], cons))
            else:
                log('[%s - %s]: Wrong value for index %s (%s)' % (sensor, sname, idx, (idx in values)))
    return json_body

def snmp_process(snmpEngine, sendRequestHandle, errorIndication, errorStatus, errorIndex, varBinds, cbCtx):
    timestamp = int(time.time())
    req_info = requests[sendRequestHandle].split('_')
    sensor_name = req_info[0]
    sensor_type = req_info[1]
    config = devices[sensor_name][sensor_type]
    del requests[sendRequestHandle]
    if config['timestamp'] != timestamp:
        values = {}
        idx = -1
        if len(varBinds) > 1:
            # Find a different column index in OID of SNMP values
            i = len(varBinds) - 1
            cons0 = varBinds[0][0][0]
            cons1 = varBinds[1][0][0]
            while str(cons0).split('.')[idx] == str(cons1).split('.')[idx] and idx > len(varBinds) * -1:
                idx -= 1
        for cons in varBinds:
            try:
                # Keep only integer values
                values[str(cons[0][0]).split('.')[idx]] = int(cons[0][1])
            except:
                # Wrong values, for instance, string values
                pass
        config['timestamp'] = timestamp
        if len(values) < config['nb_values']:
            config['errors'] += 1
            log('[%s - %s]: Wrong number of values (expected: %d, actual: %d)' % (sensor_name, sensor_type,
                config['nb_values'], len(values)))
        else:
            config['errors'] = 0
            if sensor_type in globals():
                json_body = globals()[sensor_type](sensor_name, config, values)
                if len(json_body) > 0:
                    db_client.write_points(json_body, time_precision='s')
            else:
                log('[%s - %s]: Unkwown sensor type' % (sensor_name, sensor_type))
    config['state'] = 'done'

def query_devices():
    global last_measure
    snmpEngine = SnmpEngine()
    for dname, dconfig in devices.iteritems():
        ip = dname
        for sensor, sconfig in dconfig.iteritems():
            if sensor == 'ip':
                ip = sconfig
            else:
                # Query the sensor
                try:
                    # Ensure the last query is complete and limit to one measure every second
                    now = int(time.time())
                    if sconfig['state'] == 'done':
                        # Execute SNMP requests
                        if sconfig['errors'] > NB_ERRORS and \
                                time.time() - sconfig['timestamp'] > sconfig['errors']:
                            # Retry to query the PDU
                            sconfig['errors'] = 0
                        if sconfig['errors'] < NB_ERRORS:
                            req_id = bulkCmd(snmpEngine,
                                    CommunityData('public'),
                                    UdpTransportTarget((ip, 161)),
                                    ContextData(),
                                    0, sconfig['snmp_length'],
                                    ObjectType(ObjectIdentity(sconfig['oid'])),
                                    cbFun=snmp_process)
                            requests[req_id] = '%s_%s' % (dname, sensor)
                            sconfig['state'] = 'pending'
                        elif sconfig['errors'] == NB_ERRORS:
                            # Wait 1 hour before querying the PDU again
                            sconfig['errors'] = 3600
                            log('[%s] Ignored PDU, too many errors' % dname)
                except Exception as e:
                    sconfig['errors'] += 1
                    log('[%s - %s]: Wrong SNMP configuration - %s' % (dname, sensor, e))
    delta = time.time() - last_measure
    while delta < MONITORING_PERIOD:
        time.sleep(MONITORING_PERIOD - delta)
        delta = time.time() - last_measure
    last_measure = int(time.time())
    if snmpEngine.transportDispatcher is None:
        log("No SNMP commands")
    else:
        snmpEngine.transportDispatcher.runDispatcher()

# # Get the site name and configure constants
# if len(sys.argv) == 2:
#     SITE = sys.argv[1]
# else:
#     SITE = 'nantes'
# DEVICE_FILE = 'config-%s.json' % SITE
# LOG_FILE = 'error-%s.log' % SITE

DEVICE_FILE = "conf/config-nantes.json"
LOG_FILE = "logs/error-nantes.log"

# # Check the configuration file exists
# if not os.path.isfile(DEVICE_FILE):
#     print 'ERROR: File \'%s\' not found. Run \'./config_generator.py %s\'' % (DEVICE_FILE, SITE)
#     sys.exit(13)

# Node power consumptions
nodes = {}
# SNMP requests
requests = {}
# Connection to the database
db_client = InfluxDBClient('localhost', 8086, DB_USER, DB_PASSWORD, DB_NAME)
db_client.create_database('pidiou')

# Gather information about devices
devices = json.load(open(DEVICE_FILE, 'r'))
# Check incompatibility
if len(DEVICE_FILTER) > 0 and len(SENSOR_FILTER) > 0:
    log('DEVICE_FILTER and SENSOR_FILTER can not be enabled at the same time')
    sys.exit(13)
# Apply the device filter
if len(DEVICE_FILTER) > 0:
    for dname in devices.keys():
        if dname not in DEVICE_FILTER:
            del devices[dname]
# Apply the sensor filter
if len(SENSOR_FILTER) > 0:
    for dname in devices.keys():
        for metric in devices[dname].keys():
            if 'sensors' in devices[dname][metric]:
                props = devices[dname][metric]['sensors']
                for idx in props.keys():
                    sensor_name = props[idx].replace('SENSOR', dname)
                    if sensor_name not in SENSOR_FILTER:
                        del props[idx]
                if len(props) == 0:
                    del devices[dname]
# Configure devices
for dname, props in devices.iteritems():
    for metric, mconfig in props.iteritems():
        if metric != 'ip':
            mconfig['state'] = 'done'
            mconfig['errors'] = 0
            mconfig['timestamp'] = 0
            for idx in mconfig['sensors']:
                mconfig['sensors'][idx] = mconfig['sensors'][idx].replace('SENSOR', dname)
        # Store consumptions to aggregate power consumptions for nodes with multiple supplies
        if metric == 'power' and mconfig['nb_values'] > 1:
            for node_name in mconfig['sensors'].values():
                if node_name not in nodes:
                    nodes[node_name] = { 'source': 0, 'consumptions': {} }
                nodes[node_name]['source'] += 1

# Start the monitoring loop
last_measure = 0
if NB_MEASURE == 0:
    while True:
        query_devices()
else:
    for i in range(0, NB_MEASURE):
        query_devices()

