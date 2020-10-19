from influxdb import InfluxDBClient
import ast, copy, json, re

dashboard_file = 'Temperatures.json'
with open('temp-names.json', 'r') as json_file:
    temp_names = json.load(json_file)
with open(dashboard_file, 'r') as json_file:
    conf = json.load(json_file)
    sensor_template = None
    for panel in conf['panels']:
        if sensor_template is None:
            sensor_template = panel['targets'][0]
        panel['targets'] = []
        rack_info = panel['title'].split()
        sensor_info = temp_names[rack_info[1]][rack_info[2].lower()]
        for sensor in sensor_info:
            new_template = copy.deepcopy(sensor_template)
            new_template['tags'][0]['value'] = sensor
            new_template['alias'] = sensor_info[sensor]
            panel['targets'].append(new_template)
with open('new_%s' % dashboard_file, 'w') as json_file:
    json.dump(conf, json_file, indent=4)
