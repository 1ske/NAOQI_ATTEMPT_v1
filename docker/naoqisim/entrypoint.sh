#!/bin/sh
# Runs naoqisim as an extern controller of the Webots instance at WEBOTS_CONTROLLER_URL.
# Extra args go to naoqisim before the port, e.g. NAOQISIM_FLAGS=-nocam (the default).
set -e
: "${WEBOTS_CONTROLLER_URL:=tcp://host.docker.internal:1234/NAO}"
: "${NAOQI_PORT:=9559}"
export WEBOTS_CONTROLLER_URL
echo "naoqisim -> ${WEBOTS_CONTROLLER_URL}, NAOqi port ${NAOQI_PORT}"
cd /opt/naoqisim/controllers/naoqisim
exec ./naoqisim ${NAOQISIM_FLAGS} "${NAOQI_PORT}"
