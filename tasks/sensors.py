from core.data.sensors import get_sensors_arrays_with_children
from core.data.influx import db_last_sensors_updates
from dateutil import parser
from core.data.redis_counters import redis_increment_sensor_error_count
import celery
import time


@celery.task()
def detect_unresponsive_temperature_sensors():
    print("Detecting unresponsive temperature detectors")

    last_updates = db_last_sensors_updates()
    sensors_arrays_with_children = get_sensors_arrays_with_children()
    now_time = time.time()

    for sensors_array_key, sensors_array in sensors_arrays_with_children.items():
        for child in sensors_array["children"]:
            child_last_update = [x for x in last_updates if x.get("sensor") == child.get("name")]
            if len(child_last_update) > 0:
                last_update_since_epoch = int(time.mktime(parser.parse(child_last_update[0]["time"]).timetuple())) - time.timezone
                time_since_last_update_secs = now_time - last_update_since_epoch

                if time_since_last_update_secs > 40:
                    print("%s is unresponsive since %s seconds: I increment his error counter" % (child.get("name"), time_since_last_update_secs))
                    redis_increment_sensor_error_count(child.get("name"))
