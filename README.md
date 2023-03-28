# Solar Plant Simulator

The Solar Plant Simulator is a Python module that simulates a solar power plant given an input of solar irradiance from Unreal Engine 5. The simulator provides an easy-to-use interface that allows users to configure various parameters of the simulation and monitor its progress. An SQLite database is used to store the simulator configuration. The simulator also provides a modbus server that can be used to communicate with the solar plant.

## Prerequisites

- Python 3.6 or later
- Unreal Engine 5
- Config file in YAML format (default name: `config.yaml`)(optional)

## Installation

1. Create a virtual environment and activate it.
2. Upgrade pip to the latest version using `pip install --upgrade pip`.
3. Install the required dependencies by running `pip install -r requirements.txt`
4. Ensure that Unreal Engine 5 is running either on the same machine or a remote machine. The simulator will connect to the Unreal Engine 5 instance using the REST API.
5. Configure the `config.yaml` file to set up the simulation parameters. Will be automatically created if it does not exist.

## Usage

1. Run the `solarSim` module to start the simulator. Use the following command:
   ```bash
   python -m solarSim *args
   ```

    The following arguments are available:

- `--config` or `-c`: Path to the YAML config file. If not specified, the default file name `config.yaml` will be used.
- `--log` or `-l`: Logging mode. Options are `INFO` (default) or `DEBUG`.
- `--sim` or `-s`: Enable simulation weather mode. This is an optional flag that can be set to True to simulate weather conditions for the solar plant.
- `--address` or `-a`: The address of the Unreal Rest API. Default is `localhost`.
- `--port` or `-p`: The port number of the Unreal Rest API. Default is `30010`.

2. Monitor the progress of the simulation in the terminal or logs. The simulator will output information about the solar plant's power output and other relevant data.

3. A modbus server will be started on the machine running the simulator. The modbus server will be used to communicate with the solar plant. The modbus server will be started on port 502.


