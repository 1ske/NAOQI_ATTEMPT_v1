/* clockwatch: logs clock anomalies in the naoqisim container, to tell apart the two suspects for
 * ALMotion's NaN odometry (NOTES.md "Emulation stalls"):
 *   BACK  gettimeofday() went backwards (what libhal_core.so reads; a dt <= 0 for HAL)
 *   STEP  gettimeofday() moved more than STEP_MS away from CLOCK_MONOTONIC (wall clock stepped)
 *   GAP   CLOCK_MONOTONIC advanced more than GAP_MS in one 5 ms sleep (the process wasn't run: a stall)
 * One line per event, stamped with wall time and monotonic time; a STAT line every 60 s.
 *   clockwatch [GAP_MS=50] [STEP_MS=20]    (built into the naoqisim image as /opt/tools/clockwatch;
 *                                           tools/trials.sh runs it for every trial)
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>

static double mono_ms(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e3 + ts.tv_nsec / 1e6;
}

static double wall_ms(void) {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  return tv.tv_sec * 1e3 + tv.tv_usec / 1e3;
}

static void stamp(double wall, char *buf, size_t len) {
  time_t s = (time_t)(wall / 1e3);
  struct tm tm;
  gmtime_r(&s, &tm);
  size_t n = strftime(buf, len, "%Y-%m-%dT%H:%M:%S", &tm);
  snprintf(buf + n, len - n, ".%03dZ", (int)((long long)wall % 1000));
}

int main(int argc, char **argv) {
  double gap_ms = argc > 1 ? atof(argv[1]) : 50;
  double step_ms = argc > 2 ? atof(argv[2]) : 20;
  struct timespec sleep = {0, 5 * 1000 * 1000};
  double m0 = mono_ms(), m = m0, w = wall_ms(), next_stat = m0 + 60e3, max_gap = 0;
  long backs = 0, steps = 0, gaps = 0;
  char ts[40];

  stamp(w, ts, sizeof ts);
  printf("%s START gap>%.0fms step>%.0fms\n", ts, gap_ms, step_ms);
  fflush(stdout);
  for (;;) {
    nanosleep(&sleep, NULL);
    double m1 = mono_ms(), w1 = wall_ms();
    double dm = m1 - m, dw = w1 - w;
    stamp(w1, ts, sizeof ts);
    if (dw < 0) {
      backs++;
      printf("%s BACK mono=%.3fs wall_dt=%.1fms mono_dt=%.1fms\n", ts, (m1 - m0) / 1e3, dw, dm);
    } else if (dw - dm > step_ms || dm - dw > step_ms) {
      steps++;
      printf("%s STEP mono=%.3fs wall_dt=%.1fms mono_dt=%.1fms\n", ts, (m1 - m0) / 1e3, dw, dm);
    }
    if (dm > gap_ms) {
      gaps++;
      printf("%s GAP mono=%.3fs mono_dt=%.1fms\n", ts, (m1 - m0) / 1e3, dm);
    }
    if (dm > max_gap)
      max_gap = dm;
    if (m1 >= next_stat) {
      printf("%s STAT mono=%.0fs back=%ld step=%ld gap=%ld max_gap=%.1fms\n", ts, (m1 - m0) / 1e3,
             backs, steps, gaps, max_gap);
      next_stat += 60e3;
      max_gap = 0;
    }
    fflush(stdout);
    m = m1;
    w = w1;
  }
}
