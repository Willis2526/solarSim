""" Simulator modules """
import logging
import random
from abc import ABC, ABCMeta, abstractmethod
from math import sqrt

from pymodbus.datastore import ModbusServerContext

logging.getLogger("pymodbus").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

class Module(ABC):
    """The base sim module class"""
    __metaclass__ = ABCMeta

    def __init__(self, slaveId) -> None:
        self.slaveId = slaveId
        self.name = "Module"
        self.moduleGroup = "Modules"
        self.modbusContext = None
        self.connections = {}

        # Config for device will be mapped here for reference
        self.config = {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def update(self):
        """Update values"""
        self.writeModbus(self.modbusContext)

    @abstractmethod
    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        """Write values to modbus registers"""
        raise NotImplementedError(
            "Write function not implemented for %s" % self.name
        )
  
    def readModbus(self, serverContext: ModbusServerContext) -> None:
        """Read from modbus registers"""
        raise NotImplementedError(
            "Read function not implemented for %s" % self.name
        )


class Inverter(Module):
    """Sim inverter module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self.irradiance = 0
        self.realPowerSp = 2000
        self.reactivePowerSp = 0
        self.isEnabled = True
        self.maxRealPower = 2000
        self.maxReactivePower = 1500
        self.voltageL1 = 34
        self.voltageL2 = 34
        self.voltageL3 = 34

    @property
    def realPower(self):
        if self.isEnabled:
            newRealPower = self.irradiance / 950 * self.maxRealPower
            if self.realPowerSp < newRealPower:
                newRealPower = self.realPowerSp
        else:
            newRealPower = 0
        return newRealPower

    @property
    def reactivePower(self):
        if self.isEnabled:
            newReactivePower = self.maxReactivePower
            if self.reactivePowerSp < newReactivePower:
                newReactivePower = self.reactivePowerSp
        else:
            newReactivePower = 0
        return newReactivePower

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [
            self.realPower,
            self.reactivePower,
            self.voltageL1 * 100,
            self.voltageL2 * 100,
            self.voltageL3 * 100,
            self.maxRealPower,
            self.maxReactivePower,
        ]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(4, 1, inputs)

    def readModbus(self, serverContext: ModbusServerContext) -> None:
        holdings = serverContext[self.slaveId].getValues(3, 1, 2)
        coils = serverContext[self.slaveId].getValues(1, 1, 1)
        self.realPowerSp = holdings[0]
        self.reactivePowerSp = holdings[1]
        self.isEnabled = coils[0]


class Meter(Module):
    """Sim meter module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self.realPower = 0
        self.reactivePower = 0
        self.voltageL1 = 0
        self.voltageL2 = 0
        self.voltageL3 = 0
        self.currentL1 = 0
        self.currentL2 = 0
        self.currentL3 = 0
        self.frequency = 60

    @property
    def powerFactor(self):
        """Returns the meter power factor"""
        newPowerFactor = 1
        if self.reactivePower:
            newPowerFactor = (
                abs(self.reactivePower)
                / self.reactivePower
                * self.realPower
                / sqrt(self.realPower**2 + self.reactivePower**2)
            )
        return newPowerFactor

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [
            self.voltageL1 * 100,
            self.voltageL2 * 100,
            self.voltageL3 * 100,
            self.currentL1 * 100,
            self.currentL2 * 100,
            self.currentL3 * 100,
            self.frequency * 100,
            self.realPower,
            self.reactivePower,
            self.powerFactor * 100,
        ]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(4, 1, inputs)


class Breaker(Module):
    """Sim breaker module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self._realPower = 0
        self._reactivePower = 0
        self._voltageL1 = 0
        self._voltageL2 = 0
        self._voltageL3 = 0
        self._frequency = 60
        self.closeCommand = 1
        self.breakers = []
        self.inverters = []
        self.transformers = []

    @property
    def realPower(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._realPower

    @realPower.setter
    def realPower(self, newValue):
        self._realPower = newValue

    @property
    def reactivePower(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._reactivePower

    @reactivePower.setter
    def reactivePower(self, newValue):
        self._reactivePower = newValue

    @property
    def voltageL1(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._voltageL1

    @voltageL1.setter
    def voltageL1(self, newValue):
        self._voltageL1 = newValue

    @property
    def voltageL2(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._voltageL2

    @voltageL2.setter
    def voltageL2(self, newValue):
        self._voltageL2 = newValue

    @property
    def voltageL3(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._voltageL3

    @voltageL3.setter
    def voltageL3(self, newValue):
        self._voltageL3 = newValue

    @property
    def frequency(self):
        if self.isBreakerClosed:
            return 0
        else:
            return self._frequency

    @frequency.setter
    def frequency(self, newValue):
        self._frequency = newValue

    @property
    def isBreakerClosed(self):
        return not self.closeCommand

    @property
    def powerFactor(self):
        newPowerFactor = 1
        if self.reactivePower:
            newPowerFactor = (
                abs(self.reactivePower)
                / self.reactivePower
                * self.realPower
                / sqrt(self.realPower**2 + self.reactivePower**2)
            )
        return newPowerFactor

    def update(self):
        """Update values"""
        self.breakers = self.connections.get("feederBreakers")
        self.inverters = self.connections.get("inverters")
        self.transformers = self.connections.get("transformers")

        CombinedRealPower = 0
        CombinedReactivePower = 0
        CombinedVoltageL1 = 0
        CombinedVoltageL2 = 0
        CombinedVoltageL3 = 0

        if self.moduleGroup == "feederBreakers":
            if not self.inverters:
                return

            for i in self.inverters:
                CombinedRealPower += i.realPower
                CombinedReactivePower += i.reactivePower
                CombinedVoltageL1 += i.voltageL1
                CombinedVoltageL2 += i.voltageL2
                CombinedVoltageL3 += i.voltageL3

            CombinedVoltageL1 = CombinedVoltageL1 / len(self.inverters)
            CombinedVoltageL2 = CombinedVoltageL2 / len(self.inverters)
            CombinedVoltageL3 = CombinedVoltageL3 / len(self.inverters)

            # Update the enable of each of the input inverters
            for i in self.inverters:
                i.isEnabled = self.closeCommand

        if self.moduleGroup == "mainBreakers":
            if not self.breakers:
                return

            for b in self.breakers:
                CombinedRealPower += b.realPower
                CombinedReactivePower += b.reactivePower

            for t in self.transformers:
                CombinedVoltageL1 += t.voltageL1
                CombinedVoltageL2 += t.voltageL2
                CombinedVoltageL3 += t.voltageL3

        # Set power and voltages
        self._realPower = CombinedRealPower
        self._reactivePower = CombinedReactivePower
        self._voltageL1 = CombinedVoltageL1
        self._voltageL2 = CombinedVoltageL2
        self._voltageL3 = CombinedVoltageL3

        self.writeModbus(self.modbusContext)

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [
            self.voltageL1 * 100,
            self.voltageL2 * 100,
            self.voltageL3 * 100,
            self.realPower,
            self.reactivePower,
            self.powerFactor * 100,
            self.frequency * 100,
        ]
        inputs = [int(item) for item in inputs]
        discretes = [self.isBreakerClosed]
        discretes = [int(item) for item in discretes]
        serverContext[self.slaveId].setValues(4, 1, inputs)
        serverContext[self.slaveId].setValues(2, 1, discretes)

    def readModbus(self, serverContext: ModbusServerContext) -> None:
        values = serverContext[self.slaveId].getValues(1, 1, 1)
        self.closeCommand = values[0]


class Transformer(Module):
    """Sim transformer module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self._realPower = 0
        self._reactivePower = 0
        self._voltageL1 = 0
        self._voltageL2 = 0
        self._voltageL3 = 0
        self.ratio = 3.8
        self.breakers = []

    @property
    def realPower(self):
        return self._realPower

    @realPower.setter
    def realPower(self, newValue):
        self._realPower = newValue

    @property
    def reactivePower(self):
        return self._reactivePower

    @reactivePower.setter
    def reactivePower(self, newValue):
        self._reactivePower = newValue

    @property
    def voltageL1(self):
        return self._voltageL1 * self.ratio

    @voltageL1.setter
    def voltageL1(self, newValue):
        self._voltageL1 = newValue

    @property
    def voltageL2(self):
        return self._voltageL2 * self.ratio

    @voltageL2.setter
    def voltageL2(self, newValue):
        self._voltageL2 = newValue

    @property
    def voltageL3(self):
        return self._voltageL3 * self.ratio

    @voltageL3.setter
    def voltageL3(self, newValue):
        self._voltageL3 = newValue

    def get_RealPower(self):
        return self._realPower

    def update(self):
        """Update values"""
        self.breakers = self.connections.get("feederBreakers")

        CombinedRealPower = 0
        CombinedReactivePower = 0
        CombinedVoltageL1 = 0
        CombinedVoltageL2 = 0
        CombinedVoltageL3 = 0

        if not self.breakers:
            return

        for b in self.breakers:
            CombinedRealPower += b.realPower
            CombinedReactivePower += b.reactivePower
            CombinedVoltageL1 += b.voltageL1
            CombinedVoltageL2 += b.voltageL2
            CombinedVoltageL3 += b.voltageL3

        # Set power and voltages
        self._realPower = CombinedRealPower
        self._reactivePower = CombinedReactivePower
        self._voltageL1 = CombinedVoltageL1 / len(self.breakers)
        self._voltageL2 = CombinedVoltageL2 / len(self.breakers)
        self._voltageL3 = CombinedVoltageL3 / len(self.breakers)

        self.writeModbus(self.modbusContext)

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [
            self._realPower,
            self._reactivePower,
            self._voltageL1 * 100,
            self._voltageL2 * 100,
            self._voltageL3 * 100,
            self.realPower,
            self.reactivePower,
            self.voltageL1 * 100,
            self.voltageL2 * 100,
            self.voltageL3 * 100,
        ]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(4, 1, inputs)

    def readModbus(self, serverContext: ModbusServerContext) -> None:
        values = serverContext[self.slaveId].getValues(3, 1, 1)
        self.ratio = values[0]


class MetStation(Module):
    """Sim Met Station Module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self.irradiance = 0
        self.airTemperature = 0

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [self.irradiance, self.airTemperature]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(4, 1, inputs)


class SmsStation(Module):
    """Sim SMS Station Module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self.soilingRatio = 0

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [self.soilingRatio]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(4, 1, inputs)


class SimulationController(Module):
    """Simulation Controller Module"""

    def __init__(self, slaveId) -> None:
        super().__init__(slaveId)
        self.simWeatherEnabled = False
        self.irradiance = 900
        self.poaMax = 1000
        self.poaMin = 0
        self.irradianceDeviation = 20
        self.tempDeviation = 0
        self.voltageStepDifference = 0
        self.acLossRatio = 98
        self.freqDroop = 0
        self.voltageDeviation = 5
        self.voltageHighLimit = 142
        self.voltageLowLimit = 134
        self.weatherState = 0
        self.voltageStepCommand = 0
        self.nominalGridVoltage = 138
        self.voltageEffectPerVar = 0.0005
        self.voltageMaxDeviation = 0.05
        self.voltageChangeFromPlant = 0
        self.reactivePowerMaxDeviation = 25

    def update(self):
        """Update values"""
        mainBreaker = self.connections["breakers"][0]
        checkMeter = self.connections["meters"][0]

        # Update meters and simulate grid
        freqDeviation = 0.1
        freqDeviationMultiplier = random.randint(-100, 100)
        checkMeter.frequency = (
            checkMeter.frequency + 
            self.freqDroop + 
            (freqDeviation * freqDeviationMultiplier / 100)
        )
        checkMeter.voltageL1 = self.nominalGridVoltage
        checkMeter.voltageL2 = self.nominalGridVoltage
        checkMeter.voltageL3 = self.nominalGridVoltage

        # Get reactive power from inverters
        oldReactivePower = 0
        newReactivePower = 0
        for inverter in self.connections["inverters"]:
            oldReactivePower += inverter.reactivePower
            newReactivePower += inverter.reactivePower

        deltaReactivePower = newReactivePower - oldReactivePower

        # Grid voltage logic
        voltageStep = 0
        if self.voltageStepCommand:
            voltageStep = self.voltageStepDifference
            self.voltageStepCommand = False

        voltageChangeFromPlant = (
            deltaReactivePower * 
            (self.acLossRatio/100) * 
            self.voltageEffectPerVar
        )

        voltageDeviationMultiplier = random.randint(-100, 100)
        meterVoltage = (
            checkMeter.voltageL1 + 
            voltageChangeFromPlant + 
            (voltageDeviationMultiplier / 100 * self.voltageMaxDeviation) + 
            voltageStep
        )
        if meterVoltage > self.voltageHighLimit:
            meterVoltage = self.voltageHighLimit
        if meterVoltage < self.voltageLowLimit:
            meterVoltage = self.voltageLowLimit

        #Grid reactive effect
        reactiveDeviationMultiplier = random.randint(-100, 100)
        meterReactivePower = (
            mainBreaker.reactivePower + 
            (
                reactiveDeviationMultiplier / 100 * 
                self.reactivePowerMaxDeviation
            )
        )

        # Update check meter with voltage
        checkMeter.realPower = mainBreaker.realPower
        checkMeter.reactivePower = abs(meterReactivePower)
        checkMeter.voltageL1 = meterVoltage
        checkMeter.voltageL2 = meterVoltage
        checkMeter.voltageL3 = meterVoltage

        # Run weather sim if enabled
        if self.simWeatherEnabled:
            if self.weatherState == 0:
                poaMin = 0
                poaMax = 200
                for i in range(0,60):
                    if random.randint(0,30) == 0:
                        poaDeviationMultiplier = 10
                    else:
                        poaDeviationMultiplier = 1
                    poaDeviation = (
                        random.randint(-10,75) * 
                        self.irradianceDeviation *
                        poaDeviationMultiplier / 100
                    )
                    self.irradiance = self.irradiance + poaDeviation
                    if self.irradiance > poaMax:
                        self.irradiance = poaMax
                    elif self.irradiance < poaMin:
                        self.irradiance = poaMin
                    poaMin = poaMin + 75
                    poaMax = poaMax + 80
                self.weatherState = 1
                
            if self.weatherState == 1:
                poaMin = 800
                poaMax = 950
                if random.randint(0,30) == 0:
                    poaDeviationMultiplier = 10
                else:
                    poaDeviationMultiplier = 1
                poaDeviation = (
                    random.randint(-100,100) *
                    self.irradianceDeviation *
                    poaDeviationMultiplier / 100
                )
                self.irradiance = self.irradiance + poaDeviation
                if self.irradiance > poaMax:
                    self.irradiance = poaMax
                elif self.irradiance < poaMin:
                    self.irradiance = poaMin

            elif self.weatherState == 2:
                poaMin = 300
                poaMax = 950
                if random.randint(0,30) == 0:
                    poaDeviationMultiplier = 40
                else:
                    poaDeviationMultiplier = 10
                poaDeviation = (
                    random.randint(-100,100) *
                    self.irradianceDeviation *
                    poaDeviationMultiplier / 100
                )
                self.irradiance = self.irradiance + poaDeviation
                if self.irradiance > poaMax:
                    self.irradiance = poaMax
                elif self.irradiance < poaMin:
                    self.irradiance = poaMin

            if self.weatherState == 4:
                poaMin = 100
                poaMax = 500
                for i in range(0,60):
                    if random.randint(0,30) == 0:
                        poaDeviationMultiplier = 10
                    else:
                        poaDeviationMultiplier = 1
                    poaDeviation = (
                        random.randint(-10,75) *
                        self.irradianceDeviation *
                        poaDeviationMultiplier / 100
                    )
                    self.irradiance = self.irradiance + poaDeviation
                    if self.irradiance > poaMax:
                        self.irradiance = poaMax
                    elif self.irradiance < poaMin:
                        self.irradiance = poaMin
                    poaMin = poaMin - 75
                    if poaMin < 0:
                        poaMin = 0
                    poaMax = poaMax - 80
                    if poaMax < 0:
                        poaMax = 0
                self.weatherState = 5

            if self.weatherState == 5:
                for i in range(0,30):
                    self.irradiance = 0
                self.weatherState = 0

            # Update the inverters
            for inverter in self.connections["inverters"]:
                inverter.irradiance = self.irradiance + random.randint(-25,25)
                if inverter.irradiance < 0:
                    inverter.irradiance = 0

        self.writeModbus(self.modbusContext)

    def readModbus(self, serverContext: ModbusServerContext) -> None:
        values = serverContext[self.slaveId].getValues(3, 1, 9)
        self.self.irradianceDeviation = values[0]
        self.tempDeviation = values[1]
        self.voltageStepDifference = values[2]
        self.acLossRatio = values[3]
        self.freqDroop = values[4]
        self.voltageDeviation = values[5]
        self.voltageHighLimit = values[6]
        self.voltageLowLimit = values[7]
        self.weatherState = values[8]

        values = serverContext[self.slaveId].getValues(1, 1, 1)
        self.voltageStepCommand = values[0]

    def writeModbus(self, serverContext: ModbusServerContext) -> None:
        inputs = [
            self.irradianceDeviation,
            self.tempDeviation,
            self.voltageStepDifference,
            self.acLossRatio,
            self.freqDroop,
            self.voltageDeviation,
            self.voltageHighLimit,
            self.voltageLowLimit,
            self.weatherState,
            self.voltageStepCommand,
        ]
        inputs = [int(item) for item in inputs]
        serverContext[self.slaveId].setValues(3, 1, inputs)
