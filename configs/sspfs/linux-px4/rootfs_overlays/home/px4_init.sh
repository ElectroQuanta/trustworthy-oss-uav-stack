#!/bin/sh

PX4_HOME="/home/px4"
PX4_BINARY="${PX4_HOME}/bin/px4"
CONFIG_FILE="${PX4_HOME}/pilotpi_mc.config"

# Check if the binary exists
if [ ! -f "${PX4_BINARY}" ]; then
    echo "Error: PX4 binary not found at ${PX4_BINARY}"
    exit 1
fi

# Check if the configuration file exists
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Error: Configuration file not found at ${CONFIG_FILE}"
    exit 1
fi

# Run the PX4 binary with the specified configuration file
cd "$PX4_HOME" # required to read the parameters.bson
"${PX4_BINARY}" -s "${CONFIG_FILE}"
