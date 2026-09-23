#!/usr/bin/env python
"""Move the head through a few targets and compare commanded vs measured angles.

Only the head is stiffened (robot can sit or hang in a harness); --wake stands it up first.
"""
from __future__ import print_function

import time

from common import MAX_JOINT_SPEED, clamp, parse_args, proxies, safe_session

NAMES = ["HeadYaw", "HeadPitch"]
TARGETS = [(0.5, 0.0), (-0.5, 0.0), (0.0, -0.3), (0.0, 0.3), (0.0, 0.0)]  # rad


def extra(parser):
    parser.add_argument("--speed", type=float, default=0.2)
    parser.add_argument("--wake", action="store_true", help="wakeUp() the whole body first")

args = parse_args(__doc__, extra)
speed = clamp(args.speed, MAX_JOINT_SPEED)
motion = proxies(args, "ALMotion")["ALMotion"]

with safe_session(motion, wake=args.wake):
    motion.stiffnessInterpolation("Head", 1.0, 0.5)
    for yaw, pitch in TARGETS:
        motion.setAngles(NAMES, [yaw, pitch], speed)
        time.sleep(2.0)
        measured = motion.getAngles(NAMES, True)
        print("target yaw %+.2f pitch %+.2f  measured yaw %+.2f pitch %+.2f"
              % (yaw, pitch, measured[0], measured[1]))
