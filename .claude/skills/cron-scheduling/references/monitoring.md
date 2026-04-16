# Cron monitoring and debugging reference

_Read this file when: the user asks about logs, monitoring, alerting on cron failures, dead man's switches, Prometheus/Grafana integration, or debugging why a cron job isn't running._

---

## Table of contents

1. [Reading cron logs](#1-reading-cron-logs)
2. [Structured logging inside scripts](#2-structured-logging-inside-scripts)
3. [Dead man's switch (healthcheck monitoring)](#3-dead-mans-switch)
4. [Exit-code monitoring and alerting](#4-exit-code-monitoring-and-alerting)
5. [Prometheus + Grafana integration](#5-prometheus--grafana-integration)
6. [Debugging — systematic process](#6-debugging--systematic-process)
7. [Troubleshooting table](#7-troubleshooting-table)
8. [Simulating cron's environment locally](#8-simulating-crons-environment)

---

## 1. Reading cron logs

### System log (where crond writes job start/end events)

```bash
# Ubuntu/Debian — systemd journal
sudo journalctl -u cron -f                          # Stream live
sudo journalctl -u cron --since "today"             # Today only
sudo journalctl -u cron --since "2 hours ago"       # Last 2 hours
sudo journalctl -u cron -p err                      # Errors only
sudo journalctl -u cron --since "today" | grep CMD  # Show commands run

# Ubuntu/Debian — syslog (older systems)
sudo tail -f /var/log/syslog | grep CRON
sudo grep CRON /var/log/syslog | tail -50

# CentOS/RHEL
sudo tail -f /var/log/cron
sudo grep "backup" /var/log/cron | tail -20
```

### What a successful cron log entry looks like

```
Jan 15 02:00:01 myserver CRON[18432]: (ubuntu) CMD (/bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1)
│              │          │           │        │
timestamp      hostname  daemon[PID]  user     command that ran
```

### Count how many times a job ran

```bash
# Count runs today
sudo journalctl -u cron --since "today" | grep "backup.sh" | wc -l

# Show run times for the last 7 days
sudo journalctl -u cron --since "7 days ago" | grep "backup.sh"
```

### Cron job output logs (written by your script redirect)

```bash
# View job output log
tail -f /var/log/backup.log
tail -100 /var/log/backup.log

# Search for errors in job log
grep -i "error\|fail\|warn" /var/log/backup.log | tail -20

# Show entries with timestamps (if your script logs them)
grep "2024-01-15" /var/log/backup.log
```

---

## 2. Structured logging inside scripts

Add this boilerplate to every cron script for consistent, parseable logs:

### Bash — simple timestamped log function

```bash
#!/usr/bin/env bash
set -euo pipefail

LOG="/var/log/myjob.log"
JOB="myjob"

log() {
  local level=$1; shift
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$JOB] [$level] $*" >> "$LOG"
}

START=$(date +%s)
log INFO "Job started (PID $$)"

# ... your logic ...
EXIT_CODE=0
some_command || EXIT_CODE=$?

DURATION=$(( $(date +%s) - START ))
if [ "$EXIT_CODE" -eq 0 ]; then
  log INFO "Job completed successfully in ${DURATION}s"
else
  log ERROR "Job failed with exit code $EXIT_CODE after ${DURATION}s"
fi
exit "$EXIT_CODE"
```

### JSON structured logs (for log aggregators like Datadog, Loki, Splunk)

```bash
log_json() {
  local level=$1; shift
  printf '{"ts":"%s","job":"%s","level":"%s","msg":"%s","pid":%d}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$JOB" "$level" "$*" "$$" >> "$LOG"
}

log_json INFO "Backup started"
log_json INFO "Written 1.24 GB to /backups/db_20240115.sql.gz"
log_json INFO "Completed in 142s"
```

### Log rotation (prevent logs from filling disk)

```bash
# /etc/logrotate.d/cron-jobs
/var/log/backup.log
/var/log/report.log
/var/log/sync.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate        # Safe for scripts still writing to the file
}
```

---

## 3. Dead man's switch

Standard log monitoring tells you when something goes wrong. A dead man's switch alerts you when a job *stops running* — which is invisible in logs.

### Healthchecks.io (free tier available)

```bash
HC_UUID="your-uuid-here"     # From healthchecks.io dashboard
HC_URL="https://hc-ping.com/${HC_UUID}"

# Pattern 1 — Ping start and success; auto-ping /fail if start was sent but success wasn't
0 2 * * * \
  /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}/start" && \
  /opt/scripts/backup.sh >> /var/log/backup.log 2>&1 && \
  /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}" \
  || /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}/fail"

# Pattern 2 — Simple ping on success (no start signal)
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1 && \
  /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}"
```

### Cronitor

```bash
CRONITOR_KEY="your-monitor-key"

0 2 * * * \
  /usr/bin/curl -sm 5 "https://cronitor.link/${CRONITOR_KEY}/run" && \
  /opt/scripts/backup.sh >> /var/log/backup.log 2>&1 && \
  /usr/bin/curl -sm 5 "https://cronitor.link/${CRONITOR_KEY}/complete" \
  || /usr/bin/curl -sm 5 "https://cronitor.link/${CRONITOR_KEY}/fail"
```

### Wrapper script approach (DRY — reuse across all jobs)

```bash
#!/usr/bin/env bash
# /opt/scripts/monitored-run.sh
# Usage: monitored-run.sh <healthcheck-uuid> <command> [args...]

HC_UUID=$1; shift
HC_URL="https://hc-ping.com/${HC_UUID}"

/usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}/start" 2>/dev/null || true

START=$(date +%s)
"$@"
EXIT_CODE=$?
DURATION=$(( $(date +%s) - START ))

if [ "$EXIT_CODE" -eq 0 ]; then
  /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}?duration=${DURATION}" 2>/dev/null || true
else
  /usr/bin/curl -fsS --retry 3 -o /dev/null "${HC_URL}/fail" 2>/dev/null || true
fi

exit "$EXIT_CODE"
```

```bash
# Clean crontab entries using the wrapper
0 2 * * * /opt/scripts/monitored-run.sh "UUID-1" /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
0 8 * * 1-5 /opt/scripts/monitored-run.sh "UUID-2" /opt/scripts/report.sh >> /var/log/report.log 2>&1
```

---

## 4. Exit-code monitoring and alerting

### Email on failure (simple — uses system mail)

```bash
#!/usr/bin/env bash
JOB_NAME="db_backup"
ALERT_EMAIL="ops@example.com"

run_job() {
  /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
}

if ! run_job; then
  EXIT_CODE=$?
  {
    echo "Subject: [CRON ALERT] $JOB_NAME failed on $(hostname)"
    echo "To: $ALERT_EMAIL"
    echo ""
    echo "Job: $JOB_NAME"
    echo "Host: $(hostname)"
    echo "Time: $(date)"
    echo "Exit code: $EXIT_CODE"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 /var/log/backup.log
  } | sendmail "$ALERT_EMAIL"
fi
```

### Slack webhook on failure

```bash
#!/usr/bin/env bash
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
JOB_NAME="db_backup"

/opt/scripts/backup.sh >> /var/log/backup.log 2>&1
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ]; then
  /usr/bin/curl -fsS -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\":rotating_light: *Cron job failed*\n*Job:* \`${JOB_NAME}\`\n*Host:* \`$(hostname)\`\n*Time:* $(date -u)\n*Exit code:* ${EXIT_CODE}\"}" \
    "$SLACK_WEBHOOK"
fi
```

### Generic alert wrapper script

```bash
#!/usr/bin/env bash
# /opt/scripts/alert-on-fail.sh — universal wrapper
# Usage: alert-on-fail.sh "Job Name" /path/to/command [args...]
JOB_NAME="$1"; shift

"$@"
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ]; then
  MSG="Cron job '$JOB_NAME' failed on $(hostname) at $(date). Exit code: $EXIT_CODE"
  # Notify via your preferred channel:
  echo "$MSG" | mail -s "Cron failure: $JOB_NAME" ops@example.com
  # or: curl -fsS -X POST ... (Slack/PagerDuty/etc.)
fi

exit "$EXIT_CODE"
```

```bash
# In crontab
0 2 * * * /opt/scripts/alert-on-fail.sh "DB Backup" /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 5. Prometheus + Grafana integration

Push job metrics to a **Prometheus Pushgateway** after each run.

### Push metrics script

```bash
#!/usr/bin/env bash
# /opt/scripts/push-metrics.sh
# Usage: push-metrics.sh <job_name> <exit_code> <duration_seconds>

JOB_NAME=$1
EXIT_CODE=$2
DURATION=$3
PUSHGATEWAY="${PUSHGATEWAY_URL:-http://pushgateway:9091}"
TS=$(date +%s)

cat << EOF | /usr/bin/curl -s --data-binary @- "${PUSHGATEWAY}/metrics/job/cron/instance/${JOB_NAME}"
# HELP cron_job_last_success_timestamp_seconds Unix timestamp of last successful run
# TYPE cron_job_last_success_timestamp_seconds gauge
$([ "$EXIT_CODE" -eq 0 ] && echo "cron_job_last_success_timestamp_seconds{job=\"$JOB_NAME\"} $TS")
# HELP cron_job_last_exit_code Exit code of the most recent run
# TYPE cron_job_last_exit_code gauge
cron_job_last_exit_code{job="$JOB_NAME"} $EXIT_CODE
# HELP cron_job_last_duration_seconds Duration in seconds of the most recent run
# TYPE cron_job_last_duration_seconds gauge
cron_job_last_duration_seconds{job="$JOB_NAME"} $DURATION
EOF
```

### Full wrapper with Prometheus push

```bash
#!/usr/bin/env bash
# /opt/scripts/cron-wrapper.sh
# Usage: cron-wrapper.sh <job_name> <command> [args...]

JOB_NAME=$1; shift
START=$(date +%s)

"$@"
EXIT_CODE=$?
DURATION=$(( $(date +%s) - START ))

/opt/scripts/push-metrics.sh "$JOB_NAME" "$EXIT_CODE" "$DURATION"

exit "$EXIT_CODE"
```

```bash
# In crontab — clean one-liner
0 2 * * * /opt/scripts/cron-wrapper.sh "db_backup" /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Grafana dashboard queries (PromQL)

```promql
# Jobs that haven't run successfully in the expected window
time() - cron_job_last_success_timestamp_seconds > 90000   # > 25 hours

# Jobs currently failing
cron_job_last_exit_code != 0

# Duration trend (last 7 days)
cron_job_last_duration_seconds{job="db_backup"}

# Alert rule — job failed
ALERT CronJobFailed
  IF cron_job_last_exit_code != 0
  FOR 5m
  LABELS { severity = "warning" }
  ANNOTATIONS {
    summary = "Cron job {{ $labels.job }} failed",
    description = "Exit code: {{ $value }}"
  }
```

---

## 6. Debugging — systematic process

Work through these checks in order:

```
Job didn't run?
│
├─ 1. Is crond running?
│     systemctl status cron
│     → If stopped: sudo systemctl start cron
│
├─ 2. Is the schedule correct?
│     crontab -l  (look for syntax errors)
│     Validate at https://crontab.guru
│     Check: is the system timezone what you expect?
│     echo $TZ; timedatectl
│
├─ 3. Does the crontab file parse OK?
│     sudo systemctl status cron | grep error
│     sudo journalctl -u cron | grep error
│
├─ 4. Did crond attempt to run it?
│     sudo journalctl -u cron --since "1 hour ago" | grep CMD
│     → If no entry: schedule isn't matching — re-check fields
│
├─ 5. Can the script run in cron's environment?
│     env -i HOME=/home/USER SHELL=/bin/bash PATH=/usr/bin:/bin bash /path/to/script.sh
│     → If fails: fix PATH, absolute paths, env vars
│
├─ 6. Does the script have execute permission?
│     ls -la /path/to/script.sh
│     → Fix: chmod +x /path/to/script.sh
│
├─ 7. Can the cron user read the script and its dependencies?
│     sudo -u www-data bash /path/to/script.sh
│     → Fix: chown/chmod as needed
│
└─ 8. Is output being captured?
      Add >> /tmp/debug.log 2>&1 to capture errors
      cat /tmp/debug.log
```

---

## 7. Troubleshooting table

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Job never runs | crond is stopped | `sudo systemctl start cron` |
| Job never runs | Wrong schedule | Validate at crontab.guru; check timezone |
| Job never runs | `/etc/cron.d/` file has wrong perms | `chmod 644 /etc/cron.d/myapp` |
| Job never runs | `/etc/cron.d/` file has a `.sh` extension | Rename to no extension |
| `command not found` | Relative path | Use absolute paths everywhere |
| Works manually, fails in cron | PATH mismatch | Set `PATH=` at top of crontab; use absolute paths |
| Works manually, fails in cron | Env var not set | Source `.env` file explicitly in script |
| No output, no errors | Output not redirected | Add `>> /var/log/job.log 2>&1` |
| `Permission denied` | Script not executable | `chmod +x /path/to/script.sh` |
| Job runs but has no effect | Missing secrets/credentials | Source env file; check secret manager |
| Multiple copies running | Job overlaps itself | Add `flock -n /tmp/job.lock` |
| Job runs once then stops | `crontab -r` was run | Recreate crontab |
| Runs at wrong time | System timezone unexpected | Check `timedatectl`; set `TZ=` in crontab |
| Job output triggers email | `MAILTO` not set | Add `MAILTO=""` to crontab header |
| Job runs as wrong user | Mixed up crontab sources | Check which user's crontab you're editing |
| Stale lock file after crash | flock lock not cleaned up | `rm -f /tmp/job.lock` |
| Job killed mid-run | OOM killer | Add `resources:` limits; check `dmesg \| grep OOM` |

---

## 8. Simulating cron's environment

The most reliable way to reproduce a cron failure locally:

```bash
# Full simulation — strips your entire environment
env -i \
  HOME=/home/ubuntu \
  SHELL=/bin/bash \
  PATH=/usr/bin:/bin \
  USER=ubuntu \
  LOGNAME=ubuntu \
  /bin/bash /opt/scripts/myjob.sh

# With additional vars your crontab defines
env -i \
  HOME=/home/ubuntu \
  SHELL=/bin/bash \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  MAILTO="" \
  TZ=UTC \
  /bin/bash /opt/scripts/myjob.sh

# Run as the cron user (catches permission issues)
sudo -u www-data env -i \
  HOME=/var/www \
  SHELL=/bin/bash \
  PATH=/usr/bin:/bin \
  /bin/bash /opt/scripts/myjob.sh
```

### Quick diagnostic one-liner

Add this temporarily to catch environment issues:

```bash
# In crontab — dumps cron's environment to a file for inspection
* * * * * env > /tmp/cron-env.txt && echo "---" >> /tmp/cron-env.txt
```

Then inspect `/tmp/cron-env.txt` to see exactly what cron sees.
