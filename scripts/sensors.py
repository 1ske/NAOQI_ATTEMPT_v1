#!/usr/bin/env python
"""Print sonar, foot bumpers and inertial angles once per --period. Doesn't move the robot."""
from __future__ import print_function

import time

from common import parse_args, proxies

D = "Device/SubDeviceList/"
KEYS = [
    ("sonarL", D + "US/Left/Sensor/Value"),
    ("sonarR", D + "US/Right/Sensor/Value"),
    ("LF.bL", D + "LFoot/Bumper/Left/Sensor/Value"),
    ("LF.bR", D + "LFoot/Bumper/Right/Sensor/Value"),
    ("RF.bL", D + "RFoot/Bumper/Left/Sensor/Value"),
    ("RF.bR", D + "RFoot/Bumper/Right/Sensor/Value"),
    ("angX", D + "InertialSensor/AngleX/Sensor/Value"),
    ("angY", D + "InertialSensor/AngleY/Sensor/Value"),
]
NAME = "naoqi_basics_sensors"


def extra(parser):
    parser.add_argument("--duration", type=float, default=20.0, help="seconds")
    parser.add_argument("--period", type=float, default=1.0, help="seconds")

args = parse_args(__doc__, extra)
p = proxies(args, "ALSonar", "ALMemory")
sonar, memory = p["ALSonar"], p["ALMemory"]

sonar.subscribe(NAME)
try:
    print("  ".join("%7s" % label for label, _ in KEYS))
    end = time.time() + args.duration
    while time.time() < end:
        values = memory.getListData([key for _, key in KEYS])
        print("  ".join("%7.3f" % (v if v is not None else float("nan")) for v in values))
        time.sleep(args.period)
except KeyboardInterrupt:
    pass
finally:
    sonar.unsubscribe(NAME)
