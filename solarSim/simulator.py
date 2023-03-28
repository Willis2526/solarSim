""" The simulator """
import copy
import logging
import queue
import signal
import threading
import time

import yaml
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer

from solarSim import database, dataStores, modules, unreal

logger = logging.getLogger(__name__)


class Simulator:
    """Main sim class"""

    def __init__(self, configFile, simWeather, restServer) -> None:

        self.modules = {
            "inverters": modules.Inverter,
            "feederBreakers": modules.Breaker,
            "transformers": modules.Transformer,
            "mainBreakers": modules.Breaker,
            "checkMeters": modules.Meter
        }
        self.deviceTypes = list(self.modules.keys())
        self.devices = {}
        self.simWeather = simWeather
        self.context = None

        self.unrealService = unreal.UnrealService(restServer)
        self.unrealPollRate = 1

        self.database = database.Database()

        # Load in config file
        try:
            with open(configFile, "r") as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(
                "Config file not found. Generating new file. "
                + "Using default configuration."
            )
            self.config = {
                "devices": {
                    "inverters": [
                        {
                            "name": "inverter1"
                        },
                        {
                            "name": "inverter2"
                        },
                        {
                            "name": "inverter3"
                        },
                        {
                            "name": "inverter4"
                        },
                    ],
                    "feederBreakers": [
                        {
                            "name": "feeder1Breaker",
                            "connections": {
                                "inverters": [
                                    "inverter1",
                                    "inverter2"
                                ]
                            }
                        },
                        {
                            "name": "feeder2Breaker",
                            "connections": {
                                "inverters": [
                                    "inverter3",
                                    "inverter4"
                                ]
                            }
                        },
                    ],
                    "transformers": [
                        {
                            "name": "transformer1",
                            "connections": {
                                "feederBreakers": [
                                    "feeder1Breaker",
                                    "feeder2Breaker"
                                ]
                            }
                        },
                    ],
                    "mainBreakers": [
                        {
                            "name": "mainBreaker1",
                            "connections": {
                                "feederBreakers": [
                                    "feeder1Breaker",
                                    "feeder2Breaker"
                                ],
                                "transformers": [
                                    "transformer1"
                                ]
                            }
                        },
                    ],
                    "checkMeters": [
                        {
                            "name": "checkMeter1"
                        }
                    ]
                },
                "unreal": {
                    "solarPath": ""
                }
            }
            with open(configFile, "w") as file:
                yaml.dump(self.config, file)

        # Generate the device objects
        self.generateDevices()

        self.callbacks = queue.Queue()

        # Setup modbus server identity and context
        identity = ModbusDeviceIdentification()
        identity.VendorName = "Vertech"
        identity.ProductCode = "VerSim"
        identity.VendorUrl = "https://vertech.com/"
        identity.ProductName = "Vertech SoloarSim"
        identity.ModelName = "Vertech SoloarSim"
        identity.MajorMinorRevision = "1.0"

        # Build context depending on the devices in the config
        self.context = dataStores.buildContext(self.devices)

        # Start modbus server thread
        self.msThread = threading.Thread(
            target=StartTcpServer,
            kwargs={
                "context": self.context,
                "identity": identity,
                "address": ("0.0.0.0", 502),
            },
        )
        self.msThread.daemon = True
        self.msThread.name = "modbus_server"
        self.msThread.start()
        logger.info("Modbus server thread started")

        # Start API request thread
        self.unrealThread = threading.Thread(target=self.unrealRequest)
        self.unrealThread.daemon = True
        self.unrealThread.name = "unreal_thread"
        self.unrealThread.start()
        logger.info("Unreal API request thread started")

    def generateDevices(self):
        """Generate the devices from the config file"""
        nextSlaveId = 1

        # Generate device structure
        for deviceGroup in self.config["devices"]:
            self.devices[deviceGroup] = []

            # Instanstiate the device objects
            for device in self.config["devices"][deviceGroup]:
                module = copy.deepcopy(self.modules[deviceGroup])(
                    slaveId=nextSlaveId
                )

                # Set module attributes
                module.config = device
                module.connections = device.get("connections", {})
                module.moduleGroup = deviceGroup
                module.name = device["name"]

                self.devices[deviceGroup].append(module)

                # Increment slave ID for next module
                nextSlaveId += 1

        # Map the input devices for each device. Replace the string
        # representation of the input devices with the actual device objects
        for deviceTypes in self.devices:
            for device in self.devices[deviceTypes]:

                if not device.connections:
                    continue

                connections = {}
                for inputType in device.connections:
                    # Loop through device objects. If the device name is in the
                    # input list, add it to the connections object
                    connections[inputType] = [
                        d for d in self.devices[inputType]
                        if d.name in device.connections[inputType]
                    ]

                device.connections = connections

        # Add in simulator Device
        self.devices["simControl"] = []
        module = modules.SimulationController(slaveId=nextSlaveId)
        module.name = "simControl"
        module.connections["inverters"] = self.devices["inverters"]
        module.connections["meters"] = self.devices["checkMeters"]
        module.connections["breakers"] = self.devices["mainBreakers"]
        module.simWeatherEnabled = self.simWeather
        self.devices["simControl"].append(module)

    def updateDevices(self):
        """Update the inputs of all the devices"""
        for deviceGroup in self.devices:
            for device in self.devices[deviceGroup]:
                device.update()

                # Debug logging
                if device.moduleGroup == "inverters":
                    logger.debug("------------------------")
                    logger.debug(
                        "{} Enabled: {}".format(
                            device.name,
                            device.isEnabled
                        )
                    )
                    logger.debug(
                        "{} Irradiance: {:.2f}".format(
                            device.name,
                            device.irradiance
                        )
                    )
                    logger.debug(
                        "{} Power: {:.2f}".format(
                            device.name,
                            device.realPower
                        )
                    )
                    logger.debug("------------------------")

    def unrealRequest(self):
        """Request the simulation data from Unreal Engine"""
        solarPath = None
        solarPath = self.config.get("unreal", {}).get("solarPath")

        if not solarPath:
            logger.warn(
                "Solar object not defined in config. API request stopped.")
            return

        while True:
            properties = self.unrealService.getProperty(solarPath)
            self.callbacks.put((self.unrealCallback, (properties,)))
            time.sleep(self.unrealPollRate)

    def unrealCallback(self, data):
        """Callback for Unreal Engine Requests"""
        logger.debug("Callback from Unreal: {}".format(data))

    def start(self):
        """Start the sim event loop"""
        signal_handler = SignalHandler()

        while True:
            if signal_handler.stop:
                break

            try:
                # Update devices
                self.updateDevices()

                # Check for callbacks
                callback, args = self.callbacks.get(timeout=1)
                if args:
                    callback(*args)
                else:
                    callback()

                # Task done
                self.callbacks.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                logger.error("Simulation error. %s", e)
                time.sleep(0.5)


class InputNotFoundError(Exception):
    """Custom Exception for a required input not found on a device"""
    pass


class SignalHandler:
    """Handle Signals"""

    def __init__(self):
        self.stop = False

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Callback for signals"""
        self.stop = True
