#!/usr/bin/env python
"""moveTo(x, y, theta) --repeat times, printing odometry for each walk.

Check in Webots: --x 0.5 --repeat 3 walks ~0.5 m each time without falling;
--x 0 --theta 1.57 turns ~90 degrees.
"""
from __future__ import print_function

import math

from common import parse_args, proxies, safe_session

MAX_DISTANCE = 1.0  # m per moveTo, keep walks short


def extra(parser):
    parser.add_argument("--x", type=float, default=0.5, help="m forward")
    parser.add_argument("--y", type=float, default=0.0, help="m left")
    parser.add_argument("--theta", type=float, default=0.0, help="rad, counter-clockwise")
    parser.add_argument("--repeat", type=int, default=1)

args = parse_args(__doc__, extra)
if math.hypot(args.x, args.y) > MAX_DISTANCE:
    raise SystemExit("refusing to walk more than %.1f m in one moveTo" % MAX_DISTANCE)
p = proxies(args, "ALMotion", "ALRobotPosture")
motion, posture = p["ALMotion"], p["ALRobotPosture"]
if any(math.isnan(v) for v in motion.getRobotPosition(True)):
    # seen with naoqisim under emulation after a HAL stall (NOTES.md); the walk won't move
    raise SystemExit("ALMotion odometry is NaN, the walk would not move: restart NAOqi")

with safe_session(motion):
    if not posture.goToPosture("StandInit", 0.5) or posture.getPostureFamily() != "Standing":
        raise SystemExit("could not reach StandInit (now %s), not walking" % posture.getPosture())
    motion.moveInit()
    for i in range(args.repeat):
        start = motion.getRobotPosition(True)
        ok = motion.moveTo(args.x, args.y, args.theta)
        end = motion.getRobotPosition(True)
        dx, dy = end[0] - start[0], end[1] - start[1]
        dtheta = math.atan2(math.sin(end[2] - start[2]), math.cos(end[2] - start[2]))
        family = posture.getPostureFamily()
        print("walk %d/%d: moveTo=%s  odometry %.2f m, %.1f deg  posture family %s"
              % (i + 1, args.repeat, ok, math.hypot(dx, dy), math.degrees(dtheta), family))
        if family != "Standing":
            print("not standing any more, stopping")
            break
    motion.stopMove()
