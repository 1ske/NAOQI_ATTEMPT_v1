# NOTES

What worked, what didn't, and how NAOqi behaves in Webots vs on the NAO V5.

## Step 1 — naoqisim ↔ Webots

- Host: Apple Silicon Mac, Webots R2025a. Docker runs linux/amd64 containers emulated.
- naoqisim pinned at `f4c167c` (last commit, 2021-11-15), built on Ubuntu 22.04 + Webots R2025a Linux.
- Device names in the R2025a `Nao` PROTO match what naoqisim looks up (joints, `…S` sensors,
  `Sonar/*`, `LFsr`/`RFsr`, foot bumpers, `CameraTop`/`CameraBottom`, `inertial unit`,
  `accelerometer`, `gyro`). No patch needed.
- The R2025a PROTO already rotates the InertialUnit for the ENU/FLU coordinate change. naoqisim maps
  `AngleX = roll`, `AngleY = -pitch`. **(verify signs with sensors.py by tilting the robot)**
- Build: the old naoqisim Makefile and R2025a's `Makefile.os.include` turn `WEBOTS_HOME_PATH`
  into `"/opt/webots "`; fixed by passing `WEBOTS_HOME_PATH=` on the make command line.
- Build: the SDK's Qt4 needs system `libglib2.0-0`; `albonjour` needs `libdbus-1-3`.
- NAOqi modules that **won't load** (need `libpng12`, not in Ubuntu 22.04): allocalization,
  modularityperception, navigation, poddetection, visionrecognition. Not used by our scripts;
  expect error lines for them at startup.

### Patches applied to naoqisim

| patch | why |
|---|---|
| `0001-model-name-from-r2025a-proto.patch` | The PROTO's model is `NAO_H25_VV5 (red)`; naoqisim turned that into `NAOH25VV5 (RED).xml`. Now parsed to `NAOH25V50` (override with `NAOQISIM_MODEL`). |

## Step 2 — scripts against Webots

| script | result | notes |
|---|---|---|
| connect.py | | |
| stiffness.py | | |
| posture.py | | |
| walk.py | | |
| head.py | | |
| sensors.py | | |
| fall.py | | |
| camera.py | | |

## Step 3 — real NAO V5

- NAOqi version on the robot:

| script | result | notes |
|---|---|---|

## Sim vs robot differences
