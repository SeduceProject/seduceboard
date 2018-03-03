import sys
from influxdb import InfluxDBClient
import traceback
import subprocess
from core.data.cq_aggregates import cqs_recreate_all
from core.data.cq_aggregates import cqs_recompute_data
from core.data.cq_aggregates import cq_multitree_recreate_all
import random


N_WATTMETER = 96
N_THERMOMETER = 96
WATTMETER_INTERVAL_SECS = 1
THERMOMETER_INTERVAL_SECS = 30
SIMULATION_DURATION = 7 * 24 * 3600

DAY_DURATION = 24 * 3600

WRITE_EACH_PIECE_OF_DATA = False

DB_CLIENT = InfluxDBClient("127.0.0.1", 8086, "root", "root", "pidiou")


def simulate_temperature_record(timestamp, value, thermometer):
    return [{
        "measurement": "sensors",
        "fields": {
            "value": value
        },
        "time": timestamp,
        "tags": {
            "location": "room thermometer",
            "sensor": thermometer,
            "unit": "celsius",
            "sensor_type": "thermometer"
        }
    }]


def simulate_wattmeter_record(timestamp, value, wattmeter):
    return [{
        "measurement": "sensors",
        "fields": {
            "value": value
        },
        "time": timestamp,
        "tags": {
            "location": "room wattmeter",
            "sensor": wattmeter,
            "unit": "W",
            "sensor_type": "wattmeter"
        }
    }]


def simulate_with_real_data_for_given_duration(start_date, duration, day, graph_data):
    global DB_CLIENT
    data = []
    for t in range(0, duration):
        seconds = t % 60
        minutes = ((t - seconds) / 60) % 60
        hours = ((t - seconds - 60 * minutes) / 3600) % 24

        print("[%s] %s : %s : %s" % (day, hours, minutes, seconds))
        random_watt = random.uniform(110, 120)
        random_temp = random.uniform(22, 24)

        if t % WATTMETER_INTERVAL_SECS == 0:
            for wm in range(0, N_WATTMETER):
                data += simulate_wattmeter_record(start_date + t, random_watt  + 0.01 * t, wm)
        if t % THERMOMETER_INTERVAL_SECS == 0:
            for tm in range(0, N_WATTMETER):
                data += simulate_temperature_record(start_date + t, random_temp + 0.01 * t, tm)
        if t % 3600 == 0:
            DB_CLIENT.write_points(data)
            data = []
        if t % 1800 == 0:
            influxdb_size = get_influx_size()
            graph_data += [(start_date + t, influxdb_size)]
    return True


def get_influx_size():
    proc = subprocess.Popen(["du ~/.influxdb | tail -n 1 | awk '{print $1}'"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return int(out)


def simulate_with_real_data():
    print("""I will simulate the following infrastructure:
    - 1 temperature record every %s second(s)
    - 1 wattmeter record every %s second(s)
    - %s wattmeter(s)
    - %s temperature sensor(s)
    - simulation duration is %s second(s)
    
    """ % (THERMOMETER_INTERVAL_SECS, WATTMETER_INTERVAL_SECS, N_THERMOMETER, N_WATTMETER, SIMULATION_DURATION))

    # Create continuous queries
    cqs_recreate_all(force_creation=True)
    cqs_recompute_data()

    # Launch the simulation
    graph_data = []
    n_days = SIMULATION_DURATION / (24 * 3600)

    influxdb_size = get_influx_size()
    graph_data += [(0, influxdb_size)]
    for day in range(1, n_days + 1):
        print("day: %i" % day)
        simulate_with_real_data_for_given_duration(day * DAY_DURATION, DAY_DURATION, day, graph_data)

        influxdb_size = get_influx_size()
        graph_data += [(day * DAY_DURATION, influxdb_size)]

    # Display results
    print("==== result ====")
    print(graph_data)

    pass


if __name__ == "__main__":
    # simulate_with_real_data()
    print get_influx_size()
    sys.exit(0)