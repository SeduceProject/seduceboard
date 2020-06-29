# Architecture

The SeDuCe dashboard is a web application which contains several sub services:

- *frontend*
- *api*
- *influxdb*
- *pdu_crawler_z1_10*
- *pdu_crawler_z1_11*
- *pdu_crawler_z1_20*
- *pdu_crawler_z1_21*
- *pdu_crawler_z1_40*
- *pdu_crawler_z1_41*
- *pdu_crawler_z1_50*
- *pdu_crawler_z1_51*
- *temperature_registerer*
- *sensors_crawler*
- *modbus_crawler_entech*
- *modbus_crawler_inrow*
- *poe_crawler*
- *redis*
- *celery_beat*
- *celery_worker*

All theses services are run through [supervisord](http://supervisord.org/), which read a configuration file in `/etc/supervisord.conf` based on [the example configuration file](https://github.com/SeduceProject/seduceboard/blob/master/conf/seduce/supervisord.conf.example).
The overall architecture of the dashboard follows quite the functional architecture depicted by this Figure:

![SeDuCe dashboard architecture](img/seduce_portal.png)

## SeDuCe portal
- *frontend*

This service is in charge of serving a web UI to users of the SeDuCe testbed. It is developed using the python Flask framework and consist of monolithic web applications composed of several [blueprints](https://flask.palletsprojects.com/en/1.1.x/blueprints/).

The executable of this service is located in [bin/app.py](https://github.com/SeduceProject/seduceboard/blob/master/bin/app.py) and the resulting web app is available at [dashboard.seduce.fr](dashboard.seduce.fr/).

## SeDuCe API
- *api*

This service is in charge of serving an API to enable users to use the SeDuCe testbed. It is developed using the python Flask framework integrated with the [flasgger](https://github.com/flasgger/flasgger) framework to generate Swagger documentation.

The executable of this service is located in [bin/app.py](https://github.com/SeduceProject/seduceboard/blob/master/bin/api.py) and the resulting web app is available at [api.seduce.fr](api.seduce.fr/).

## InfluxDB
- *influxdb*

All the data regarding metrics collected in the SeDuCe system are stored in an InfluxDB database.
 
The following rules have been used to integrate SeDuCe with influx:

- each sensors stores its related values in the `sensors` serie, with a tag corresponding to its name. For example, values of sensors `ecotype-1_pdu-Z1.50` is stored in the following location: `sensors,location=ecotype-1,sensor=ecotype-1_pdu-Z1.50,sensor_type=wattmeter,unit=W`, which corresponds to:  
  <ul>
  <li>serie: `sensors`</li>
  <li>tags: `location=ecotype-1,sensor=ecotype-1_pdu-Z1.50,sensor_type=wattmeter,unit=W`</li>
  </ul>
- data from `sensors` are aggregated every 30s, 1m, 1h, 1d in series called
  <ul>
  <li>`measurement_downsample_1m,sensor=ecotype-1_pdu-Z1.50`</li>
  <li>`measurement_downsample_1h,sensor=ecotype-1_pdu-Z1.50`</li>
  <li>`measurement_downsample_1d,sensor=ecotype-1_pdu-Z1.50`</li>
  </ul>
- to ease the development of tree visualisation, data from power consumption and power production sensors are aggreagated in:
  <ul>
  <li>`cq_battery1_30s`</li>
  <li>`cq_battery1_1m`</li>
  <li>`cq_battery1_1h`</li>
  <li>`cq_battery1_1d`</li>
  </ul>


## Power consumption crawlers
- *pdu_crawler_z1_10*
- *pdu_crawler_z1_11*
- *pdu_crawler_z1_20*
- *pdu_crawler_z1_21*
- *pdu_crawler_z1_40*
- *pdu_crawler_z1_41*
- *pdu_crawler_z1_50*
- *pdu_crawler_z1_51*
- *poe_crawler*
- *modbus_crawler_inrow*

## Temperature Registerer
- *temperature_registerer*

## Entech crawlers
- *modbus_crawler_entech*

## Periodic tasks system
- *redis*
- *celery_beat*
- *celery_worker*


