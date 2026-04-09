---
name: cron-scheduling
description: >-
  Complete cron job lifecycle skill: setup, write, update, manage, pause, stop, and monitor
  scheduled tasks on Linux, macOS, Windows, Docker, Kubernetes, GitHub Actions, Node.js, and Python.
  Use this skill whenever a user asks about scheduling, automating recurring tasks, cron expressions,
  crontab editing, job management, cron monitoring, task schedulers, or any variation of
  "run this script automatically", "set up a scheduled job", "run every X minutes/hours/days",
  "cronjob", "crontab", "stop a cron job", "why isn't my cron job running", or
  "how do I see what cron jobs are running". Always reach for this skill even for
  adjacent topics like launchd, Task Scheduler, GitHub Actions schedules, APScheduler,
  node-cron, or Kubernetes CronJobs.
---

# Cron Scheduling Skill

## Quick reference: where to go deeper

| Topic | Reference file |
|-------|-----------------|
| Cron expression syntax and operators | [references/syntax-reference.md](references/syntax-reference.md) |
| Non-Linux environments and platforms | [references/environments.md](references/environments.md) |
| Updating, pausing, and managing jobs | [references/managing-jobs.md](references/managing-jobs.md) |
| Monitoring, logging, and troubleshooting | [references/monitoring.md](references/monitoring.md) |

---

## Quick-decision tree — what does the user need?

```
User asks about cron…
│
├── "What does */5 * * * * mean?" / "How do I write a schedule for…"
│   └── Read: references/syntax-reference.md
│
├── "Set up / create a cron job"
│   └── Follow: §Setup workflow below — no extra file needed for Linux basics
│       If macOS / Windows / Docker / K8s / Node / Python → also read: references/environments.md
│
├── "Update / change / edit a cron job"
│   └── Read: references/managing-jobs.md §Updating
│
├── "Pause / disable / stop / delete a cron job"
│   └── Read: references/managing-jobs.md §Stopping & disabling
│
├── "My cron job isn't running" / "How do I debug?"
│   └── Read: references/monitoring.md §Debugging
│
├── "Monitor / see logs / alert on failures"
│   └── Read: references/monitoring.md
│
└── Non-Linux environment question
    └── Read: references/environments.md
```

---

## Core concepts (always available)

### Cron syntax at a glance

```
 ┌──────── minute        0–59
 │  ┌───── hour          0–23
 │  │  ┌── day-of-month  1–31
 │  │  │  ┌─ month       1–12
 │  │  │  │  ┌ day-of-week  0–7  (0 and 7 both = Sunday)
 │  │  │  │  │
 *  *  *  *  *   command
```

| Symbol | Meaning | Example |
|--------|---------|---------|
| `*` | Every value | `* * * * *` → every minute |
| `,` | List | `0,30 * * * *` → :00 and :30 |
| `-` | Range | `0 9-17 * * *` → every hour 9 AM–5 PM |
| `/` | Step | `*/15 * * * *` → every 15 min |
| `@daily` | Shorthand | = `0 0 * * *` |
| `@reboot` | At boot | runs once on startup |

### The #1 rule: cron's environment is minimal

Cron runs with a stripped-down `PATH=/usr/bin:/bin` — no `.bashrc`, no `.zshrc`, no exports.
**Always use absolute paths** for both the interpreter and the script.

```bash
# Wrong — relies on your PATH
0 2 * * * python3 backup.py

# Correct
0 2 * * * /usr/bin/python3 /opt/app/backup.py >> /var/log/backup.log 2>&1
```

---

## Setup workflow (Linux/macOS cron)

### Step 1 — Write and test the script

```bash
#!/usr/bin/env bash
set -euo pipefail           # Exit on error, undefined vars, pipe failures

LOG=/var/log/myjob.log
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$LOG"; }

log "INFO: Job started"
# ... your logic here ...
log "INFO: Job finished"
```

Test it in cron's exact environment before scheduling:

