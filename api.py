from flask import Flask, jsonify
from flasgger import Swagger
from core.data.db import *

app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Seduce API',
    'uiversion': 3
}
swagger = Swagger(app)


@app.route('/infrastructure')
def infrastructure():
    """Endpoint returning a complete view of the infrastructure
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - infrastructure
    definitions:
      Infrastructure:
        type: object
        properties:
          name:
            type: string
          rooms:
            type: array
            items:
              $ref: '#/definitions/Room'
      Room:
        type: object
        properties:
          uuid:
            type: string
          name:
            type: string
          location:
            type: string
          description:
            type: string
          sensor_arrays:
            type: array
            items:
              $ref: '#/definitions/SensorArray'
          sensor_arrays_uuids:
            type: array
            items:
              type: string
      SensorArray:
        type: object
        properties:
          uuid:
            type: string
          name:
            type: string
          room_uuid:
            type: string
          description:
            type: string
          sensors:
            type: array
            items:
              $ref: '#/definitions/Sensor'
          sensors_uuids:
            type: array
            items:
              type: string
      Sensor:
        type: object
        properties:
          uuid:
            type: string
          name:
            type: string
          location:
            type: string
          description:
            type: string
          sensors_arrays:
            type: array
            items:
              $ref: '#/definitions/SensorArray'
    responses:
      200:
        description: A description of the infrastructure
        schema:
          $ref: '#/definitions/Infrastructure'
        examples:
          response: [{
            "uuid": "ABCDEFGHIJKL12345",
            "name": "b232",
            "location": "IMT Atlantique",
            "description": "Room hosting the bouillonantes g5k cluster",
            "sensor_arrays": [{
              "uuid": "EXCFJDKJD1382",
              "name": "moteino1",
              "room_uuid": "ABCDEFGHIJKL12345",
              "description": "Moteino that is in charge of measuring temperature in room B232",
              "sensors": [{
                "uuid": "DKsldkl98329",
                "name": "AF:CF:EF:B8:77",
                "array_uuid": "EXCFJDKJD1382",
                "index": 0,
                "description": "ds18b20"
              }]
            }]
          }]
    """
    all_rooms = [{
        "uuid": "ABCDEFGHIJKL12345",
        "name": "b232",
        "location": "IMT Atlantique",
        "description": "Room hosting the bouillonantes g5k cluster",
        "sensor_arrays": [{
            "uuid": "EXCFJDKJD1382",
            "name": "moteino1",
            "room_uuid": "ABCDEFGHIJKL12345",
            "description": "Moteino that is in charge of measuring temperature in room B232",
            "sensors": [{
                "uuid": "DKsldkl98329",
                "name": "AF:CF:EF:B8:77",
                "array_uuid": "EXCFJDKJD1382",
                "index": 0,
                "description": "ds18b20"
            }]
        }]
    }]
    result = all_rooms
    return jsonify(result)


@app.route('/rooms')
def rooms():
    """Endpoint returning a list of the infrastructure's rooms
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - rooms
    parameters:
      - name: load_relationships
        in: query
        type: boolean
        default: false
    responses:
      200:
        description: A list of rooms
        schema:
            type: "array"
            items:
                $ref: '#/definitions/Room'
        examples:
          response: [{
            "uuid": "ABCDEFGHIJKL12345",
            "name": "b232",
            "location": "IMT Atlantique",
            "description": "Room hosting the bouillonantes g5k cluster",
            "sensor_arrays_uuids": ["EXCFJDKJD1382"]
          }]
    """
    all_rooms = [{
        "uuid": "ABCDEFGHIJKL12345",
        "name": "b232",
        "location": "IMT Atlantique",
        "description": "Room hosting the bouillonantes g5k cluster",
        "sensor_arrays_uuids": ["EXCFJDKJD1382"]
    }]
    result = all_rooms
    return jsonify(result)


@app.route('/rooms/<room_uuid>')
def rooms_by_uuid(room_uuid):
    """Endpoint returning a room (identified by its uuid) in the Seduce infrastructure
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - rooms
    parameters:
      - name: room_uuid
        in: path
        type: string
        required: true
      - name: load_relationships
        in: query
        type: boolean
        default: false
    responses:
      200:
        description: A Room that have the specified uuid
        schema:
          $ref: '#/definitions/Room'
        examples:
            response: {
            "uuid": "ABCDEFGHIJKL12345",
            "name": "b232",
            "location": "IMT Atlantique",
            "description": "Room hosting the bouillonantes g5k cluster",
            "sensor_arrays_uuids": ["EXCFJDKJD1382"]
          }
      404:
        description: No room corresponds to the specified uuid
    """
    room = {
        "uuid": "ABCDEFGHIJKL12345",
        "name": "b232",
        "location": "IMT Atlantique",
        "description": "Room hosting the bouillonantes g5k cluster",
        "sensor_arrays_uuids": ["EXCFJDKJD1382"]
    }

    result = room
    return jsonify(result)


