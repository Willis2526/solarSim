""" Modbus Datastores """

import copy
import logging

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)

logger = logging.getLogger(__name__)

# Datastores will be generated depending on the equipment listed in the 
# config file

baseDataStore = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),
    co=ModbusSequentialDataBlock(0, [0] * 100),
    hr=ModbusSequentialDataBlock(0, [0] * 100),
    ir=ModbusSequentialDataBlock(0, [0] * 100),
)

def buildContext(devices):
    """
    Build the modbus context for the given devices.
    Order: 
    inverter -> feederBreaker -> transformer -> mainBreaker -> checkMeter
    """
    slaves = {}

    # Create datastores
    for deviceGroup in devices:
        for device in devices[deviceGroup]:
            slaves[device.slaveId] = copy.deepcopy(baseDataStore)


    context = ModbusServerContext(slaves=slaves, single=False)

    # Add context to all devices
    for deviceGroup in devices:
        for device in devices[deviceGroup]:
            device.modbusContext = context

    return context
