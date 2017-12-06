from serial import Serial
import sys
import time
import re
import os
import threading
from threading import Timer
import traceback

from docopt import docopt
from core.data.pdus import get_pdus, get_outlets, get_outlets_names
from core.data.db import *

BAUDRATE = 9600
NO_PAUSE = -1

RECORDS = []
influx_lock = threading.Lock()


def process_one_outlet(outlet_name, timestamp, outlet_value, outlet_sensor_name):

    outlet_unit = "W"
    outlet_location = outlet_name
    outlet_sensor_name = outlet_sensor_name
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

    return data


def process_reading(msg, pdu_name, outlets):
    global influx_lock
    global RECORDS
    if re.match("( |[0-9])[0-9]: Outlet [0-9]+: [0-9]+ W", msg) is not None:
        (outlet_num, outlet_name, outlet_reading_str) = msg.replace("W", "").strip().split(":")

        # print("%s -> %s" % (outlet_num, outlet_reading_str))
        if outlet_num in outlets:
            timestamp = int(time.time())
            outlet_name = outlets[outlet_num]
            outlet_sensor_name = outlet_name+"_"+pdu_name
            data = process_one_outlet(outlet_name, timestamp, outlet_reading_str, outlet_sensor_name)

            influx_lock.acquire()
            RECORDS += data
            influx_lock.release()


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

    help = """PDUs serial crawler

    Usage:
      pdus_serial_crawler.py --pdu=<pdu> --serial=<serial>
      pdus_serial_crawler.py --list-pdus
      pdus_serial_crawler.py --list-serial

    Options:
      -h --help        Show this message and exit.
      --list-pdus      List PDUs that are in the configuration.
      --list-serial    List serial ports that can be crawled.
    """
    arguments = docopt(help)
    pdus = get_pdus()

    if arguments["--list-pdus"]:
        print("Available pdus:")
        for pdu_name in pdus:
            print("  %s" % pdu_name)
        pass
        sys.exit(0)
    elif arguments["--list-serial"]:
        files = [f for f in os.listdir('/dev') if re.match(r'.*tty(\.|.*USB|.*usb).*', f)]
        print("Available serial ports:")
        for file in files:
            print("  /dev/%s" % file)
        pass
        sys.exit(0)
    else:
        pdu_name = arguments["--pdu"]
        serial_device_path = arguments["--serial"]

        outlets = get_outlets(pdu_name)
        outlet_num_min = min([int(x) for x in outlets])
        outlet_num_max = max([int(x) for x in outlets])
        outlet_range = "%i-%i" % (outlet_num_min, outlet_num_max)

        with Serial(port=serial_device_path, baudrate=BAUDRATE, timeout=1, writeTimeout=1) as serial_port:
            if serial_port.isOpen():

                # Launch the background function that will be in charge of saving
                # data to the database
                set_interval(flush_records, ("Nothing"), 30, task_name="influx")

                # Try to wake up the APC daemon in charge of listing to serial port
                serial_port.writelines(["\r\n"])
                serial_port.writelines(["\r"])
                time.sleep(1)
                # Wait for user prompt and answer "apc"
                wait_for_user_prompt = True
                got_shell_prompt = False
                # Simulate a user that press "\n" until he get a prompt asking
                # for user name and password
                while not got_shell_prompt:
                    msg = serial_port.readline()
                    # The user is already logged in
                    if "apc>" in msg:
                        got_shell_prompt = True
                    # At last, we got this prompt asking for user name
                    elif "User Name :" in msg:
                        time.sleep(1)
                        serial_port.writelines("apc\r")
                        wait_for_user_prompt = False
                        time.sleep(1)
                        # Now the user will try to enter his password until he succeed to access
                        # the APC console.
                        while not got_shell_prompt:
                            msg2 = serial_port.readline()
                            # At last, we got this prompt asking for password
                            if "Password" in msg2:
                                serial_port.writelines("apc\r")
                            # Woot! we are connected to the APC console!!
                            if "Schneider" in msg2:
                                got_shell_prompt = True
                    elif "Bye" in msg:
                        serial_port.writelines(["\r\n"])
                    else:
                        serial_port.writelines(["\r"])
                # At this point, we got a shell prompt
                cpt = 0
                while True:
                    cpt += 1
                    # if cpt % 8 == 0:
                    #     time.sleep(0.05)
                    msg = serial_port.readline()
                    if msg != "":
                        # We are back to the APC prompt waiting for a command
                        if "apc>" in msg:
                            # Entering a command that will display power consumption
                            # for each outlet
                            serial_port.writelines("olReading 1:%s power\nolReading 1:%s power\n" % (outlet_range, outlet_range))
                        else:
                            # Processing a line that is likely to correspond to a
                            # power reading of an outlet
                            process_reading(msg, pdu_name, outlets)
    sys.exit(0)
