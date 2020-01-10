#!/usr/bin/env python

import unittest
from tests.test_snmp_collecter import *
from tests.test_sensors_collecters import *
from tests.test_modbus_collecters import *
from tests.test_temperature_registerer import *
from tests.test_influx import *
from tests.test_multitree_influx import *
from tests.test_cq_aggregates import *
from tests.test_webapp import *
from tests.test_webapp_api import *


if __name__ == '__main__':
    unittest.main()
