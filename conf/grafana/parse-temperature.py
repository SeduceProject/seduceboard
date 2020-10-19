import json, yaml

def analyze(data, rack_name, position, alone_temps):
    global json_data
    if rack_name not in json_data:
        json_data[rack_name] = {}
    json_data[rack_name][position] = {}
    temp_names = json_data[rack_name][position]
    print('##### %s %s' % (rack_name, position.upper()))
    rack_info = data[rack_name][position]
    temp_idx = 0
    for temp in sorted(rack_info, key=lambda x: int(x), reverse=True):
        info = rack_info[temp]
        if len(info['tags']) == 0:
            print('%s: %s -> %s-%s' % (temp, info['serie'], alone_temps[temp_idx], position))
            temp_names[info['serie']] = '%s-%s' % (alone_temps[temp_idx], position)
            temp_idx += 1
        else:
            print('%s: %s -> temp-%s-%s' %(temp, info['serie'], info['tags'][0], position))
            temp_names[info['serie']] = '%s-%s' % (info['tags'][0], position)


with open('temperature.yaml', 'r') as yfile:
    temps = yaml.load(yfile, Loader=yaml.FullLoader)
json_data = {}
analyze(temps, 'Z1.5', 'back', ['temp-1', 'temp-2', 'temp-3', 'temp-4'])
analyze(temps, 'Z1.5','front', ['temp-1', 'temp-2', 'temp-3', 'temp-4'])
analyze(temps, 'Z1.4','back', ['temp-5', 'temp-6', 'temp-7', 'temp-8'])
analyze(temps, 'Z1.4','front', ['temp-5', 'temp-6', 'temp-7', 'temp-8'])
analyze(temps, 'Z1.2','back', ['temp-9', 'temp-10', 'temp-11', 'temp-12'])
analyze(temps, 'Z1.2','front', ['temp-9', 'temp-10', 'temp-11', 'temp-12'])
analyze(temps, 'Z1.1','back', ['temp-13', 'temp-14', 'temp-15', 'temp-16'])
analyze(temps, 'Z1.1','front', ['temp-13', 'temp-14', 'temp-15', 'temp-16'])

with open('temp_names.json', 'w') as jfile:
    json.dump(json_data, jfile, indent=4)
