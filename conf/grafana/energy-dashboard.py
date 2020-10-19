from influxdb import InfluxDBClient
import ast, copy, json, re

# name -> sensor name in the DB ; surname: sensor name in the grafana graph
sensor_surname = [
            { 'surname': 'PV', 'pattern': 'solar.*P_AC' },
            { 'surname': 'ecotype-', 'pattern': 'ecotype.*pdu-Z1.10' }
        ]
dashboard_file = 'Energy.json'
client = InfluxDBClient(host='127.0.0.1', port=8086, database='pidiou')
with open(dashboard_file, 'r') as json_file:
    conf = json.load(json_file)
    for panel in conf['panels']:
        if 'tags' in panel['targets'][0]:
            for surname in sensor_surname:
                tag_name = panel['targets'][0]['tags'][0]['value']
                if re.match(surname['pattern'], tag_name) is not None:
                    print(tag_name)
                    sensor_template = panel['targets'][0]
                    panel['targets'] = []
                    sensor_info = client.query("show tag values with key = sensor where value =~ /%s/" % surname['pattern']).raw
                    sensors = []
                    for sensor in sensor_info['series'][0]['values']:
                        sensors.append(sensor[1])
                    sensors = sorted(sensors, key=lambda name: int(re.findall(r'\d+', name)[0]))
                    print(sensors)
                    for sensor in sensors:
                        new_template = copy.deepcopy(sensor_template)
                        new_template['tags'][0]['value'] = sensor
                        nb = re.findall(r'\d+', sensor)[0]
                        new_template['alias'] = '%s%s' % (surname['surname'], nb)
                        panel['targets'].append(new_template)
with open('new_%s' % dashboard_file, 'w') as json_file:
    json.dump(conf, json_file, indent=4)
