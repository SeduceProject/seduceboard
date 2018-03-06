import requests
import json
from core.config.room_config import get_temperature_sensors_infrastructure

target_url = "http://localhost:8888/seduce"


def main():
    temperature_sensors_infrastructure = get_temperature_sensors_infrastructure()
    room = "b232"
    for (rack_id, rack_v) in temperature_sensors_infrastructure.iteritems():
        # Create a new Bus
        create_bus_url = "%s/buses/" % (target_url)
        create_bus_payload = {
            "name": rack_id,
        }
        result = requests.post(create_bus_url, json=create_bus_payload)
        for (position, sensor) in rack_v.get("positions_index").iteritems():
            # Create a new Sensor
            create_sensor_url = "%s/sensors/" % target_url
            create_sensor = {
                "mac": sensor,
                "model": "ds18b20",
                "name": "%s.%s" % (rack_id, position),
                "state": 0,
                "type": "temperature"
            }
            result = requests.post(create_sensor_url, json=create_sensor)

            # Create a new Position
            create_sensor_url = "%s/positions/" % target_url
            create_sensor = {
                "mac": sensor,
                "model": "ds18b20",
                "name": "%s.%s" % (rack_id, position),
                "state": 0,
                "type": "temperature"
            }
            result = requests.post(create_sensor_url, json=create_sensor)
        pass
    pass


if __name__ == "__main__":
    main()