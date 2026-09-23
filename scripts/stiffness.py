#!/usr/bin/env python
"""wakeUp() (stiffen and stand), wait, then rest() (crouch and go limp)."""
from __future__ import print_function

import time

from common import parse_args, proxies, safe_session


def extra(parser):
    parser.add_argument("--hold", type=float, default=3.0, help="seconds awake")

args = parse_args(__doc__, extra)
p = proxies(args, "ALMotion", "ALRobotPosture")
motion, posture = p["ALMotion"], p["ALRobotPosture"]

with safe_session(motion, wake=False):
    print("wakeUp()")
    motion.wakeUp()
    print("awake: %s, posture: %s" % (motion.robotIsWakeUp(), posture.getPosture()))
    time.sleep(args.hold)
    print("rest()")
    motion.rest()
    print("awake: %s, posture: %s" % (motion.robotIsWakeUp(), posture.getPosture()))
