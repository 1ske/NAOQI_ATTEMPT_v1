#!/bin/bash
# Reset the sim until NAOqi's odometry survives: reload the world + fresh naoqisim, run
# tools/probe_odometry.py (stand, 0.1 m walk, rest, stand), repeat until a probe passes.
#   tools/sim_reset.sh [MAX=10]
# Ends with naoqisim running and the robot resting; then start the bridge / your client.
# Every attempt is logged in tools/out/trials.csv with label "reset". Env: see tools/trials.sh.
cd "$(dirname "$0")/.."
UNTIL_OK=1 exec tools/trials.sh "${1:-10}" reset
