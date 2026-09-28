# Hooking up a new project to this simulator stack

This repo (NAOQI_ATTEMPT_v1) is the **simulator stack**. It runs NAOqi 2.1.4 (naoqisim) in Docker
and serves it on port 9559. A new project owns its own Webots worlds and code and only talks to
NAOqi over the network. The only command it needs from this repo is `docker compose up naoqisim`.

```
new project/webots/worlds/x.wbt ──opened in──► Webots (Mac)
                                                  ▲ tcp :1234 (extern controller "NAO")
                                    NAOQI_ATTEMPT_v1: naoqisim container, NAOqi on :9559
                                                  ▲ tcp :9559
new project: app container (Python 2.7 + pynaoqi) ┘
```

Same code on the real NAO V5: set `NAO_IP=<robot ip>`, no naoqisim needed.

## 1. Files to create in the new project

Paths below are relative to the new repo. `$SIM` = path to this repo (e.g. `~/Documents/GitHub/NAOQI_ATTEMPT_v1`).

```sh
mkdir -p webots/worlds webots/tools docker/naoqi src
cp $SIM/webots/worlds/nao_flat.wbt  webots/worlds/        # starting point for your worlds
cp $SIM/webots/tools/truth.py       webots/tools/         # optional ground truth
cp $SIM/docker/client/Dockerfile    docker/naoqi/Dockerfile
cp $SIM/scripts/common.py $SIM/scripts/connect.py src/    # safety helpers + connection check
printf '*.pyc\nwebots/worlds/.*.wbproj\n' > .gitignore
```

Copying the client Dockerfile keeps the new project self-contained: it doesn't depend on an image built in this repo.

`docker-compose.yml`:

```yaml
# naoqisim runs from NAOQI_ATTEMPT_v1 (`docker compose up naoqisim` there);
# open a world from webots/worlds/ in Webots first.
services:
  app:
    build: docker/naoqi
    platform: linux/amd64
    volumes:
      - ./src:/app
    working_dir: /app
    environment:
      NAO_IP: ${NAO_IP:-host.docker.internal}   # naoqisim's published port on the Mac
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

## 2. Rules for worlds in the new project

Any world works if it keeps these three things from `nao_flat.wbt`:

```
WorldInfo {
  basicTimeStep 20                          # naoqisim expects 20 ms
  contactProperties [ ContactProperties {   # foot friction; without it walking degrades
      material1 "NAO foot material"
      coulombFriction [ 7 ]
      bounce 0.3
      bounceVelocity 0.003 } ]
}
DEF NAO Nao {
  name "NAO"                                # naoqisim attaches to the robot named NAO
  controller "<extern>"
}
```

- Keep the `Nao` PROTO at its defaults (V5, H25). naoqisim reads the model from it. If you change
  `version`/`degreeOfFreedom`, start naoqisim with `NAOQISIM_MODEL=...` set.
- The `truth` Robot (supervisor, `<extern>`, `synchronization FALSE`) is optional. Keep it if you
  want `webots/tools/truth.py`. It finds the NAO through `DEF NAO`.
- One NAO per world. A second robot needs a second naoqisim on another port (not set up here).
- Only one Webots instance open. naoqisim connects to port 1234. A second Webots instance would take 1235.
- Heavy worlds slow the sim below real time, and emulation stalls get worse (see NOTES.md).

## 3. Running it

```sh
# 1. Webots on the Mac: open <new project>/webots/worlds/<world>.wbt, real-time mode
# 2. in NAOQI_ATTEMPT_v1:
docker compose up naoqisim                   # wait for "NAOqi is ready"
#    (NAOQISIM_FLAGS=-nocam docker compose up naoqisim  to disable cameras)
# 3. in the new project:
docker compose run --rm app python connect.py
```

`connect.py` should print `ALMotion version: 2.1.4...`. It doesn't move the robot.

Switching worlds: stop naoqisim, open the other world in Webots, then start naoqisim again.

Ground truth (optional), on the Mac from the new project:

```sh
WEBOTS_HOME=/Applications/Webots.app /Applications/Webots.app/Contents/MacOS/webots-controller \
    --robot-name=truth webots/tools/truth.py
```

## 4. Things to carry over

- **Python 2.7 only** in anything that imports `naoqi`. For Python 3 code, put a thin py2.7 bridge
  container in front of NAOqi and have the py3 code talk to the bridge.
- **Safety rules** from `common.py` (README "Safety"): speeds clamped (joints ≤ 0.3, postures
  ≤ 0.5), fall manager and foot-contact protection stay on, every moving program ends limp and
  resting via `safe_session`, no `.motion` keyframe replay on the real robot.
- **Known sim limits** (NOTES.md): walks go ~86 % of the commanded distance, odometry NaN at startup is
  fixed by patch 0004 (if it recurs: `tools/sim_reset.sh`), camera is QVGA only, and ALNavigation / ALLocalization /
  ALVisionRecognition / ALSystem don't exist in naoqisim.
