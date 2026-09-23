#!/usr/bin/env python
"""Go through postures (default StandInit, Stand, Crouch) and report each result."""
from __future__ import print_function

import time

from common import MAX_POSTURE_SPEED, clamp, parse_args, proxies, safe_session


def extra(parser):
    parser.add_argument("--postures", nargs="+", default=["StandInit", "Stand", "Crouch"])
    parser.add_argument("--speed", type=float, default=0.5)

args = parse_args(__doc__, extra)
speed = clamp(args.speed, MAX_POSTURE_SPEED)
p = proxies(args, "ALMotion", "ALRobotPosture")
motion, posture = p["ALMotion"], p["ALRobotPosture"]

with safe_session(motion):
    for name in args.postures:
        ok = posture.goToPosture(name, speed)
        print("goToPosture(%s): %s -> now %s" % (name, ok, posture.getPosture()))
        time.sleep(1.0)
