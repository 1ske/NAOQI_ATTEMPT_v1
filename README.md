# naoqi-basics

Small Python 2.7 scripts that do the basics through NAOqi 2.1.4 (stiffness, postures,
walking, head, sensors, falls, camera). They run unchanged against a Webots NAO and a real
NAO V5; only `--ip` changes.

```
scripts (Python 2.7, pynaoqi) → NAOqi 2.1.4 → { Webots NAO (via naoqisim) | real NAO V5 }
```

```
 Mac: Webots R2025a, world webots/worlds/nao_flat.wbt, NAO controller "<extern>"
        ▲ extern-controller link (TCP :1234)
 Docker (linux/amd64, emulated on Apple Silicon):
   naoqisim  NAOqi 2.1.4 inside a Webots controller   :9559
        ▲
   client    Python 2.7 + pynaoqi 2.1.4.13            runs scripts/
```

## Run against Webots

1. Open `webots/worlds/nao_flat.wbt` in Webots R2025a and start it in **real-time** mode.
2. `docker compose up naoqisim`: it attaches to the NAO and serves NAOqi on port 9559.
   For the camera, use `NAOQISIM_FLAGS= docker compose up naoqisim` (without `-nocam`).
3. Run a script:
   ```
   docker compose run --rm client python connect.py
   docker compose run --rm client python walk.py --x 0.5 --repeat 3
   ```
   `NAO_IP` defaults to `naoqisim`. Every script takes `--ip` and `--port`, plus `--help`.

| script | what it does |
|---|---|
| `connect.py` | prints NAOqi / ALMotion version (no motion) |
| `stiffness.py` | `wakeUp()` then `rest()` |
| `posture.py` | StandInit → Stand → Crouch |
| `walk.py` | `moveTo(x, y, theta)` × `--repeat`, prints odometry |
| `head.py` | head yaw/pitch targets, commanded vs measured |
| `sensors.py` | sonar, foot bumpers, inertial angles (no motion) |
| `fall.py` | waits for a fall, then stands back up |
| `camera.py` | saves one camera image to `scripts/out/camera.png` |

## Run against the real NAO V5

Same scripts with `--ip <robot ip>`, e.g. `docker compose run --rm client python connect.py --ip 192.168.1.20`.
Do them in this order and don't move on until the current one behaves:

1. `connect.py`, `sensors.py`: robot sitting, motors off.
2. `stiffness.py`, `head.py`: robot suspended or in a harness.
3. `posture.py`: standing, with a spotter.
4. `walk.py --x 0.2`, then up to 0.5 m: flat floor, with a spotter.

Write results and any sim-vs-robot differences in `NOTES.md`.

## Safety

- NAOqi's protections stay on: nothing here disables the fall manager or foot-contact protection.
- Low speeds: joint `fractionMaxSpeed` ≤ 0.3, posture speed ≤ 0.5 (enforced in `scripts/common.py`).
- Every moving script ends limp and resting, also on errors and Ctrl-C (`safe_session`).
- No keyframe replay on the real robot: the Webots `.motion` files need joint speeds the V5 can't do.
- Real robot: the chest button is the e-stop; someone stays within arm's reach while it moves;
  check the battery and let it cool between walking sessions.

## Simulator SDK copy

`docker/naoqisim` downloads `simulator-sdk-2.1.4.1-linux64.tar.gz` (checksum-verified) unless a copy
is in `docker/naoqisim/vendor/`. The file is 275 MB, too big for plain git, so it's git-ignored for now.
To keep it in the repo: `brew install git-lfs && git lfs install`, remove the vendor line from
`.gitignore`, then `git add docker/naoqisim/vendor/*.tar.gz`.
