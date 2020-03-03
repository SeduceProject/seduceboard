import yaml
import traceback
from pymodbus.client.sync import ModbusTcpClient

COMMANDS = None


def load_sensors_data():
    # global COMMANDS
    COMMANDS = None
    if COMMANDS is None:
        with open("conf/commands.yaml") as f:
            COMMANDS = yaml.load(f)
    return COMMANDS


def get_commands_arrays():
    commands_data = load_sensors_data()
    result = dict([(k, v) for k, v in commands_data.items() if k != "classes"])
    return result


def modbus_action(how):
    try:
        client = ModbusTcpClient(how.get("ip"), port=how.get("port"))
        client.connect()
        value = client.write_register(how.get("register"), how.get("value"))
    except:
        print("no connexion")
        traceback.print_exc()

    return True


def read_modbus_property(how):
    from bin.modbus_crawler import new_modbus_reading
    from pymodbus.payload import BinaryPayloadDecoder

    data_type = how.get("type")

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
    elif data_type == "bool":
        read_count_bytes = 1
    else:
        raise Exception(f"Could not understand how to parse the following data_type '{data_type}'")

    client = ModbusTcpClient(how.get("ip"), port=how.get("port"))
    client.connect()

    if how.get("type") != "bool":
        value = client.read_holding_registers(how.get("register"), read_count_bytes, unit=1)
    else:
        value = client.read_holding_registers(how.get("register"), read_count_bytes, unit=1)
    client.close()

    # Default byte order
    default_byteorder = '<'
    default_wordorder = '<'

    byteorder = how.get("byteorder", default_byteorder)
    wordorder = how.get("wordorder", default_wordorder)

    if not hasattr(value, "registers"):
        print(f"ERROR with reading: {how}")

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
    elif data_type == "bool":
        decode_func = decoder.decode_16bit_uint()
    else:
        raise Exception(f"Could not understand how to parse the following data_type '{data_type}'")

    decoded = decode_func

    for value, value_dict in how.get("values", {}).items():

        expected_value = value_dict.get("expected_value")
        if expected_value == decoded:
            return value

    return decode_func

