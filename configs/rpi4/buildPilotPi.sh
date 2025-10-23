#!/bin/sh

PX4_DIR=Autopilot
PX4_BRANCH=v1.14.0
PX4_VENV=px4-venv

# Download Autopilot
git clone https://github.com/PX4/PX4-Autopilot.git "$PX4_DIR" \
	--branch "$PX4_BRANCH" --recursive
git submodule sync --recursive
git submodule update --recursive
# Setup virtual environment for the build
python3 -m venv "$PX4_VENV"
source "$PX4_VENV/bin/activate"
# Build PX4 for PilotPi
make -C "$PX4_DIR" scumaker_pilotpi_arm64
# Upload PX4 to PilotPi
export autopilot_host=192.168.1.55
export autopilot_user=pilotpi
make -C "$PX4_DIR" scumaker_pilotpi_arm64 upload # to host 
make -C "$PX4_DIR" scumaker_pilotpi_arm64 upload_local_br # to local buildroot
