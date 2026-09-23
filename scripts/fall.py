#!/usr/bin/env python
"""Wait for a fall, then get back up with goToPosture("Stand").

Polls ALMemory (robotHasFallen) and the posture family instead of subscribing with an
ALBroker callback: a callback needs NAOqi to connect back to this client, which doesn't work
from a Docker container on a Mac to the real robot.
"""
from __future__ import print_function

import time

from common import MAX_POSTURE_SPEED, parse_args, proxies, safe_session

LYING = ("LyingBelly", "LyingBack")


def extra(parser):
    parser.add_argument("--falls", type=int, default=2, help="falls to recover from")
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds per fall")

args = parse_args(__doc__, extra)
p = proxies(args, "ALMotion", "ALRobotPosture", "ALMemory")
motion, posture, memory = p["ALMotion"], p["ALRobotPosture"], p["ALMemory"]


def fallen_value():
    try:
        return memory.getData("robotHasFallen")
    except RuntimeError:  # key only exists after the first fall
        return None

with safe_session(motion):
    posture.goToPosture("Stand", MAX_POSTURE_SPEED)
    for n in range(args.falls):
        before = fallen_value()
        print("fall %d/%d: push the robot over (face down and face up)..." % (n + 1, args.falls))
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            family = posture.getPostureFamily()
            if family in LYING:
                break
            time.sleep(0.2)
        else:
            print("no fall within %.0f s" % args.timeout)
            break
        print("fallen: posture family %s, robotHasFallen %r -> %r"
              % (family, before, fallen_value()))
        time.sleep(2.0)  # let it settle
        motion.wakeUp()  # the fall manager removes stiffness
        ok = posture.goToPosture("Stand", MAX_POSTURE_SPEED)
        print("goToPosture(Stand): %s -> now %s" % (ok, posture.getPosture()))
