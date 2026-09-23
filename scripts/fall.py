#!/usr/bin/env python
"""Wait for a fall, then try to get back up with goToPosture("Stand").

Polls the posture family and ALMemory robotHasFallen instead of subscribing with an ALBroker
callback: a callback needs NAOqi to connect back to this client, which doesn't work from a
Docker container on a Mac to the real robot.
"""
from __future__ import print_function

import time

from common import MAX_POSTURE_SPEED, clamp, parse_args, proxies, safe_session


def extra(parser):
    parser.add_argument("--falls", type=int, default=2, help="falls to recover from")
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds to wait per fall")
    parser.add_argument("--speed", type=float, default=MAX_POSTURE_SPEED, help="get-up speed")

args = parse_args(__doc__, extra)
speed = clamp(args.speed, MAX_POSTURE_SPEED)
p = proxies(args, "ALMotion", "ALRobotPosture", "ALMemory")
motion, posture, memory = p["ALMotion"], p["ALRobotPosture"], p["ALMemory"]


def fallen_value():
    try:
        return memory.getData("robotHasFallen")
    except RuntimeError:  # key only exists after the first fall
        return None

with safe_session(motion):
    ok = posture.goToPosture("Stand", MAX_POSTURE_SPEED)
    print("start: goToPosture(Stand): %s -> now %s" % (ok, posture.getPosture()))
    for n in range(args.falls):
        print("fall %d/%d: push the robot over (face down and face up)..." % (n + 1, args.falls))
        deadline = time.time() + args.timeout
        while time.time() < deadline and posture.getPostureFamily() == "Standing":
            time.sleep(0.2)
        if posture.getPostureFamily() == "Standing":
            print("no fall within %.0f s" % args.timeout)
            break
        time.sleep(3.0)  # let it settle
        print("fallen: posture family %s (%s), robotHasFallen %r"
              % (posture.getPostureFamily(), posture.getPosture(), fallen_value()))
        motion.wakeUp()  # the fall manager removes stiffness
        ok = posture.goToPosture("Stand", speed)
        print("goToPosture(Stand, %.1f): %s -> now %s" % (speed, ok, posture.getPosture()))
        if not ok:
            print("could not get up, stopping")
            break
