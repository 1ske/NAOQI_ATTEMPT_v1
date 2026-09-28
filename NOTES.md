# NOTES

What worked, what didn't, and how NAOqi behaves in Webots vs on the NAO V5.
Ground truth ("truth") below comes from `webots/tools/truth.py` (Webots supervisor), not NAOqi.

## Step 1 — naoqisim ↔ Webots: passes

- Host: Apple Silicon Mac, Webots R2025a. Docker Desktop VM (8 CPUs, 4 GB) runs the linux/amd64
  containers through Rosetta (`/proc/cpuinfo`: VirtualApple).
- naoqisim pinned at `f4c167c` (last commit, 2021-11-15), built on Ubuntu 22.04 + Webots R2025a Linux.
- The extern link works: `WEBOTS_CONTROLLER_URL=tcp://host.docker.internal:1234/NAO`, Webots logs
  `'NAO' extern controller: connected`, NAOqi logs `NAOqi is ready`, port 9559 accepts connections.
- Simulation speed: ~0.96× real time with `-nocam`, ~0.91× with cameras. Slower while NAOqi starts.
- Build fixes (in the Dockerfile, not patches):
  - the old naoqisim Makefile and R2025a's `Makefile.os.include` turn `WEBOTS_HOME_PATH` into
    `"/opt/webots "`, so it's passed on the make command line;
  - system libs needed by the SDK: `libglib2.0-0` (Qt4), `libdbus-1-3`, `libusb-0.1-4` (`hal`);
  - NAOqi refuses to run as root → container user `nao`.
- NAOqi modules that **don't load** (need `libpng12`, not in Ubuntu 22.04): allocalization,
  modularityperception, navigation, poddetection, visionrecognition. Not used by our scripts.
  ALSystem doesn't exist in naoqisim either (`connect.py` handles it).
- Device names in the R2025a `Nao` PROTO match what naoqisim looks up. No patch needed there.

### Patches applied to naoqisim

