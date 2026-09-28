# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python 2.7 scripts that drive a NAO robot through NAOqi 2.1.4. The same scripts run against a Webots-simulated NAO and a real NAO V5; only `--ip` changes. The scripts are probes and smoke tests: NAOqi does the actual control (walking, balance, falls, IK). The scripts are clients over TCP :9559.

```
Mac: Webots R2025a (webots/worlds/nao_flat.wbt, NAO controller "<extern>")
       ▲ extern-controller link, tcp://host.docker.internal:1234/NAO
Docker (linux/amd64, emulated via Rosetta on Apple Silicon):
  naoqisim  NAOqi 2.1.4 running as a Webots controller, serves :9559
       ▲
  client    Python 2.7 + pynaoqi 2.1.4.13, mounts ./scripts at /scripts
```

## Commands

There is no build step, linter or test suite. "Testing" means running a script against the sim or the robot.

```sh
# 1. open webots/worlds/nao_flat.wbt in Webots, real-time mode
docker compose up naoqisim                      # wait for "NAOqi is ready" (~1 min under emulation)
NAOQISIM_FLAGS=-nocam docker compose up naoqisim # same, cameras disabled (slightly faster sim)
NAOQISIM_IMU_DEBUG=1 docker compose up naoqisim # log IMU/FSR once per sim second

docker compose run --rm client python connect.py          # single script; every script has --help
docker compose run --rm client python walk.py --x 0.5 --repeat 3
docker compose run --rm client python connect.py --ip 192.168.1.20   # real robot
```

`NAO_IP` defaults to `naoqisim` inside the client container. To reset the robot, reload the world in Webots and restart naoqisim.

Ground truth (Webots supervisor, not NAOqi's estimate), on the Mac:
```sh
WEBOTS_HOME=/Applications/Webots.app /Applications/Webots.app/Contents/MacOS/webots-controller \
    --robot-name=truth webots/tools/truth.py
```

## Code conventions

- **Python 2.7 only** (pynaoqi 2.1 has no Python 3 build). Use `from __future__ import print_function`. Use `%` formatting, not f-strings. Don't use py3-only stdlib.
- Every script uses `scripts/common.py`: `parse_args(__doc__, extra)` for `--ip/--port`, `proxies(args, "ALMotion", ...)` for NAOqi modules, and `with safe_session(motion):` around any motion.
- The module docstring is also the `--help` text. It says what to check in Webots.

## Safety rules (enforced in `common.py`, must be kept)

- Never disable the fall manager or foot-contact protection.
- Joint `fractionMaxSpeed` ≤ `MAX_JOINT_SPEED` (0.3), posture speed ≤ `MAX_POSTURE_SPEED` (0.5). Pass speeds through `clamp()`.
- Moving scripts must end limp and resting on every exit path, including errors and Ctrl-C. That's what `safe_session` is for.
- No keyframe/`.motion` replay on the real robot: those files need joint speeds the V5 can't do.
- Real-robot order: connect/sensors (motors off) → stiffness/head (suspended) → posture (spotter) → walk ≤ 0.2 m then up to 0.5 m.

## naoqisim specifics

- `docker/naoqisim/Dockerfile` builds naoqisim (pinned `f4c167c`) on Ubuntu 22.04 + Webots R2025a Linux, and applies `docker/naoqisim/patches/*.patch`: PROTO model name, IMU angles from accelerometer+gyro, skipping NaN sensor samples before the first reading, and sending sensor values before NAOqi starts (without that, ALMotion's odometry went NaN at startup). NOTES.md explains each patch.
- The simulator SDK tarball (275 MB) goes in `docker/naoqisim/vendor/`. It's git-ignored and downloaded with a checksum check if missing.
- Not available in naoqisim: ALSystem, ALNavigation, ALLocalization, ALVisionRecognition, and the other modules that need libpng12. Camera only fills QVGA buffers.
- Known sim issues: walks go ~86% of the commanded distance while odometry reports 100%. If `getRobotPosition` is NaN, `moveTo` silently does nothing until naoqisim restarts; patch 0004 fixed the cause (10/10 fresh starts OK), scripts still check for NaN.

## Sim tooling (`tools/`, not robot code)

```sh
tools/trials.sh 10 <label>   # fresh-start trials: reload world, new naoqisim, probe odometry -> tools/out/trials.csv
tools/sim_reset.sh           # same, until one passes; leaves naoqisim up and the robot resting
```
Stop anything else commanding the robot first (e.g. the use_the_naoqi_bridge bridge). Sim-only logic goes here or in `docker/`, never in `scripts/`.

## NOTES.md

`NOTES.md` is the lab log. It has per-step results tables (Step 1 naoqisim, Step 2 scripts in Webots, Step 3 real NAO V5) and a "Sim vs robot differences" list. Record new results and sim/robot differences there.

## Other projects using this stack

`docs/NEW_PROJECT.md` describes how a separate repo can own its own Webots worlds and code and still use naoqisim from here (it connects to `host.docker.internal:9559`). Changes to `docker-compose.yml`, the port, or the robot name `NAO` affect those projects.