```bash
env -i HOME=/home/youruser SHELL=/bin/bash PATH=/usr/bin:/bin \
    bash /opt/scripts/myjob.sh
```

If it fails here → fix it before adding to cron.

### Step 2 — Open the crontab

```bash
crontab -e                        # Your own jobs
sudo crontab -u www-data -e       # Another user's jobs (as root)
sudo nano /etc/cron.d/myapp       # System-wide jobs (needs username field)
```

### Step 3 — Write a complete entry

```bash
# ── Environment (set at top of crontab, once) ──────────────────
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""          # "" = suppress email; or admin@example.com

# ── Job entries ────────────────────────────────────────────────
# minute  hour  day  month  weekday  command

# Daily backup at 2:30 AM
30 2 * * *  /bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1

# Weekdays at 8 AM
0 8 * * 1-5  /usr/bin/python3 /opt/app/report.py >> /var/log/report.log 2>&1

# Every 5 minutes, safe against overlaps
*/5 * * * *  /usr/bin/flock -n /tmp/poll.lock /opt/scripts/poll.sh >> /var/log/poll.log 2>&1
```

> `>> /var/log/file.log 2>&1` captures both stdout and stderr.
> Omit it and output vanishes (or goes to root's mailbox).

### Step 4 — Verify

```bash
crontab -l                                          # List installed jobs
systemctl status cron                               # Ubuntu/Debian
systemctl status crond                              # CentOS/RHEL
sudo tail -f /var/log/syslog | grep CRON            # Watch live execution
sudo journalctl -u cron --since "1 hour ago"        # Recent activity
```

### Step 5 — System-wide jobs (`/etc/cron.d/`)

Files in `/etc/cron.d/` need a username field and must be owned by root, mode 644:

```bash
# /etc/cron.d/myapp
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# minute hour day month weekday  USER     command
0 2 * * *                        root     /opt/myapp/backup.sh >> /var/log/myapp.log 2>&1
*/5 * * * *                      www-data /opt/myapp/worker.sh > /dev/null 2>&1
```

```bash
sudo chmod 644 /etc/cron.d/myapp
sudo chown root:root /etc/cron.d/myapp
```

Drop-in directories (no username field needed, just drop an executable file):

| Directory | Frequency |
|-----------|-----------|
| `/etc/cron.hourly/` | Every hour |
| `/etc/cron.daily/` | Every day |
| `/etc/cron.weekly/` | Every week |
| `/etc/cron.monthly/` | Every month |

---

## Safe job template (copy-paste starter)

```bash
#!/usr/bin/env bash
# ── Safe cron job template ─────────────────────────────────────────
# Usage: crontab entry should use flock + timeout + absolute paths
#   */5 * * * * /usr/bin/flock -n /tmp/JOBNAME.lock \
#     /usr/bin/timeout 240 /opt/scripts/JOBNAME.sh \
#     >> /var/log/JOBNAME.log 2>&1

set -euo pipefail
IFS=$'\n\t'

JOB_NAME="JOBNAME"
LOG="/var/log/${JOB_NAME}.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$JOB_NAME] $*" >> "$LOG"; }

START=$(date +%s)
log "INFO: Started"

# ── Your logic here ────────────────────────────────────────────────

log "INFO: Finished in $(( $(date +%s) - START ))s"
```

---

## Quick reference — crontab commands

```bash
crontab -e               # Edit your crontab
crontab -l               # List your crontab
crontab -r               # Remove ALL your jobs (careful!)
crontab -u USER -e       # Edit another user's crontab (root only)
crontab -u USER -l       # List another user's crontab

# List ALL users' jobs on the system
for u in $(cut -f1 -d: /etc/passwd); do
  jobs=$(crontab -l -u "$u" 2>/dev/null | grep -v '^#' | grep -v '^$')
  [ -n "$jobs" ] && echo "=== $u ===" && echo "$jobs"
done
```

