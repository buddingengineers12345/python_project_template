# Cron environments reference

_Read this file when: the user is on macOS, Windows, Docker, Kubernetes, GitHub Actions, Node.js, or Python — i.e., anything that isn't standard Linux cron._

---

## Table of contents

1. [macOS — launchd](#1-macos--launchd)
2. [Windows — Task Scheduler & schtasks](#2-windows--task-scheduler)
3. [Docker containers](#3-docker-containers)
4. [Kubernetes CronJob](#4-kubernetes-cronjob)
5. [AWS EventBridge + Lambda](#5-aws-eventbridge--lambda)
6. [GitHub Actions scheduled workflows](#6-github-actions)
7. [Node.js — node-cron](#7-nodejs--node-cron)
8. [Python — APScheduler & schedule](#8-python)
9. [Environment comparison table](#9-comparison-table)

---

## 1. macOS — launchd

macOS marks cron as legacy. The native scheduler is **launchd**, using XML plist files.

### Plist file locations

| Location | Purpose |
|----------|---------|
| `~/Library/LaunchAgents/` | Per-user jobs (run when user is logged in) |
| `/Library/LaunchAgents/` | Per-user jobs (run for any user that logs in) |
| `/Library/LaunchDaemons/` | System-wide jobs (run as root, no user session needed) |

### Calendar-based job (equivalent to cron schedule)

```xml
<!-- ~/Library/LaunchAgents/com.myapp.backup.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.myapp.backup</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/me/scripts/backup.sh</string>
    </array>

    <!-- Run daily at 2:00 AM -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>2</integer>
        <key>Minute</key><integer>0</integer>
    </dict>

    <!-- Catch up on missed runs after sleep/off -->
    <key>RunAtLoad</key><false/>

    <key>StandardOutPath</key><string>/tmp/backup.log</string>
    <key>StandardErrorPath</key><string>/tmp/backup.err</string>
</dict>
</plist>
```

### Interval-based job (run every N seconds)

```xml
<!-- Run every 5 minutes (300 seconds) -->
<key>StartInterval</key>
<integer>300</integer>
```

### StartCalendarInterval field keys

| Key | Values |
|-----|--------|
| `Minute` | 0–59 |
| `Hour` | 0–23 |
| `Day` | 1–31 |
| `Month` | 1–12 |
| `Weekday` | 0–7 (0 and 7 = Sunday) |

### Management commands

```bash
# Load (activate) — first time or after editing
launchctl load ~/Library/LaunchAgents/com.myapp.backup.plist

# Unload (deactivate)
launchctl unload ~/Library/LaunchAgents/com.myapp.backup.plist

# Run immediately (for testing)
launchctl start com.myapp.backup

# Stop a running job
launchctl stop com.myapp.backup

# Check status (exit code in 3rd column; 0 = OK, null = not running)
launchctl list | grep com.myapp

# macOS 10.11+ alternative
launchctl enable gui/$(id -u)/com.myapp.backup
launchctl bootout gui/$(id -u)/com.myapp.backup
```

---

## 2. Windows — Task Scheduler

### schtasks CLI (Command Prompt / PowerShell)

```powershell
# Create — daily at 2 AM
schtasks /create /tn "MyApp Backup" /tr "C:\Scripts\backup.bat" /sc daily /st 02:00 /ru SYSTEM /f

# Create — every 5 minutes
schtasks /create /tn "MyApp Poll" /tr "C:\Scripts\poll.bat" /sc minute /mo 5 /ru SYSTEM /f

# Update — change schedule time
schtasks /change /tn "MyApp Backup" /st 03:00

# Enable / disable
schtasks /change /tn "MyApp Backup" /enable
schtasks /change /tn "MyApp Backup" /disable

# Run immediately
schtasks /run /tn "MyApp Backup"

# Delete
schtasks /delete /tn "MyApp Backup" /f

# Query all tasks
schtasks /query /fo LIST /v

# Query one task
schtasks /query /tn "MyApp Backup" /fo LIST /v
```

### PowerShell — richer task creation

```powershell
# Create a repeating daily task
$action   = New-ScheduledTaskAction -Execute "C:\Scripts\backup.bat"
$trigger  = New-ScheduledTaskTrigger -Daily -At "2:00AM"
$settings = New-ScheduledTaskSettingsSet `
              -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
              -RunOnlyIfNetworkAvailable `
              -StartWhenAvailable           # Run missed tasks when machine wakes
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask `
  -TaskName "MyApp Backup" `
  -Action $action -Trigger $trigger -Settings $settings -Principal $principal

# Update trigger
$task = Get-ScheduledTask -TaskName "MyApp Backup"
$task.Triggers[0].StartBoundary = "2024-01-01T03:00:00"
Set-ScheduledTask -InputObject $task

# Remove
Unregister-ScheduledTask -TaskName "MyApp Backup" -Confirm:$false
```

---

## 3. Docker containers

### Approach A — cron inside the container (simple)

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY mycrontab /etc/cron.d/myapp
RUN chmod 0644 /etc/cron.d/myapp && crontab /etc/cron.d/myapp
RUN touch /var/log/cron.log

# Print Docker env vars to /etc/environment so cron can read them
CMD ["bash", "-c", "printenv > /etc/environment && cron -f"]
```

```bash
# mycrontab (no username field — already installed via crontab command)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

* * * * * root echo "tick" >> /var/log/cron.log 2>&1
0 2 * * * root /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Approach B — host-level cron triggers container (recommended for production)

Keep your host crontab clean and let it drive the container:

```bash
# Run a one-shot command inside a named running container
0 2 * * * docker exec myapp_container bash -c '/app/scripts/backup.sh >> /app/logs/backup.log 2>&1'

# Run a fresh disposable container
0 2 * * * docker run --rm --env-file /etc/myapp.env myapp/backup:latest
```

### Docker Compose variant

```bash
0 2 * * * docker compose -f /opt/myapp/docker-compose.yml run --rm backup
```

---

## 4. Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: production
spec:
  schedule: "30 2 * * *"               # Standard cron syntax
  timeZone: "America/New_York"          # Kubernetes 1.27+ (requires TZ data)
  concurrencyPolicy: Forbid             # Forbid|Allow|Replace
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  startingDeadlineSeconds: 300          # Skip if can't start within 5 min
  jobTemplate:
    spec:
      backoffLimit: 2                   # Retry failed pods up to 2 times
      template:
        spec:
          restartPolicy: OnFailure      # Never|OnFailure
          containers:
            - name: backup
              image: myapp/backup:latest
              command: ["/app/backup.sh"]
              env:
                - name: DB_URL
                  valueFrom:
                    secretKeyRef:
                      name: db-secret
                      key: url
              resources:
                requests: { memory: "256Mi", cpu: "100m" }
                limits:   { memory: "512Mi", cpu: "500m" }
```

```bash
# List all CronJobs
kubectl get cronjobs -n production

# Check recent Job runs
kubectl get jobs -n production --sort-by=.metadata.creationTimestamp

# Trigger a manual run
kubectl create job --from=cronjob/db-backup manual-backup-$(date +%s) -n production

# Suspend a CronJob (stops new runs, doesn't kill current)
kubectl patch cronjob db-backup -p '{"spec":{"suspend":true}}' -n production

# Resume
kubectl patch cronjob db-backup -p '{"spec":{"suspend":false}}' -n production

# Delete
kubectl delete cronjob db-backup -n production
```

---

## 5. AWS EventBridge + Lambda

### AWS cron syntax differences from Unix

```
cron(minute  hour  day-of-month  month  day-of-week  year)
#                                                    ^^^^
#     Year field is REQUIRED in AWS (doesn't exist in Unix cron)
#     Use ? in EITHER day-of-month OR day-of-week (not both, not neither)
```

```bash
# Daily at 2 AM UTC
cron(0 2 * * ? *)

# Every weekday at 8 AM EST (UTC-5 = 13:00 UTC)
cron(0 13 ? * MON-FRI *)

# Every 5 minutes
rate(5 minutes)

# Every hour
rate(1 hour)
```

### AWS CLI

```bash
# Create EventBridge rule
aws events put-rule \
  --name "daily-backup" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED \
  --region us-east-1

# Add Lambda as target
aws events put-targets \
  --rule "daily-backup" \
  --targets "Id=1,Arn=arn:aws:lambda:us-east-1:123456789:function:BackupFn"

# Disable / enable rule
aws events disable-rule --name "daily-backup"
aws events enable-rule  --name "daily-backup"

# Delete rule (must remove targets first)
aws events remove-targets --rule "daily-backup" --ids 1
aws events delete-rule --name "daily-backup"
```

### Terraform

```hcl
resource "aws_cloudwatch_event_rule" "daily_backup" {
  name                = "daily-backup"
  schedule_expression = "cron(0 2 * * ? *)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "backup_lambda" {
  rule      = aws_cloudwatch_event_rule.daily_backup.name
  target_id = "BackupLambda"
  arn       = aws_lambda_function.backup.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_backup.arn
}
```

---

## 6. GitHub Actions

```yaml
# .github/workflows/scheduled.yml
name: Nightly Tasks

on:
  schedule:
    # Standard Unix cron syntax (UTC only)
    - cron: '0 2 * * *'          # 2 AM UTC daily
    - cron: '0 8 * * 1-5'        # 8 AM UTC weekdays (second trigger)
  workflow_dispatch:              # Allow manual run from GitHub UI

jobs:
  backup:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Run backup
        env:
          DB_URL: ${{ secrets.DATABASE_URL }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: ./scripts/backup.sh

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Nightly backup failed',
              body: `Run: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`
            })
```

**GitHub Actions cron caveats:**
- All times are UTC — there is no timezone support
- Minimum interval: 5 minutes
- Heavily loaded repos may have 15–60 min delays during peak hours
- Scheduled workflows are disabled after 60 days of repo inactivity
- Only runs on the default branch

---

## 7. Node.js — node-cron

```bash
npm install node-cron
```

```javascript
const cron = require('node-cron');

// Basic usage
cron.schedule('0 2 * * *', () => {
  console.log('Running nightly backup…');
  runBackup();
});

// With timezone and explicit start control
const task = cron.schedule('30 7 * * 1-5', async () => {
  try {
    await generateMorningReport();
  } catch (err) {
    console.error('Report failed:', err.message);
    await notifyOpsTeam(err);
  }
}, {
  scheduled: false,             // Don't auto-start
  timezone: 'America/New_York'
});

task.start();   // Start the task
task.stop();    // Pause (keeps registration)
task.destroy(); // Remove permanently

// Validate an expression without scheduling
const valid = cron.validate('*/5 * * * *');  // true

// Graceful shutdown
process.on('SIGTERM', () => {
  task.stop();
  process.exit(0);
});
```

---

## 8. Python

### Option A — `schedule` (simple, synchronous)

```bash
pip install schedule
```

```python
import schedule
import time

def backup():
    print("Running backup…")

def report():
    print("Sending weekly report…")

# Human-readable scheduling DSL
schedule.every().day.at("02:00").do(backup)
schedule.every().monday.at("09:00").do(report)
schedule.every(5).minutes.do(lambda: print("Heartbeat"))
schedule.every().hour.at(":30").do(lambda: print("Half-past"))

# Blocking run loop
while True:
    schedule.run_pending()
    time.sleep(30)          # Check every 30 seconds
```

### Option B — APScheduler (production-grade, async-capable)

```bash
pip install apscheduler
```

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import atexit, logging

logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler(timezone='UTC')

# Event listener for monitoring
def job_listener(event):
    if event.exception:
        logging.error(f'Job {event.job_id} failed: {event.exception}')
    else:
        logging.info(f'Job {event.job_id} succeeded')

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Add jobs
scheduler.add_job(
    func=run_backup,
    trigger=CronTrigger(hour=2, minute=0, timezone='UTC'),
    id='nightly_backup',
    name='Nightly Database Backup',
    max_instances=1,           # Prevent overlap
    coalesce=True,             # If missed, run once (not multiple)
    misfire_grace_time=300,    # Allow up to 5-min late start
    replace_existing=True
)

scheduler.add_job(
    func=generate_report,
    trigger=CronTrigger(day_of_week='mon-fri', hour=8, minute=0),
    id='morning_report'
)

scheduler.add_job(
    func=heartbeat,
    trigger=IntervalTrigger(minutes=5),
    id='heartbeat'
)

scheduler.start()
atexit.register(scheduler.shutdown)  # Clean shutdown on exit

# Modify a running job
scheduler.reschedule_job('nightly_backup', trigger=CronTrigger(hour=3))
scheduler.pause_job('heartbeat')
scheduler.resume_job('heartbeat')
scheduler.remove_job('morning_report')

# List all jobs
for job in scheduler.get_jobs():
    print(f'{job.id}: next run = {job.next_run_time}')
```

### APScheduler with FastAPI / Flask

```python
# FastAPI integration
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

---

## 9. Comparison table

| Feature | Linux cron | macOS launchd | Windows Task Scheduler | Kubernetes CronJob | GitHub Actions | node-cron | APScheduler |
|---------|-----------|--------------|----------------------|-------------------|---------------|-----------|-------------|
| Syntax | 5-field cron | XML plist | GUI / schtasks CLI | 5-field cron | 5-field cron | 5-field cron | Python DSL |
| Timezone support | System TZ | Plist key | GUI setting | `spec.timeZone` | UTC only | Option field | Per-job |
| Catch-up on miss | No | `RunAtLoad` | `StartWhenAvailable` | `startingDeadline` | No | No | `coalesce` |
| Overlap prevention | `flock` | One instance | Setting | `concurrencyPolicy` | Manual | Manual | `max_instances` |
| Retry on failure | No | No | Limited | `backoffLimit` | No | Manual | Manual |
| Secret injection | env vars | Keychain | Credential manager | K8s Secrets | GitHub Secrets | env vars | env vars |
| Min interval | 1 min | 1 sec | 1 min | 1 min | 5 min | 1 min | 1 sec |
