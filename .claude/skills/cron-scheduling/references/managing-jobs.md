# Cron job management reference

_Read this file when: the user wants to update, edit, pause, resume, stop, delete, or manage the execution behaviour of existing cron jobs — including preventing overlaps, managing environment variables, running as specific users, or chaining jobs._

---

## Table of contents

1. [Updating a cron job](#1-updating-a-cron-job)
2. [Stopping and disabling jobs](#2-stopping-and-disabling-jobs)
3. [Deleting jobs](#3-deleting-jobs)
4. [Preventing overlapping runs](#4-preventing-overlapping-runs)
5. [Managing environment variables](#5-managing-environment-variables)
6. [Running as a specific user](#6-running-as-a-specific-user)
7. [Job chaining and dependencies](#7-job-chaining-and-dependencies)
8. [Killing a running job](#8-killing-a-running-job)
9. [Stopping the cron daemon](#9-stopping-the-cron-daemon)

---

## 1. Updating a cron job

### Method 1 — Interactive edit (best for one-off changes)

```bash
crontab -e
# Find the line, edit it, save and quit
# crontab reloads automatically on save — no daemon restart needed
```

### Method 2 — Programmatic sed update (best for scripts and CI/CD)

```bash
# Change backup time from 2 AM to 3 AM
OLD='0 2 \* \* \* /bin/bash /opt/scripts/backup.sh'
NEW='0 3 * * * /bin/bash /opt/scripts/backup.sh'

crontab -l | sed "s|$OLD|$NEW|" | crontab -

# Verify
crontab -l
```

### Method 3 — Full file replacement (best for config management / Ansible / Terraform)

```bash
# Write a complete new crontab from a managed file
cat > /tmp/managed-crontab << 'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# v2.4.0 — updated 2024-01-20
0 3 * * *    /bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
0 */4 * * *  /usr/bin/python3 /opt/app/sync.py >> /var/log/sync.log 2>&1
EOF

crontab /tmp/managed-crontab
rm /tmp/managed-crontab
crontab -l   # Verify
```

### Method 4 — Append a new job without touching existing ones

```bash
# Safe append — preserves current crontab
(crontab -l 2>/dev/null; echo "*/10 * * * * /opt/scripts/newjob.sh >> /var/log/newjob.log 2>&1") | crontab -
```

### Updating `/etc/cron.d/` files

Just overwrite the file — crond polls `/etc/cron.d/` and picks up changes automatically (no reload needed):

```bash
sudo tee /etc/cron.d/myapp > /dev/null << 'EOF'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Updated schedule
0 3 * * * root /bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
EOF

sudo chmod 644 /etc/cron.d/myapp
sudo chown root:root /etc/cron.d/myapp
```

---

## 2. Stopping and disabling jobs

### Temporarily disable — comment out

```bash
# Manual — open editor and add # at start of line
crontab -e

# Programmatic — tag with marker so you can re-enable later
TARGET="/opt/scripts/backup.sh"
crontab -l | sed "/$TARGET/s/^/#DISABLED /" | crontab -

# Re-enable by removing the tag
crontab -l | sed "s/^#DISABLED \(.*$TARGET.*\)/\1/" | crontab -
```

### Temporarily disable — use a flag file

Add this guard at the top of your script. Gives you instant on/off without touching crontab:

```bash
#!/usr/bin/env bash
# Check for disable flag
FLAG="/opt/scripts/.backup.disabled"
if [ -f "$FLAG" ]; then
  echo "[$(date)] Skipping: disabled by flag file $FLAG" >> /var/log/backup.log
  exit 0
fi
# ... rest of script
```

```bash
# Disable
touch /opt/scripts/.backup.disabled

# Re-enable
rm /opt/scripts/.backup.disabled
```

### Temporarily disable — stop the cron daemon (disables ALL jobs)

```bash
sudo systemctl stop cron     # Ubuntu/Debian
sudo systemctl stop crond    # CentOS/RHEL

sudo systemctl start cron    # Resume all jobs
```

---

## 3. Deleting jobs

### Delete one specific job

```bash
# Manual
crontab -e   # Delete the line, save

# Programmatic — match on command string
TARGET="/opt/scripts/backup.sh"
crontab -l | grep -v "$TARGET" | crontab -

# Verify it's gone
crontab -l | grep "$TARGET"   # Should return nothing
```

### Delete ALL jobs for the current user

```bash
# Always back up first
crontab -l > ~/crontab_backup_$(date +%Y%m%d_%H%M%S).txt

# Then remove
crontab -r
```

### Delete jobs for another user (as root)

```bash
crontab -r -u www-data
```

### Remove a `/etc/cron.d/` file

```bash
sudo rm /etc/cron.d/myapp
```

---

## 4. Preventing overlapping runs

When a job takes longer than its scheduled interval, multiple instances pile up. Choose the right prevention strategy:

### Strategy A — `flock` (recommended for most jobs)

`flock` is part of `util-linux` (pre-installed on all major Linux distros):

```bash
# In crontab — non-blocking: skip if already running
*/5 * * * * /usr/bin/flock -n /tmp/myjob.lock /opt/scripts/myjob.sh >> /var/log/myjob.log 2>&1
#                            │  └── lock file     └── your command
#                            └── -n = non-blocking (exit code 1 if locked, don't queue)

# Blocking: wait up to 30 seconds to acquire the lock, then skip
*/5 * * * * /usr/bin/flock -w 30 /tmp/myjob.lock /opt/scripts/myjob.sh >> /var/log/myjob.log 2>&1
```

### Strategy B — PID file inside the script

```bash
#!/usr/bin/env bash
PIDFILE="/var/run/myjob.pid"

# Check if already running
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "[$(date)] Already running (PID $(cat $PIDFILE)), exiting." >> /var/log/myjob.log
  exit 0
fi

# Register PID and clean up on exit
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"; exit' INT TERM EXIT

# ... your job logic here ...

rm -f "$PIDFILE"
```

### Strategy C — `timeout` (kill if job runs too long)

```bash
# Kill the job if it hasn't finished within 4 minutes
*/5 * * * * /usr/bin/timeout 240 /opt/scripts/myjob.sh >> /var/log/myjob.log 2>&1
#                             │
#                       seconds (240 = 4 min)

# With a signal (default TERM; use -k for KILL after grace period)
*/5 * * * * /usr/bin/timeout --kill-after=10 240 /opt/scripts/myjob.sh >> /var/log/myjob.log 2>&1
```

### Strategy D — combine flock + timeout (most robust)

```bash
*/5 * * * * /usr/bin/flock -n /tmp/myjob.lock /usr/bin/timeout 240 /opt/scripts/myjob.sh >> /var/log/myjob.log 2>&1
```

---

## 5. Managing environment variables

Cron runs with `PATH=/usr/bin:/bin` and no shell profile loaded. Three safe patterns:

### Pattern 1 — Set variables in the crontab header

```bash
# At the top of crontab, before any job entries
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""
TZ=UTC
DB_HOST=localhost
API_ENV=production
```

Limitation: no `$(...)` substitution, no `source`, no arrays. Simple key=value only.

### Pattern 2 — Source an env file inside the script

```bash
#!/usr/bin/env bash
# Load application environment
set -a                             # Auto-export all vars
source /opt/app/.env               # Contains: DB_URL=..., API_KEY=...
set +a

# Now all .env variables are available
/opt/app/run.sh
```

### Pattern 3 — Wrapper script that sources env and execs

```bash
#!/usr/bin/env bash
# /opt/scripts/with-env.sh — reusable env wrapper
set -a
source /opt/app/.env
set +a
exec "$@"
```

```bash
# In crontab — clean, reusable pattern
0 2 * * * /opt/scripts/with-env.sh /opt/app/backup.py >> /var/log/backup.log 2>&1
0 8 * * 1-5 /opt/scripts/with-env.sh /opt/app/report.py >> /var/log/report.log 2>&1
```

### Pattern 4 — Inline env vars per job

```bash
# Set vars inline (simple cases)
0 2 * * * DB_HOST=localhost DB_USER=app /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Secrets management

Never store secrets in plaintext in the crontab file. Use:

```bash
# Read from a protected file (owned root, mode 600)
0 2 * * * DB_PASSWORD=$(cat /etc/myapp/db.secret) /opt/scripts/backup.sh

# Source a protected env file
0 2 * * * source /etc/myapp/secrets.env && /opt/scripts/backup.sh

# Use systemd credentials / vault agent / AWS SSM Parameter Store in the script
```

---

## 6. Running as a specific user

### User-level crontab

```bash
sudo crontab -u postgres -e     # Edit postgres user's crontab
sudo crontab -u www-data -l     # List www-data's crontab
```

### System crontab (`/etc/crontab` and `/etc/cron.d/`)

These files have an extra `USERNAME` field between the schedule and the command:

```bash
# /etc/cron.d/myapp
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# min  hr   dom  mon  dow   USER       command
0 2   * * *       postgres   pg_dump mydb | gzip > /backups/db.sql.gz
*/5 * * * *       www-data   php /var/www/html/artisan queue:work --once
0 3 1 * *         root       /usr/sbin/logrotate -f /etc/logrotate.conf
```

### `sudo` in a cron job (avoid if possible)

```bash
# If a non-root job needs elevated access, prefer sudoers configuration
# /etc/sudoers.d/myapp-cron:
www-data ALL=(root) NOPASSWD: /opt/scripts/specific_privileged_script.sh

# Then in the crontab for www-data:
*/5 * * * * sudo /opt/scripts/specific_privileged_script.sh
```

---

## 7. Job chaining and dependencies

### Sequential — job B runs after job A finishes (in the same crontab entry)

```bash
# Run B only if A succeeds (&&)
0 2 * * * /opt/scripts/prepare.sh && /opt/scripts/process.sh >> /var/log/etl.log 2>&1

# Run B regardless of A's exit code (;)
0 2 * * * /opt/scripts/cleanup.sh; /opt/scripts/report.sh >> /var/log/chain.log 2>&1

# Run B only if A fails (||)
0 2 * * * /opt/scripts/primary.sh || /opt/scripts/fallback.sh >> /var/log/chain.log 2>&1
```

### Sequential — stagger with separate crontab entries

Use time offsets when tasks share a resource (DB, API) and you want them spread out:

```bash
0  2 * * *   /opt/scripts/export_users.sh    >> /var/log/export.log 2>&1
20 2 * * *   /opt/scripts/export_orders.sh   >> /var/log/export.log 2>&1
40 2 * * *   /opt/scripts/export_products.sh >> /var/log/export.log 2>&1
```

### Parallel — all start at the same time

```bash
0 2 * * *   /opt/scripts/job_a.sh >> /var/log/job_a.log 2>&1
0 2 * * *   /opt/scripts/job_b.sh >> /var/log/job_b.log 2>&1
0 2 * * *   /opt/scripts/job_c.sh >> /var/log/job_c.log 2>&1
```

### Dependency via sentinel file (A must finish before B runs)

```bash
#!/usr/bin/env bash
# job_b.sh — waits for job_a to complete
SENTINEL="/tmp/job_a.done"
TIMEOUT=1800   # 30 minutes

start=$(date +%s)
while [ ! -f "$SENTINEL" ]; do
  elapsed=$(( $(date +%s) - start ))
  [ "$elapsed" -ge "$TIMEOUT" ] && { echo "Timed out waiting for job_a"; exit 1; }
  sleep 10
done

rm -f "$SENTINEL"
# ... rest of job_b ...
```

```bash
# job_a.sh — create sentinel on success
# ... main logic ...
touch /tmp/job_a.done
```

---

## 8. Killing a running job

```bash
# Find the process
pgrep -af "backup.sh"
ps aux | grep backup.sh

# Graceful kill (SIGTERM — lets script clean up)
kill $(pgrep -f "backup.sh")

# Force kill (SIGKILL — use if graceful kill doesn't work after ~10s)
kill -9 $(pgrep -f "backup.sh")

# Kill process tree (also kills child processes spawned by the job)
pkill -TERM -P $(pgrep -f "backup.sh")    # Graceful
pkill -KILL -P $(pgrep -f "backup.sh")    # Forceful

# Kill by PID file
kill $(cat /var/run/myjob.pid)

# After killing a flock-managed job, remove stale lock file
rm -f /tmp/myjob.lock
```

---

## 9. Stopping the cron daemon

```bash
# Stop crond (all scheduled jobs pause immediately)
sudo systemctl stop cron         # Ubuntu/Debian
sudo systemctl stop crond        # CentOS/RHEL

# Restart crond (pick up config changes, clear stuck state)
sudo systemctl restart cron

# Disable crond at boot (won't start on reboot)
sudo systemctl disable cron
sudo systemctl enable cron       # Re-enable

# Status check
sudo systemctl status cron
sudo systemctl is-active cron    # Prints "active" or "inactive"
```
