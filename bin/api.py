from flask import Flask, jsonify
from flask import request
from flasgger import Swagger
from core.data.influx import *
from core.config.rack_config import extract_nodes_configuration
from logger_conf import setup_root_logger
from datetime import datetime

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'SeDuCe API',
    'uiversion': 3
}
swagger = Swagger(app)

DEBUG = True


@app.route('/')
def index():
    return jsonify({
        "api_documentation_url": "/apidocs",
        "api_specification_url": "/apispec_1.json",
        "message": "Read the api documentation at http://api.seduce.fr/apidocs/ , or get the specification of the API at http://api.seduce.fr/apispec_1.json"
    })


@app.route('/sensors')
def sensors():
    """Endpoint returning IDs of all sensors of the Seduce infrastructure.
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
    definitions:
      SensorsDict:
        type: object
        properties:
          sensors:
            type: array
            items:
              type: string
    responses:
      200:
        description: A object containing a list of the sensors parts of the infrastructure
        schema:
          $ref: '#/definitions/SensorsDict'
        examples:
          response: {
              "sensors": [
                "2800622b090000e6",
                "28006d2c0900000f",
                "ecotype-10_pdu-Z1.50",
                "ecotype-10_pdu-Z1.51",
                "ecotype-11_pdu-Z1.50",
                "ecotype-11_pdu-Z1.51",
                "electrical_mgmt_board_pdu-Z1.11",
                "switch_mgmt_pdu-Z1.40",
                "switch_prod_1_pdu-Z1.51",
                "switch_prod_2_pdu-Z1.21",
                "wattmeter_condensator",
                "wattmeter_cooling",
                "wattmeter_servers"
              ],
              "since": "1510232877.81"
            }
    """
    from core.data.influx import db_sensors
    result = db_sensors()
    return jsonify(result)


@app.route('/sensors_types')
def sensors_types():
    """Endpoint returning what kind of sensors are part of the Seduce infrastructure.
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors_types
    definitions:
      SensorsTypesDict:
        type: object
        properties:
          sensors_types:
            type: array
            items:
              type: string
    responses:
      200:
        description: A object containing what kind of sensors are part of the Seduce infrastructure.
        schema:
          $ref: '#/definitions/SensorsTypesDict'
        examples:
          response: {
              "sensor_types": [
                "temperature",
                "wattmeter"
              ]
            }
    """
    from core.data.influx import db_sensor_types
    result = db_sensor_types()
    return jsonify(result)


@app.route('/sensors_types/<sensor_type>/sensors')
def sensors_of_specified_sensors_type(sensor_type):
    """Endpoint returning sensors that corresponds to a specified kind of sensors.
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
      - sensors_types
    parameters:
      - name: "sensor_type"
        in: "path"
        description: "A sensor type"
        required: true
        type: string
    responses:
      200:
        description: A object containing what kind of sensors are part of the Seduce infrastructure.
        schema:
          $ref: '#/definitions/SensorsDict'
        examples:
          response: {
              "sensor_types": [
                "temperature",
                "wattmeter"
              ]
            }
    """
    from core.data.influx import db_sensors
    result = db_sensors(sensor_type=sensor_type)
    return jsonify(result)


@app.route('/servers/all/sensors')
def servers_and_sensors():
    """Endpoint returning servers and network switches, including the sensors associated with them.
    ---
    tags:
      - servers
      - sensors
    definitions:
      ServerDict:
        type: object
        properties:
          name:
            type: string
          temp:
            type: object
            properties:
              front:
                type: string
              back:
                type: string
          power:
            type: array
            items:
              type: string
    responses:
      200:
        description: An object describing the sensors associated to servers of SeDuCe.
        schema:
          $ref: '#/definitions/ServerDict'
        examples:
          response: [{
              "name": "ecotype-1",
              "temp": {
                "front": "temp_front_ecotype1",
                "back": "temp_back_ecotype1",
              },
              "power": [
                "pdu1.ecotype1",
                "pdu2.ecotype1"
              ]
            }]
    """

    result = []

    ecotype_configuration = extract_nodes_configuration("nantes", "ecotype")

    for server_short_name in ecotype_configuration.get("power").keys():

        temperature_sensors_of_the_server = {
        }

        power_sensors_of_the_server = []

        # Find the temperature sensors
        for rack_name, rack_sensors_per_side in ecotype_configuration.get("temperature", {}).items():
            for side, sensor_dict in rack_sensors_per_side.items():
                sensor_matches = [sensor for sensor in sensor_dict.values() if server_short_name in sensor.get("tags", [])]
                if len(sensor_matches) > 0:
                    sensor_serie = sensor_matches[0].get("serie")
                    temperature_sensors_of_the_server[side] = sensor_serie

        # Find the power sensors
        for pdu_name, sensor_name in ecotype_configuration.get("power").get(server_short_name).items():
            power_sensors_of_the_server += [sensor_name]

        result += [{
            "name": server_short_name,
            "temp": temperature_sensors_of_the_server,
            "power": power_sensors_of_the_server
        }]

    return jsonify(result)


