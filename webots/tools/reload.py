"""Reload the open Webots world (resets the NAO), then exit. Used by tools/trials.sh.

Runs on the Mac with Webots' own Python, as the `truth` supervisor robot (so not while truth.py runs):
    /Applications/Webots.app/Contents/MacOS/webots-controller --robot-name=truth webots/tools/reload.py
Keep naoqisim connected: Webots waits for the NAO's extern controller, so without it the reload
(applied at the next step) never happens. naoqisim exits when the world reloads.
"""
from controller import Supervisor

robot = Supervisor()
robot.worldReload()
robot.step(int(robot.getBasicTimeStep()))  # the reload happens at the next step
