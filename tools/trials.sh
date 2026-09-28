#!/bin/bash
# Fresh-start trials: does ALMotion odometry survive naoqisim under emulation? (NOTES.md "Emulation stalls")
#   tools/trials.sh [N=10] [LABEL=baseline]
# Per trial: reload the Webots world (naoqisim exits), start a fresh naoqisim + clockwatch, wait for
# "NAOqi is ready", sleep SETTLE s, run tools/probe_odometry.py. Appends a row to tools/out/trials.csv
# and keeps tools/out/<label>-<n>.log (naoqisim log with timestamps + probe) and <label>-<n>.clock.log.
# Needs Webots open on a world with the NAO and the `truth` robot, in real-time mode, and nothing
# else commanding the robot. Leaves naoqisim running and the robot resting.
# Env: SETTLE (s, 0), READY_TIMEOUT (s, 300), PROBE_TIMEOUT (s, 240), WEBOTS_HOME (/Applications/Webots.app),
#      UNTIL_OK (set: stop at the first OK trial, exit 1 if none; used by tools/sim_reset.sh)
set -u
cd "$(dirname "$0")/.."
N=${1:-10}
LABEL=${2:-baseline}
SETTLE=${SETTLE:-0}
READY_TIMEOUT=${READY_TIMEOUT:-300}
PROBE_TIMEOUT=${PROBE_TIMEOUT:-240}
export WEBOTS_HOME=${WEBOTS_HOME:-/Applications/Webots.app}
OUT=tools/out
CSV=$OUT/trials.csv
mkdir -p "$OUT"
[ -f "$CSV" ] || echo "label,trial,start_utc,result,phase,t_nan,moved,dcmlost,rt_warning,clock_back,clock_step,clock_gap,max_gap_ms,ready_s" > "$CSV"

if curl -s -m 2 -o /dev/null localhost:8765/health; then
  echo "something answers on :8765 (the use_the_naoqi_bridge bridge?): stop it first, it rests an awake robot" >&2
  exit 1
fi

if pgrep -f "truth.py" >/dev/null; then
  echo "webots/tools/truth.py is running: stop it first, the world reload needs the truth robot" >&2
  exit 1
fi

# run "$@", kill it after $1 seconds
with_timeout() {
  local secs=$1; shift
  "$@" & local pid=$!
  ( sleep "$secs"; kill "$pid" 2>/dev/null ) & local watchdog=$!
  wait "$pid"; local rc=$?
  kill "$watchdog" 2>/dev/null; wait "$watchdog" 2>/dev/null
  return $rc
}

count() { grep -c -- "$1" "$2" 2>/dev/null || true; }

naoqisim_running() { [ "$(docker compose ps -a naoqisim --format '{{.State}}')" = running ]; }

# Reload while naoqisim is connected: Webots waits for the NAO's extern controller, so without it
# the reload (applied at the next step) never happens. naoqisim exiting is the proof it happened.
reload_world() {
  local attempt t0
  for attempt in 1 2 3; do
    docker compose up -d naoqisim >/dev/null 2>&1
    with_timeout 30 "$WEBOTS_HOME/Contents/MacOS/webots-controller" --robot-name=truth \
      webots/tools/reload.py >/dev/null 2>&1
    t0=$(date +%s)
    while naoqisim_running && [ $(( $(date +%s) - t0 )) -lt 30 ]; do sleep 1; done
    naoqisim_running || return 0
    echo "   reload attempt $attempt: naoqisim still running" >&2
  done
  return 1
}

for i in $(seq 1 "$N"); do
  start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  log=$OUT/$LABEL-$i.log
  clock=$OUT/$LABEL-$i.clock.log
  echo "== $LABEL trial $i/$N ($start)"

  if ! reload_world; then
    echo "world reload failed (is Webots open and running, with a robot named truth?)" >&2
    exit 1
  fi
  sleep 2
  docker compose up -d --force-recreate naoqisim >/dev/null 2>&1
  docker compose exec -d naoqisim sh -c '/opt/tools/clockwatch > /tmp/clockwatch.log 2>&1'

  t0=$(date +%s); ready_s=""
  while [ $(( $(date +%s) - t0 )) -lt "$READY_TIMEOUT" ]; do
    if docker compose logs naoqisim 2>/dev/null | grep -q "NAOqi is ready"; then
      ready_s=$(( $(date +%s) - t0 )); break
    fi
    sleep 2
  done

  if [ -z "$ready_s" ]; then
    fields="NOT_READY,,,"
  else
    sleep "$SETTLE"
    with_timeout "$PROBE_TIMEOUT" docker compose run --rm -T -v "$PWD/tools:/tools" client \
      python /tools/probe_odometry.py > "$OUT/probe.tmp" 2>&1
    fields=$(python3 - "$OUT/probe.tmp" <<'EOF'
import json, sys
lines = [l for l in open(sys.argv[1]) if " RESULT " in l]
r = json.loads(lines[-1].split(" RESULT ", 1)[1]) if lines else {"result": "NO_RESULT"}
keys = ["result", "phase", "t_nan", "moved"]
print(",".join("" if r.get(k) is None else str(r[k]) for k in keys))
EOF
)
  fi

  docker compose logs -t naoqisim > "$log" 2>&1
  if [ -f "$OUT/probe.tmp" ]; then
    { echo "==== probe"; cat "$OUT/probe.tmp"; } >> "$log"
    rm -f "$OUT/probe.tmp"
  fi
  docker compose exec -T naoqisim cat /tmp/clockwatch.log > "$clock" 2>/dev/null
  max_gap=$(awk '/ GAP /{sub("mono_dt=", "", $4); sub("ms", "", $4); if ($4 > m) m = $4} END {print m + 0}' "$clock")
  row="$LABEL,$i,$start,$fields,$(count DcmLostPlugin "$log"),$(count "real-time has not been guaranteed" "$log"),$(count " BACK " "$clock"),$(count " STEP " "$clock"),$(count " GAP " "$clock"),$max_gap,$ready_s"
  echo "$row" >> "$CSV"
  echo "   $row"
  if [ -n "${UNTIL_OK:-}" ] && [ "${fields%%,*}" = OK ]; then
    echo "ready: naoqisim is up with valid odometry, robot resting"
    exit 0
  fi
done
[ -z "${UNTIL_OK:-}" ] || { echo "no OK trial in $N attempts" >&2; exit 1; }

ok=$(grep -c "^$LABEL,.*,OK," "$CSV")
total=$(grep -c "^$LABEL," "$CSV")
echo "$LABEL: $ok/$total OK (all runs with this label in $CSV)"