@app.route('/sensors/<sensor_id>/measurements')
def measurements(sensor_id):
    """Endpoint returning sensors that corresponds to a specified kind of sensors.
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
      - sensors_types
      - measurements
    definitions:
      MeasurementsDict:
        type: object
        properties:
          start_date:
            type: string
          end_date:
            type: string
          timestamps:
            type: array
            items:
              type: string
          epoch_ts:
            type: array
            items:
              type: int
          values:
            type: array
            items:
                type: any
          epoch_ts:
            type: array
            items:
              type: int
          is_downsampled:
            type: boolean
          sensor_name:
            type: string
    parameters:
      - name: "sensor_id"
        in: "path"
        description: "A sensor ID"
        required: true
        type: string
        schema:
            example: "3b00065909fc2caf"
      - name: "start_date"
        in: "query"
        description: "Start date (YY-MM-DD-hh-mm)"
        required: true
        type: string
        pattern: "^([0-9]{2})-([0-9]{2})-([0-9]{2})-([0-9]{2})-([0-9]{2})$"
      - name: "end_date"
        in: "query"
        description: "End date (YY-MM-DD-hh-mm)"
        required: true
        type: string
        pattern: "^([0-9]{2})-([0-9]{2})-([0-9]{2})-([0-9]{2})-([0-9]{2})$"
    responses:
      200:
        description: A object containing what kind of sensors are part of the Seduce infrastructure.
        schema:
          $ref: '#/definitions/SensorsDict'
        examples:
          response: {
              "sensor_types": [
                "temperature",
                "wattmeter"
              ]
            }
    """
    from core.data.influx import db_sensor_data
    start_date = datetime.strptime(request.args["start_date"],  '%y-%m-%d-%H-%M')
    end_date = datetime.strptime(request.args["end_date"],  '%y-%m-%d-%H-%M')
    result = db_sensor_data(sensor_id,
            start_date="%ds" % start_date.timestamp(),
            end_date="%ds" % end_date.timestamp())
    return jsonify(result)


@app.route('/power_infrastructure/description/tree')
def power_infrastructure():
    """Endpoint returning an hierarchical description of the Seduce infrastructure.
    ---
    tags:
      - power_infrastructure
    definitions:
      TreeDict:
        type: object
        properties:
          level:
            type: int
          node:
            type: object
            properties:
              id:
                type: string
              name:
                type: string
              root:
                type: boolean
              target:
                type: string
                required: false
              children:
                type: array
                items:
                  type: string
                required: false
          children:
            type: array
            items:
              type: TreeDict
    responses:
      200:
        description: A JSON object describing the Seduce infrastructure.
        schema:
          $ref: '#/definitions/TreeDict'
        examples:
          response: {
            "level": 0,
            "children": [
              {
                "level": 1,
                "children": [
                  # a list of children nodes
                ],
                "node": {
                  "children": [
                    "cooling_room"
                  ],
                  "id": "room",
                  "name": "Room",
                   "root": false
                  }
                },
                {
                "level": 1,
                "children": [
                  # a list of children nodes
                ],
                "node": {
                  "children": [
                    "cooling_cluster",
                    "hardware_cluster"
                  ],
                  "id": "cluster",
                  "name": "Cluster",
                   "root": false
                  }
                }
            ],
            "node": {
              "children": [
                "cluster",
                "room"
              ],
              "id": "datacenter",
              "name": "Datacenter",
               "root": true
              }
            }
    """

    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_tree
    root_node_id = "datacenter"
    starting_node = get_node_by_id(root_node_id)
    if starting_node is not None:
        tree = get_tree(starting_node, False)
        return jsonify(tree)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (root_node_id)})


@app.route('/infrastructure/description/tree')
def infrastructure():
    """Endpoint returning an hierarchical description of the Seduce infrastructure.
    ---
    tags:
      - infrastructure
    definitions:
      TreeDict:
        type: object
        properties:
          level:
            type: int
          node:
            type: object
            properties:
              id:
                type: string
              name:
                type: string
              root:
                type: boolean
              target:
                type: string
                required: false
              children:
                type: array
                items:
                  type: string
                required: false
          children:
            type: array
            items:
              type: TreeDict
    responses:
      200:
        description: A JSON object describing the Seduce infrastructure.
        schema:
          $ref: '#/definitions/TreeDict'
        examples:
          response: {
            "level": 0,
            "children": [
              {
                "level": 1,
                "children": [
                  # a list of children nodes
                ],
                "node": {
                  "children": [
                    "cooling_room"
                  ],
                  "id": "room",
                  "name": "Room",
                   "root": false
                  }
                },
                {
                "level": 1,
                "children": [
                  # a list of children nodes
                ],
                "node": {
                  "children": [
                    "cooling_cluster",
                    "hardware_cluster"
                  ],
                  "id": "cluster",
                  "name": "Cluster",
                   "root": false
                  }
                }
            ],
            "node": {
              "children": [
                "cluster",
                "room"
              ],
              "id": "datacenter",
              "name": "Datacenter",
               "root": true
              }
            }
    """

    from core.config.rack_config import extract_nodes_configuration
    ecotype_configuration = extract_nodes_configuration("nantes", "ecotype")
    if ecotype_configuration is not None:
        return jsonify(ecotype_configuration)
    else:
        return jsonify({"status": "failure", "cause": "Could not extract configuration for ecotype cluster in Nantes"})


if __name__ == "__main__":
    setup_root_logger("/tmp/api.log")
    app.run(host="0.0.0.0", port=5069, debug=DEBUG, threaded=True)

