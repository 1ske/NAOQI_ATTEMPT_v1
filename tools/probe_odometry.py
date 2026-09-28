#!/usr/bin/env python
"""Does ALMotion odometry survive a fresh naoqisim start? One trial for tools/trials.sh.

wakeUp -> StandInit (0.5), watching getRobotPosition for NaN; a 0.1 m moveTo that has to change
odometry; rest -> StandInit again. Always ends resting. Last line: RESULT {json} with result one of
OK, NAN_AT_START, NAN_AT_STAND, NO_MOVE, NAN_LATER, FELL, NO_STAND, ERROR.
Sim tooling only (NOTES.md "Emulation stalls"), not a robot script:
    docker compose run --rm -v "$PWD/tools:/tools" client python /tools/probe_odometry.py
"""
from __future__ import print_function

import json
import math
import sys
import time
from datetime import datetime

sys.path.insert(0, "/scripts")  # scripts/common.py, mounted by the client service
from common import MAX_POSTURE_SPEED, parse_args, proxies, safe_session  # noqa: E402

WATCH = 10.0   # s to keep watching odometry after a stand
WALK = 0.1     # m, short test walk
MOVED = 0.03   # m of odometry change that counts as "the walk moved"
T0 = time.time()


def log(msg):
    print("%s +%.1fs %s" % (datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
                            time.time() - T0, msg))
    sys.stdout.flush()


class Failed(Exception):
    def __init__(self, result, **info):
        Exception.__init__(self, result)
        self.result, self.info = result, info


def is_nan(pos):
    return any(math.isnan(v) for v in pos)


def stand_and_watch(motion, posture, phase):
    """StandInit via .post, polling odometry during the transition and WATCH s after it."""
    start = time.time()
    task = posture.post.goToPosture("StandInit", MAX_POSTURE_SPEED)
    done_at = None
    while True:
        pos = motion.getRobotPosition(True)
        if is_nan(pos):
            log("%s: odometry NaN" % phase)
            raise Failed("NAN_AT_STAND" if phase == "stand1" else "NAN_LATER", phase=phase,
                         t_nan=round(time.time() - start, 2))
        if done_at is None and not posture.isRunning(task):
            done_at = time.time()
            log("%s: StandInit done in %.1fs, posture %s" % (phase, done_at - start, posture.getPosture()))
        if done_at is not None and time.time() - done_at > WATCH:
            break
        time.sleep(0.1)
    if posture.getPostureFamily() != "Standing":
        raise Failed("FELL" if motion.robotHasFallen() else "NO_STAND", phase=phase,
                     posture=posture.getPosture())


def trial(motion, posture):
    if is_nan(motion.getRobotPosition(True)):
        raise Failed("NAN_AT_START", phase="start")
    with safe_session(motion):
        log("wakeUp done, posture %s" % posture.getPosture())
        stand_and_watch(motion, posture, "stand1")
        motion.moveInit()
        before = motion.getRobotPosition(True)
        motion.moveTo(WALK, 0.0, 0.0)
        after = motion.getRobotPosition(True)
        if is_nan(after):
            raise Failed("NAN_LATER", phase="walk")
        moved = math.hypot(after[0] - before[0], after[1] - before[1])
        log("walk: odometry moved %.3f m for %.2f m" % (moved, WALK))
        if moved < MOVED:
            raise Failed("NO_MOVE", phase="walk", moved=round(moved, 3))
        if posture.getPostureFamily() != "Standing":
            raise Failed("FELL", phase="walk", posture=posture.getPosture())
        motion.rest()
        log("rest done")
        motion.wakeUp()
        stand_and_watch(motion, posture, "stand2")
    return {"moved": round(moved, 3)}


args = parse_args(__doc__)
p = proxies(args, "ALMotion", "ALRobotPosture")
motion, posture = p["ALMotion"], p["ALRobotPosture"]
log("connected, posture %s" % posture.getPosture())
report = {"result": "OK"}
try:
    report.update(trial(motion, posture))
except Failed as f:
    report["result"] = f.result
    report.update(f.info)
except Exception as e:
    report.update(result="ERROR", error=str(e).strip().splitlines()[-1][:200])
report["seconds"] = round(time.time() - T0, 1)
log("RESULT " + json.dumps(report, sort_keys=True))
