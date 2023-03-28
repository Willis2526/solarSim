""" Solar Sim main entry """
import argparse
import logging
import logging.handlers

from .simulator import Simulator

logger = logging.getLogger(__name__)
# Parse the arguments for the options
parser = argparse.ArgumentParser(description="Solar Simulator")
parser.add_argument(
    "--config", "-c", default="config.yaml", type=str, help="Config File"
)
parser.add_argument(
    "--log",
    "-l",
    type=str,
    help="Logging Mode",
    choices=["INFO", "DEBUG"],
    default="INFO",
)
parser.add_argument(
    "--sim", "-s", action="store_true", help="Sim Weather Mode enable"
)
parser.add_argument(
    "--address", "-a", default="localhost", type=str, help="Unreal Rest Address"
)
parser.add_argument(
    "--port", "-p", default=30010, type=int, help="Unreal Rest Port Number"
)
args = parser.parse_args()

# Setup logging
mode = logging.INFO
if args.log == "DEBUG":
    mode = logging.DEBUG

logging.basicConfig(
    level=mode,
    format=(
        "%(asctime)s - %(levelname)-8s - %(name)-20s:%(lineno)5d - "
        "%(message)s"
    ),
)

restServer = "{}:{}".format(args.address, args.port)

server = Simulator(args.config, args.sim, restServer)
server.start()