@app.route('/sensor_arrays')
def sensor_arrays():
    """Endpoint returning a list of the infrastructure's sensor arrays
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensor arrays
    parameters:
      - name: load_relationships
        in: query
        type: boolean
        default: false
    responses:
      200:
        description: A list of sensor arrays
        schema:
            type: "array"
            items:
                $ref: '#/definitions/SensorArray'
        examples:
          response: [{
              "uuid": "EXCFJDKJD1382",
              "name": "moteino1",
              "room_uuid": "ABCDEFGHIJKL12345",
              "description": "Moteino that is in charge of measuring temperature in room B232",
              "sensors_uuids": ["DKsldkl98329"]
              }]
    """
    all_sensor_arrays = [{
        "uuid": "EXCFJDKJD1382",
        "name": "moteino1",
        "room_uuid": "ABCDEFGHIJKL12345",
        "description": "Moteino that is in charge of measuring temperature in room B232",
        "sensors_uuids": ["DKsldkl98329"]
    }]
    result = all_sensor_arrays
    return jsonify(result)


@app.route('/sensor_arrays/<sensor_array_uuid>')
def sensor_arrays_by_uuid(sensor_array_uuid):
    """Endpoint returning a sensor array (identified by its uuid)
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensor arrays
    parameters:
      - name: sensor_array_uuid
        in: path
        type: string
        required: true
      - name: load_relationships
        in: query
        type: boolean
        default: false
    responses:
      200:
        description: A sensor array that have the specified uuid
        schema:
          $ref: '#/definitions/SensorArray'
        examples:
            response: {
              "uuid": "EXCFJDKJD1382",
              "name": "moteino1",
              "room_uuid": "ABCDEFGHIJKL12345",
              "description": "Moteino that is in charge of measuring temperature in room B232",
              "sensors_uuids": ["DKsldkl98329"]
              }
      404:
        description: No room corresponds to the specified uuid
    """
    sensor_array = {
        "uuid": "EXCFJDKJD1382",
        "name": "moteino1",
        "room_uuid": "ABCDEFGHIJKL12345",
        "description": "Moteino that is in charge of measuring temperature in room B232",
        "sensors_uuids": ["DKsldkl98329"]
    }

    result = sensor_array
    return jsonify(result)


@app.route('/sensors')
def sensors():
    """Endpoint returning a list of the infrastructure's sensors
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
    responses:
      200:
        description: A list of sensor arrays
        schema:
            type: "array"
            items:
                $ref: '#/definitions/Sensor'
        examples:
          response: [{
                "uuid": "DKsldkl98329",
                "name": "AF:CF:EF:B8:77",
                "array_uuid": "EXCFJDKJD1382",
                "index": 0,
                "description": "ds18b20"
              }]
    """
    all_sensors = [{
        "uuid": "DKsldkl98329",
        "name": "AF:CF:EF:B8:77",
        "array_uuid": "EXCFJDKJD1382",
        "index": 0,
        "description": "ds18b20"
    }]
    result = all_sensors
    return jsonify(result)


@app.route('/sensors/<sensor_uuid>')
def sensors_by_uuid(sensor_uuid):
    """Endpoint returning a sensor (identified by its uuid)
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
    parameters:
      - name: sensor_uuid
        in: path
        type: string
        required: true
    responses:
      200:
        description: A sensor array that have the specified uuid
        schema:
          $ref: '#/definitions/Sensor'
        examples:
            response: {
                "uuid": "DKsldkl98329",
                "name": "AF:CF:EF:B8:77",
                "array_uuid": "EXCFJDKJD1382",
                "index": 0,
                "description": "ds18b20"
              }
      404:
        description: No room corresponds to the specified uuid
    """
    sensor = {
        "uuid": "DKsldkl98329",
        "name": "AF:CF:EF:B8:77",
        "array_uuid": "EXCFJDKJD1382",
        "index": 0,
        "description": "ds18b20"
    }

    result = sensor
    return jsonify(result)


@app.route('/sensors/<sensor_uuid>/measurements')
def sensors_measurements_by_uuid(sensor_uuid):
    """Endpoint returning measurements for a sensor (identified by its uuid)
    This is using data entered in the Seduce configuration.
    ---
    tags:
      - sensors
    parameters:
      - name: sensor_uuid
        in: path
        type: string
        required: true
      - name: start_date
        in: query
        type: string
        required: false
      - name: end_date
        in: query
        type: string
        required: false
    responses:
      200:
        description: A sensor array that have the specified uuid
        schema:
          $ref: '#/definitions/Sensor'
        examples:
            response: {"end_date":"'2017-09-22T14:16:11Z'","is_downsampled":false,"sensor_name":"watt_cooler_ext_2","start_date":"'2017-09-22T14:16:07Z'","timestamps":["2017-09-22T14:16:07Z","2017-09-22T14:16:08Z","2017-09-22T14:16:09Z","2017-09-22T14:16:10Z","2017-09-22T14:16:11Z"],"values":[0,0,0,0,0]}

      404:
        description: No room corresponds to the specified uuid
    """
    measurements = {
        "end_date": "'2017-09-22T14:16:11Z'",
        "is_downsampled": False,
        "sensor_name": "watt_cooler_ext_2",
        "start_date": "'2017-09-22T14:16:07Z'",
        "timestamps": ["2017-09-22T14:16:07Z",
                       "2017-09-22T14:16:08Z",
                       "2017-09-22T14:16:09Z",
                       "2017-09-22T14:16:10Z",
                       "2017-09-22T14:16:11Z"],
        "values": [0,
                   0,
                   0,
                   0,
                   0]
    }

    result = measurements
    return jsonify(result)


app.run(host="0.0.0.0", debug=True)
