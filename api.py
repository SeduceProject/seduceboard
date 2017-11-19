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

#
# @app.route('/infrastructure')
# def infrastructure():
#     """Endpoint returning a complete view of the infrastructure
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - infrastructure
#     definitions:
#       Infrastructure:
#         type: object
#         properties:
#           name:
#             type: string
#           rooms:
#             type: array
#             items:
#               $ref: '#/definitions/Room'
#       Room:
#         type: object
#         properties:
#           uuid:
#             type: string
#           name:
#             type: string
#           location:
#             type: string
#           description:
#             type: string
#           sensor_arrays:
#             type: array
#             items:
#               $ref: '#/definitions/SensorArray'
#           sensor_arrays_uuids:
#             type: array
#             items:
#               type: string
#       SensorArray:
#         type: object
#         properties:
#           uuid:
#             type: string
#           name:
#             type: string
#           room_uuid:
#             type: string
#           description:
#             type: string
#           sensors:
#             type: array
#             items:
#               $ref: '#/definitions/Sensor'
#           sensors_uuids:
#             type: array
#             items:
#               type: string
#       Sensor:
#         type: object
#         properties:
#           uuid:
#             type: string
#           name:
#             type: string
#           location:
#             type: string
#           description:
#             type: string
#           sensors_arrays:
#             type: array
#             items:
#               $ref: '#/definitions/SensorArray'
#     responses:
#       200:
#         description: A description of the infrastructure
#         schema:
#           $ref: '#/definitions/Infrastructure'
#         examples:
#           response: [{
#             "uuid": "ABCDEFGHIJKL12345",
#             "name": "b232",
#             "location": "IMT Atlantique",
#             "description": "Room hosting the bouillonantes g5k cluster",
#             "sensor_arrays": [{
#               "uuid": "EXCFJDKJD1382",
#               "name": "moteino1",
#               "room_uuid": "ABCDEFGHIJKL12345",
#               "description": "Moteino that is in charge of measuring temperature in room B232",
#               "sensors": [{
#                 "uuid": "DKsldkl98329",
#                 "name": "AF:CF:EF:B8:77",
#                 "array_uuid": "EXCFJDKJD1382",
#                 "index": 0,
#                 "description": "ds18b20"
#               }]
#             }]
#           }]
#     """
#     all_rooms = [{
#         "uuid": "ABCDEFGHIJKL12345",
#         "name": "b232",
#         "location": "IMT Atlantique",
#         "description": "Room hosting the bouillonantes g5k cluster",
#         "sensor_arrays": [{
#             "uuid": "EXCFJDKJD1382",
#             "name": "moteino1",
#             "room_uuid": "ABCDEFGHIJKL12345",
#             "description": "Moteino that is in charge of measuring temperature in room B232",
#             "sensors": [{
#                 "uuid": "DKsldkl98329",
#                 "name": "AF:CF:EF:B8:77",
#                 "array_uuid": "EXCFJDKJD1382",
#                 "index": 0,
#                 "description": "ds18b20"
#             }]
#         }]
#     }]
#     result = all_rooms
#     return jsonify(result)
#
#
# @app.route('/rooms')
# def rooms():
#     """Endpoint returning a list of the infrastructure's rooms
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - rooms
#     parameters:
#       - name: load_relationships
#         in: query
#         type: boolean
#         default: false
#     responses:
#       200:
#         description: A list of rooms
#         schema:
#             type: "array"
#             items:
#                 $ref: '#/definitions/Room'
#         examples:
#           response: [{
#             "uuid": "ABCDEFGHIJKL12345",
#             "name": "b232",
#             "location": "IMT Atlantique",
#             "description": "Room hosting the bouillonantes g5k cluster",
#             "sensor_arrays_uuids": ["EXCFJDKJD1382"]
#           }]
#     """
#     all_rooms = [{
#         "uuid": "ABCDEFGHIJKL12345",
#         "name": "b232",
#         "location": "IMT Atlantique",
#         "description": "Room hosting the bouillonantes g5k cluster",
#         "sensor_arrays_uuids": ["EXCFJDKJD1382"]
#     }]
#     result = all_rooms
#     return jsonify(result)
#
#
# @app.route('/rooms/<room_uuid>')
# def rooms_by_uuid(room_uuid):
#     """Endpoint returning a room (identified by its uuid) in the Seduce infrastructure
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - rooms
#     parameters:
#       - name: room_uuid
#         in: path
#         type: string
#         required: true
#       - name: load_relationships
#         in: query
#         type: boolean
#         default: false
#     responses:
#       200:
#         description: A Room that have the specified uuid
#         schema:
#           $ref: '#/definitions/Room'
#         examples:
#             response: {
#             "uuid": "ABCDEFGHIJKL12345",
#             "name": "b232",
#             "location": "IMT Atlantique",
#             "description": "Room hosting the bouillonantes g5k cluster",
#             "sensor_arrays_uuids": ["EXCFJDKJD1382"]
#           }
#       404:
#         description: No room corresponds to the specified uuid
#     """
#     room = {
#         "uuid": "ABCDEFGHIJKL12345",
#         "name": "b232",
#         "location": "IMT Atlantique",
#         "description": "Room hosting the bouillonantes g5k cluster",
#         "sensor_arrays_uuids": ["EXCFJDKJD1382"]
#     }
#
#     result = room
#     return jsonify(result)
#
#
# @app.route('/sensor_arrays')
# def sensor_arrays():
#     """Endpoint returning a list of the infrastructure's sensor arrays
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - sensor arrays
#     parameters:
#       - name: load_relationships
#         in: query
#         type: boolean
#         default: false
#     responses:
#       200:
#         description: A list of sensor arrays
#         schema:
#             type: "array"
#             items:
#                 $ref: '#/definitions/SensorArray'
#         examples:
#           response: [{
#               "uuid": "EXCFJDKJD1382",
#               "name": "moteino1",
#               "room_uuid": "ABCDEFGHIJKL12345",
#               "description": "Moteino that is in charge of measuring temperature in room B232",
#               "sensors_uuids": ["DKsldkl98329"]
#               }]
#     """
#     all_sensor_arrays = [{
#         "uuid": "EXCFJDKJD1382",
#         "name": "moteino1",
#         "room_uuid": "ABCDEFGHIJKL12345",
#         "description": "Moteino that is in charge of measuring temperature in room B232",
#         "sensors_uuids": ["DKsldkl98329"]
#     }]
#     result = all_sensor_arrays
#     return jsonify(result)
#
#
# @app.route('/sensor_arrays/<sensor_array_uuid>')
# def sensor_arrays_by_uuid(sensor_array_uuid):
#     """Endpoint returning a sensor array (identified by its uuid)
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - sensor arrays
#     parameters:
#       - name: sensor_array_uuid
#         in: path
#         type: string
#         required: true
#       - name: load_relationships
#         in: query
#         type: boolean
#         default: false
#     responses:
#       200:
#         description: A sensor array that have the specified uuid
#         schema:
#           $ref: '#/definitions/SensorArray'
#         examples:
#             response: {
#               "uuid": "EXCFJDKJD1382",
#               "name": "moteino1",
#               "room_uuid": "ABCDEFGHIJKL12345",
#               "description": "Moteino that is in charge of measuring temperature in room B232",
#               "sensors_uuids": ["DKsldkl98329"]
#               }
#       404:
#         description: No room corresponds to the specified uuid
#     """
#     sensor_array = {
#         "uuid": "EXCFJDKJD1382",
#         "name": "moteino1",
#         "room_uuid": "ABCDEFGHIJKL12345",
#         "description": "Moteino that is in charge of measuring temperature in room B232",
#         "sensors_uuids": ["DKsldkl98329"]
#     }
#
#     result = sensor_array
#     return jsonify(result)
#
#
# @app.route('/sensors')
# def sensors():
#     """Endpoint returning a list of the infrastructure's sensors
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - sensors
#     responses:
#       200:
#         description: A list of sensor arrays
#         schema:
#             type: "array"
#             items:
#                 $ref: '#/definitions/Sensor'
#         examples:
#           response: [{
#                 "uuid": "DKsldkl98329",
#                 "name": "AF:CF:EF:B8:77",
#                 "array_uuid": "EXCFJDKJD1382",
#                 "index": 0,
#                 "description": "ds18b20"
#               }]
#     """
#     all_sensors = [{
#         "uuid": "DKsldkl98329",
#         "name": "AF:CF:EF:B8:77",
#         "array_uuid": "EXCFJDKJD1382",
#         "index": 0,
#         "description": "ds18b20"
#     }]
#     result = all_sensors
#     return jsonify(result)
#
#
# @app.route('/sensors/<sensor_uuid>')
# def sensors_by_uuid(sensor_uuid):
#     """Endpoint returning a sensor (identified by its uuid)
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - sensors
#     parameters:
#       - name: sensor_uuid
#         in: path
#         type: string
#         required: true
#     responses:
#       200:
#         description: A sensor array that have the specified uuid
#         schema:
#           $ref: '#/definitions/Sensor'
#         examples:
#             response: {
#                 "uuid": "DKsldkl98329",
#                 "name": "AF:CF:EF:B8:77",
#                 "array_uuid": "EXCFJDKJD1382",
#                 "index": 0,
#                 "description": "ds18b20"
#               }
#       404:
#         description: No room corresponds to the specified uuid
#     """
#     sensor = {
#         "uuid": "DKsldkl98329",
#         "name": "AF:CF:EF:B8:77",
#         "array_uuid": "EXCFJDKJD1382",
#         "index": 0,
#         "description": "ds18b20"
#     }
#
#     result = sensor
#     return jsonify(result)
#
#
# @app.route('/sensors/<sensor_uuid>/measurements')
# def sensors_measurements_by_uuid(sensor_uuid):
#     """Endpoint returning measurements for a sensor (identified by its uuid)
#     This is using data entered in the Seduce configuration.
#     ---
#     tags:
#       - sensors
#     parameters:
#       - name: sensor_uuid
#         in: path
#         type: string
#         required: true
#       - name: start_date
#         in: query
#         type: string
#         required: false
#       - name: end_date
#         in: query
#         type: string
#         required: false
#     responses:
#       200:
#         description: A sensor array that have the specified uuid
#         schema:
#           $ref: '#/definitions/Sensor'
#         examples:
#             response: {"end_date":"'2017-09-22T14:16:11Z'","is_downsampled":false,"sensor_name":"watt_cooler_ext_2","start_date":"'2017-09-22T14:16:07Z'","timestamps":["2017-09-22T14:16:07Z","2017-09-22T14:16:08Z","2017-09-22T14:16:09Z","2017-09-22T14:16:10Z","2017-09-22T14:16:11Z"],"values":[0,0,0,0,0]}
#
#       404:
#         description: No room corresponds to the specified uuid
#     """
#     measurements = {
#         "end_date": "'2017-09-22T14:16:11Z'",
#         "is_downsampled": False,
#         "sensor_name": "watt_cooler_ext_2",
#         "start_date": "'2017-09-22T14:16:07Z'",
#         "timestamps": ["2017-09-22T14:16:07Z",
#                        "2017-09-22T14:16:08Z",
#                        "2017-09-22T14:16:09Z",
#                        "2017-09-22T14:16:10Z",
#                        "2017-09-22T14:16:11Z"],
#         "values": [0,
#                    0,
#                    0,
#                    0,
#                    0]
#     }
#
#     result = measurements
#     return jsonify(result)


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


@app.route('/infrastructure/description/tree')
def infrastructure_tree_description():
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

    from core.data.multitree import get_node_by_id
    from core.data.multitree import get_tree
    root_node_id = "datacenter"
    starting_node = get_node_by_id(root_node_id)
    if starting_node is not None:
        tree = get_tree(starting_node, False)
        return jsonify(tree)
    else:
        return jsonify({"status": "failure", "cause": "'%s' is not a valid node id :-(" % (root_node_id)})

app.run(host="0.0.0.0", debug=True)
