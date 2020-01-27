from __future__ import absolute_import, unicode_literals

import threading
import time
import traceback
from pyModbusTCP.client import ModbusClient
from pymodbus.client.sync import ModbusTcpClient

from core.data.influx import get_influxdb_client
from core.collecters.utils import set_interval
from pymodbus.payload import BinaryPayloadDecoder

DEBUG = True
LAST_TIMESTAMP_INSERTED = {}


def modbus_read_int(client, address, nb_char):
    result = 0
    regs = client.read_holding_registers(address, nb_char)
    if regs:
        factor = len(regs)
        for i in range(0, len(regs)):
            factor -= 1
            result += regs[i] * (2 ** (factor * 16))
        return result
    else:
        return -1


def new_modbus_reading(config):
    db_client = get_influxdb_client()

    modbus_ip = config.get("ip")
    modbus_port = config.get("port", 502)
    modbus_register = config.get("register")

    sensor_name = config.get("name", config["generated_sensor_id"])
    sensor_type = config.get("sensor_type")
    data_type = config.get("type")
    sensor_unit = config.get("unit")
    sensor_location = config.get("location", "not specified")
    divide_factor = config.get("modbus_divide_by", 1)
    multiply_factor = config.get("modbus_multiply_by", 1)

    insertion_count = 0

    # modbus_client = ModbusClient(host=modbus_ip, port=modbus_port, auto_open=True, auto_close=True)

    read_count_bytes = 0
    if data_type == "float32":
        read_count_bytes = 2
    elif data_type == "int32":
        read_count_bytes = 2
    elif data_type == "uint32":
        read_count_bytes = 2
    elif data_type == "int16":
        read_count_bytes = 1
    elif data_type == "uint16":
        read_count_bytes = 1
    else:
        raise Exception(f"Could not understand how to parse the following data_type '{data_type}'")

    client = ModbusTcpClient(modbus_ip, port=modbus_port)
    client.connect()

    value = client.read_holding_registers(modbus_register, read_count_bytes, unit=1)
    client.close()

    # Default byte order
    default_byteorder = '<'
    default_wordorder = '<'

    byteorder = config.get("byteorder", default_byteorder)
    wordorder = config.get("wordorder", default_wordorder)

    decoder = BinaryPayloadDecoder.fromRegisters(value.registers, byteorder=byteorder, wordorder=wordorder)

    decode_func = None
    if data_type == "float32":
        decode_func = decoder.decode_32bit_float()
    elif data_type == "int16":
        decode_func = decoder.decode_16bit_int()
    elif data_type == "uint16":
        decode_func = decoder.decode_16bit_uint()
    elif data_type == "int32":
        decode_func = decoder.decode_32bit_int()
    elif data_type == "uint32":
        decode_func = decoder.decode_32bit_uint()
    else:
        raise Exception(f"Could not understand how to parse the following data_type '{data_type}'")

    decoded = {
        f'{sensor_name}': decode_func
    }

    try:
        sensor_value = 1.0 * multiply_factor * decode_func / divide_factor
    except:
        traceback.print_exc()
        print("[%s] failed to read a value from socomec (%s:%s:%s)" % (sensor_name,
                                                                       modbus_ip,
                                                                       sensor_unit,
                                                                       modbus_register))
        return {"status": "failure", "reason": "could not read socomec (%s:%s:%s)" % (modbus_ip,
                                                                                      sensor_unit,
                                                                                      modbus_register)}
    if sensor_value is None:
        print("[%s] failed to read an accurate value (%s)"
              " from socomec (%s:%s)" % (sensor_name,
                                            sensor_value,
                                            modbus_ip,
                                            modbus_register))
        return {"status": "failure",
                "reason": "failed to read an accurate (%s) value"
                          " from socomec (%s:%s:%s)" % (sensor_name,
                                                        modbus_ip,
                                                        modbus_register)}

    data = [{
        "measurement": "sensors",
        "fields": {
            "value": float(sensor_value)
        },
        "tags": {
            "location": sensor_location,
            "sensor": sensor_name,
            "unit": sensor_unit,
            "sensor_type": sensor_type
        }
    }]

    try:
        failure = not db_client.write_points(data, time_precision="s")
    except :
        traceback.print_exc()
        failure = True

    db_client.close()

    if failure:
        print("[%s] failed to insert rows in the database" % (sensor_name))
        return {"status": "failure", "reason": "could not write in the DB"}
    else:
        insertion_count += 1

    print("[%s] %s rows have been inserted in the database" % (sensor_name, insertion_count))
    return {"status": "success", "update_count": insertion_count}


if __name__ == "__main__":
    from core.config.crawlers_config import get_modbus_sensors

    modbus_readers = []
    for config in get_modbus_sensors():
        modbus_readers += [set_interval(new_modbus_reading, (config, ), 1)]

        # To prevent all sensors to crawl in parallel
        time.sleep(2)

    try:
        for modbus_reader in modbus_readers:
            modbus_reader.join()
    except:
        for modbus_reader in modbus_readers:
            modbus_reader.stop()
