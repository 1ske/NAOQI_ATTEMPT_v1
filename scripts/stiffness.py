#!/usr/bin/env python
"""wakeUp() and stand, wait, then rest() (crouch and go limp).

On a NAO H25, wakeUp() only turns stiffness on and keeps the current pose, so we go to
StandInit explicitly.
"""
from __future__ import print_function

import time

from common import MAX_POSTURE_SPEED, parse_args, proxies, safe_session


def extra(parser):
    parser.add_argument("--hold", type=float, default=3.0, help="seconds awake")

args = parse_args(__doc__, extra)
p = proxies(args, "ALMotion", "ALRobotPosture")
motion, posture = p["ALMotion"], p["ALRobotPosture"]

with safe_session(motion, wake=False):
    print("wakeUp()")
    motion.wakeUp()
    print("awake: %s, posture: %s" % (motion.robotIsWakeUp(), posture.getPosture()))
    print("goToPosture(StandInit): %s" % posture.goToPosture("StandInit", MAX_POSTURE_SPEED))
    print("awake: %s, posture: %s" % (motion.robotIsWakeUp(), posture.getPosture()))
    time.sleep(args.hold)
    print("rest()")
    motion.rest()
    print("awake: %s, posture: %s" % (motion.robotIsWakeUp(), posture.getPosture()))
