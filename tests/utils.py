from core.config.config_loader import load_config
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.smi import instrum, error
from pysnmp.proto.api import v2c
import threading
import yaml
import random
import os
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import StartTlsServer
from pymodbus.server.sync import StartUdpServer
from pymodbus.server.sync import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.framer.socket_framer import ModbusSocketFramer

from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from bin.temperature_registerer import app as temperature_registerer_app
import time
from werkzeug.serving import make_server
from unittest import mock


def _get_influxdb_parameters():
    config_key = "influx_tests"

    return {
        "host": load_config().get(config_key).get("address"),
        "port": load_config().get(config_key).get("port"),
        "user": load_config().get(config_key).get("user"),
        "password": load_config().get(config_key).get("password"),
        "database": load_config().get(config_key).get("db"),
    }


def _get_mock_data_path():
    mock_data_path_candidates = ["./mock_data", "./tests/mock_data"]

    for mock_data_path_candidate in mock_data_path_candidates:
        if os.path.exists(mock_data_path_candidate):
            return mock_data_path_candidate
    return None


def _get_configuration_path():
    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        sensors_file = f"{mock_data_path}/ecotype/snmp.json"

    return sensors_file


def _get_multitree_config():
    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        multitree_file_path = f"{mock_data_path}/multitree.yaml"

    with open(multitree_file_path) as f:
        yaml_as_dict = yaml.load(f)
        result = yaml_as_dict
        return result
    return None


def _load_sensors_arrays_data():
    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        multitree_file_path = f"{mock_data_path}/room_map.yaml"

    with open(multitree_file_path) as f:
        yaml_as_dict = yaml.load(f)
        result = yaml_as_dict
        return result
    return None


def _load_sensors_data():
    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        multitree_file_path = f"{mock_data_path}/sensors.yaml"

    with open(multitree_file_path) as f:
        yaml_as_dict = yaml.load(f)
        result = yaml_as_dict
        return result
    return None


def _get_sensors_by_collect_method(collect_method):
    result = []

    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        sensors_file = f"{mock_data_path}/sensors.yaml"

    with open(sensors_file) as f:
        yaml_as_dict = yaml.load(f)
        # json_as_dict = json.load(f)
        for unit_name, unit_dict in yaml_as_dict.items():
            if unit_name == "classes":
                continue
            for sensor_name, sensor_dict in unit_dict.items():
                if "name" not in sensor_dict:
                    continue
                if sensor_dict.get("method", "ko") == collect_method:
                    generated_sensor_id = "%s.%s" % (unit_name, sensor_name)
                    sensor_dict["generated_sensor_id"] = generated_sensor_id
                    result += [sensor_dict]
    return result


def _get_temperature_sensors_infrastructure():

    mock_data_path = _get_mock_data_path()

    if mock_data_path is None:
        raise Exception("Could not find path for 'mock_data_path' folder")
    else:
        sensors_file = f"{mock_data_path}/sensors.yaml"

    result = {}
    with open(sensors_file) as f:
        sensors = yaml.load(f)
        temperature_sensors = sensors["temperature"]
        for temperature_sensor_name, temperature_sensor in temperature_sensors.items():
            if temperature_sensor.get("exclude_from_rack_temperature_overview", False):
                continue
            rack_side_key = ("%s.%s" % (temperature_sensor.get("rack"), temperature_sensor.get("side"))).lower()
            position = temperature_sensor.get("position")
            if rack_side_key not in result:
                result[rack_side_key] = {
                    "positions": {},
                    "positions_index": {},
                    "rack": rack_side_key,
                    "sensors": []
                }
            result[rack_side_key].get("positions")[temperature_sensor_name] = position
            result[rack_side_key].get("positions_index")[position] = temperature_sensor_name
            sensors = result[rack_side_key].get("sensors")
            sensors += [temperature_sensor_name]
    return result


