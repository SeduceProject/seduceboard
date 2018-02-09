from flask import Flask, jsonify
from flasgger import Swagger
from core.data.db import *
from flask import request

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Seduce API',
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
    from core.data.db import db_sensors
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
    from core.data.db import db_sensor_types
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
    definitions:
      MeasurementsDict:
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
          $ref: '#/definitions/SensorsDict'
        examples:
          response: {
              "sensor_types": [
                "temperature",
                "wattmeter"
              ]
            }
    """
    from core.data.db import db_sensors
    result = db_sensors(sensor_type=sensor_type)
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
    parameters:
      - name: "sensor_id"
        in: "path"
        description: "A sensor ID"
        required: true
        type: string
      - name: "start_date"
        in: "query"
        description: "A start date (epochTime)"
        required: true
        type: int
      - name: "end_date"
        in: "query"
        description: "A end date (epochTime)"
        required: true
        type: int
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
    from core.data.db import db_sensor_data
    start_date = request.args["start_date"]
    end_date = request.args["end_date"]
    result = db_sensor_data(sensor_id, start_date=start_date, end_date=end_date)
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
    app.run(host="0.0.0.0", port=5000, debug=DEBUG, threaded=True)

