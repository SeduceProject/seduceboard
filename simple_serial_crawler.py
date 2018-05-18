import threading
from serial import Serial
import time
import sys
import json
from influxdb import InfluxDBClient
import traceback

DB_HOST = "127.0.0.1"
DB_PORT = 6379
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "calibration"


def handle_msg(msg):
    if "-->" in msg:
        try:
            values = msg.split(" ")
            sensor_id = values[1]
            temperature = float(values[3])
            timestamp = int(time.time())

            data = [{
                "measurement": "sensors",
                "fields": {
                    "value": temperature
                },
                "timestamp": timestamp,
                "tags": {
                    "location": "room exterior",
                    "sensor": sensor_id,
                    "unit": "celsius",
                    "sensor_type": "temperature"
                }
            }]

            db_client = InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
            flush_data = [data]

            try:
                failure = not db_client.write_points(flush_data, time_precision="s")
                print("[influx] %s rows have been inserted in the database" % (len(flush_data)))
            except:
                traceback.print_exc()
                failure = True

            db_client.close()

            print(msg)
        except:
            print("Error with msg: '%s'" % msg)


if __name__ == "__main__":

    serial_device_path = "/dev/cu.SLAB_USBtoUART"
    baudrate = 9600

    with Serial(port=serial_device_path, baudrate=baudrate, timeout=1, writeTimeout=1) as serial_port:
        if serial_port.isOpen():
            while True:
                msg = serial_port.readline()
                if msg != "":
                    handle_msg(msg.strip())
    sys.exit(0)