| patch | why |
|---|---|
| `0001-model-name-from-r2025a-proto.patch` | The PROTO's model string is `NAO_H25_VV5 (red)`; naoqisim looked for `NAOH25VV5 (RED).xml`. Now parsed to `NAOH25V50` (override with `NAOQISIM_MODEL`). |
| `0002-inertial-angles-from-accelerometer-gyro.patch` | The PROTO's InertialUnit has `yAxis FALSE`. Webots implements that by zeroing a component of the rotation axis, which corrupts roll/pitch as soon as the robot has turned (NAOqi saw a 90° turn as "LyingRight" while truth said upright). AngleX/AngleY now come from the accelerometer (gravity) fused with the gyro. Convention checked against NAOqi's own posture library (`postures_naoh25.xml`): StandInit AngleY 0.104 (we read 0.100), Crouch −0.052 (−0.051), LyingBack −1.62, i.e. pitch is the outer angle (±π), roll the inner one (±π/2). Matches truth within ~0.1° standing and after turning (lying poses only checked against NAOqi's posture recognition). |
| `0003-skip-nan-before-first-sample.patch` | Webots sensors read NaN until their first sample. `Motor` skipped it, `HipMotor` (LHipYawPitch) and `Fsr` didn't: ALMotion kept a NaN leg length (`Left Leg max leg length: compute torso height failed`) and couldn't walk. |
| `0004-send-sensors-before-naoqi-starts.patch` | The cause of the NaN odometry (see "NaN odometry" below). On Linux naoqisim launched hal + naoqi without the SDK's `initSimulatorFunc`, and only sent sensor values ~1 s later. ALMotion started on HAL's NaN joint positions, its joint velocities went NaN and stayed NaN, and so did `getRobotPosition` once the robot moved. naoqisim now creates the devices in that callback, steps Webots and sends real values before naoqi starts (`sim_launcher.h`: the callback must send every sensor value). Log line: `sensors sent to HAL before NAOqi start`. |

`NAOQISIM_IMU_DEBUG=1 docker compose up naoqisim` logs IMU and FSR values once per sim second.

## Step 2 — scripts against Webots

| script | result | notes |
|---|---|---|
| connect.py | pass | ALMotion 2.1.4, body Nao V5.0; no ALSystem in naoqisim |
| stiffness.py | pass | from the all-zero start pose `wakeUp()` only stiffens (NAOqi 2.1 on H25 keeps the current pose), so the script goes to StandInit itself; `rest()` → Crouch |
| posture.py | pass | StandInit, Stand, Crouch all reached |
| walk.py | pass, **intermittent** | truth: 3/3 × 0.5 m without falling, **1.29 m for 1.5 m commanded (86 %)**; 2 × 90° turns = 154° (86 %). NAOqi odometry claims the full distance. See "Emulation stalls" for the intermittent part. |
| head.py | pass | measured = commanded to 0.01 rad |
| sensors.py | pass | inertial angles match truth; sonar sees a box: 0.31 m at ~0.30 m, 0.25 (min) when closer, **only if the surface faces the sensor** (Webots sonar drops rays > 22.5° incidence); foot bumpers not tested (need a contact) |
| fall.py | **partial** | falls detected (LyingBack after a backward push). Getting up: **from the back only at speed 1.0** (fails at our 0.5 cap); **from the belly: fails at 0.5 and 1.0**. After a forward push the robot lands head-down (AngleY 1.8 vs NAOqi's LyingBelly 1.38) or twisted (`Unknown`), neither of which ALRobotPosture gets up from. |
| camera.py | pass at QVGA | image matches the Webots view. naoqisim only fills a QVGA buffer, so a VGA request returns an empty buffer (solid green). Default is now QVGA. |

### NaN odometry: a startup race, fixed by patch 0004 (2026-09-24)

`tools/trials.sh N LABEL` measures it: each trial reloads the world, starts a fresh naoqisim and runs
`tools/probe_odometry.py` (StandInit, 0.1 m walk, rest, StandInit, watching `getRobotPosition`).
`clockwatch` runs in the container meanwhile and logs backwards wall-clock jumps and stalls.
Results and per-trial logs go to `tools/out/` (git-ignored).

| label | OK | notes |
|---|---|---|
| baseline (patches 0001–0003) | 0/10 | all NaN 0.96–1.11 s into the first StandInit; 0 backwards jumps, 8/10 trials without any stall > 50 ms |
| init-sensors (+ 0004) | 10/10 | walk 0.098–0.099 m odometry; stalls up to 98 ms, up to 66 `DcmLostPlugin` lines, 5 small backwards clock jumps (−5 ms): all harmless |

- Not the emulation stalls and not the clock. A boot trace showed the joint positions in ALMemory
  NaN for ~0.7 s after HAL started, `Motion/Velocity/Sensor/*` going NaN in that window, before
  `wakeUp` and with the robot still, and staying NaN after the positions became valid.
- Older starts were slower, so naoqisim sometimes won the race (1 of 4 OK before). With cached
  images NAOqi is ready in ~4 s and it lost every time.
- So no clock shim, `SYS_NICE` or Docker CPU tuning was needed; not tried.
- End to end through use_the_naoqi_bridge's MCP: stand, `walk_to(0.3)` completed (truth 0.26 m),
  a 90° turn (truth ~78°), rest.
- `tools/sim_reset.sh` retries reload + fresh naoqisim until a probe passes, if it ever comes back.

### Emulation stalls (the Mac↔Docker risk from the plan)

- Even an idle loop in an amd64 container sometimes isn't scheduled for ~200 ms. naoqisim's HAL
  then misses its cycle (`DcmLostPlugin: Decrease stiffness due to HAL cycle time error of 150–420 ms`)
  and the DCM briefly lowers stiffness. Once HAL also saw time step backwards (`4294967048 ms` = −248 ms).
- In 3 of 4 fresh starts (patches 0001–0003), ALMotion's odometry (`getRobotPosition`) became NaN a
  few seconds into the first motion (StandZero → StandInit), and `moveTo` then did nothing until
  NAOqi restarted. I blamed the stalls; the cause was the startup race above (patch 0004).
  `walk.py` still checks for NaN.
- Not caused by memory or CPU load (3 GB free, load ~2/8). Nothing to tune from inside the container.

### Tools

- `webots/tools/truth.py`: ground-truth position, heading, roll, pitch of the NAO (supervisor robot
  `truth` in the world, `synchronization FALSE` so it's optional).

## Step 3 — real NAO V5

Not started.

- NAOqi version on the robot:

| script | result | notes |
|---|---|---|

## Sim vs robot differences (to check on the real robot)

- Walk distance/turn angle ~86 % of commanded in Webots; odometry doesn't notice.
- Get-up needs posture speed 1.0 in Webots (from the back) and doesn't work from the belly.
- Only QVGA camera images in naoqisim.
- Sonar in Webots only sees surfaces facing it.