class FakeSnmpAgent(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self._stop = threading.Event()

        self.snmpEngine = None

    def run(self) -> None:
        self.snmpEngine = engine.SnmpEngine()

        config.addSocketTransport(
            self.snmpEngine,
            udp.domainName,
            udp.UdpTransport().openServerMode(('127.0.0.1', 1161))
        )

        config.addV1System(self.snmpEngine, 'my-area', 'public', contextName='my-context')

        config.addVacmUser(self.snmpEngine, 2, 'my-area', 'noAuthNoPriv', (1, 3, 6), (1, 3, 6))

        snmpContext = context.SnmpContext(self.snmpEngine)

        class SimpleController(instrum.AbstractMibInstrumController):
            def readVars(self, varBinds, acInfo=(None, None)):
                return [(ov[0], v2c.Integer(random.uniform(120, 140))) for ov in varBinds]

        snmpContext.registerContextName(
            v2c.OctetString('my-context'),  # Context Name
            SimpleController()  # Management Instrumentation
        )

        cmdrsp.GetCommandResponder(self.snmpEngine, snmpContext)
        # cmdrsp.SetCommandResponder(self.snmpEngine, snmpContext)

        self.snmpEngine.transportDispatcher.jobStarted(1)

        try:
            self.snmpEngine.transportDispatcher.runDispatcher()
        except:
            self.snmpEngine.transportDispatcher.closeDispatcher()
            raise

    # function using _stop function
    def stop(self):
        self.snmpEngine.transportDispatcher.jobFinished(1)


class FakeModbusAgent(threading.Thread):

    def __init__(self, port=5020, endian="big"):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.port = port
        self._stop = threading.Event()

        if endian.lower() == "big":
            self.endian = Endian.Big
        else:
            self.endian = Endian.Little

        self.snmpEngine = None

    def run(self) -> None:
        builder = BinaryPayloadBuilder(byteorder=self.endian,
                                       wordorder=self.endian)
        builder.add_32bit_uint(42)
        builder.add_16bit_uint(12)
        builder.add_32bit_int(64)
        builder.add_16bit_int(128)
        builder.add_32bit_float(256)

        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(18476, builder.to_registers()),
            co=ModbusSequentialDataBlock(18476, builder.to_registers()),
            hr=ModbusSequentialDataBlock(18476, builder.to_registers()),
            ir=ModbusSequentialDataBlock(18476, builder.to_registers()),
            zero_mode=True
        )

        slaves = {
            0x01: store,
            0x02: store,
            0x03: store,
            0x04: store,
        }

        # context = ModbusServerContext(slaves=store, single=True)
        context = ModbusServerContext(slaves=slaves, single=False)

        identity = ModbusDeviceIdentification()
        identity.VendorName = 'Pymodbus'
        identity.ProductCode = 'PM'
        identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
        identity.ProductName = 'Pymodbus Server'
        identity.ModelName = 'Pymodbus Server'
        identity.MajorMinorRevision = '2.3.0'

        framer = ModbusSocketFramer

        self.server = ModbusTcpServer(context, framer, identity, address=("127.0.0.1", self.port))
        self.server.serve_forever()

    # function using _stop function
    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class FakeTemperatureRegistererAgent(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self._stop = threading.Event()

        self.snmpEngine = None

    def run(self) -> None:
        self.server = make_server('127.0.0.1', 5500, temperature_registerer_app)
        self.ctx = temperature_registerer_app.app_context()
        self.ctx.push()

        self.server.serve_forever()

    # function using _stop function
    def stop(self):
        self.server.shutdown()


def mock_data(function):
    def wrapper(*args, **kwargs):
        with mock.patch('core.data.influx.get_influxdb_parameters', side_effect=_get_influxdb_parameters):
            with mock.patch('core.data.multitree.get_multitree_config', side_effect=_get_multitree_config):
                with mock.patch('core.config.crawlers_config.get_sensors_by_collect_method', side_effect=_get_sensors_by_collect_method):
                    with mock.patch('core.config.room_config.get_temperature_sensors_infrastructure', side_effect=_get_temperature_sensors_infrastructure):
                        with mock.patch('core.data.sensors.load_sensors_arrays_data', side_effect=_load_sensors_arrays_data):
                            with mock.patch('core.data.sensors.load_sensors_data', side_effect=_load_sensors_data):
                                result = function(*args, **kwargs)
                                return result
    return wrapper
