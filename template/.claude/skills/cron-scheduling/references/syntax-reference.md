# Cron syntax reference

_Read this file when: the user asks about cron expressions, field meanings, special characters, schedule examples, or wants help writing/understanding a specific schedule._

---

## Table of contents

1. [Field reference](#1-field-reference)
2. [Special characters](#2-special-characters)
3. [Shorthand macros](#3-shorthand-macros)
4. [Expression examples library](#4-expression-examples-library)
5. [Expression builder — step-by-step](#5-expression-builder)
6. [Edge cases and gotchas](#6-edge-cases-and-gotchas)

---

## 1. Field reference

```
position  field          valid range    notes
────────  ─────────────  ───────────    ──────────────────────────────────────
1         minute         0–59
2         hour           0–23
3         day-of-month   1–31           see gotcha §6.1
4         month          1–12           or JAN FEB MAR APR MAY JUN
                                        JUL AUG SEP OCT NOV DEC
5         day-of-week    0–7            0 and 7 both = Sunday
                                        or SUN MON TUE WED THU FRI SAT
6+        command        any string     rest of the line, including arguments
```

---

## 2. Special characters

### `*` — wildcard (every value)

```bash
* * * * *           # Every minute of every hour every day
0 * * * *           # Top of every hour, every day
0 0 * * *           # Midnight every day
```

### `,` — list (multiple specific values)

```bash
0,30 * * * *        # At :00 and :30 of every hour
0 8,12,17 * * *     # At 8 AM, 12 PM, and 5 PM
0 0 1,15 * *        # 1st and 15th of every month at midnight
0 0 * 1,4,7,10 *    # Midnight on the 1st of Jan, Apr, Jul, Oct
```

### `-` — range (inclusive)

```bash
0 9-17 * * *        # Every hour from 9 AM to 5 PM (9,10,11,...,17)
0 0 * * 1-5         # Monday through Friday at midnight
0 9 * * 1-5         # 9 AM on weekdays only
30 8-18 * * 1-5     # :30 every hour during business hours Mon–Fri
```

### `/` — step (every N)

```bash
*/5 * * * *         # Every 5 minutes
*/15 * * * *        # Every 15 minutes (0, 15, 30, 45)
0 */2 * * *         # Every 2 hours at :00 (0, 2, 4, ..., 22)
0 */6 * * *         # Every 6 hours (0, 6, 12, 18)
*/10 8-18 * * 1-5   # Every 10 min during business hours, weekdays
```

### Combining `,` `-` `/`

```bash
0,30 9-17 * * 1-5   # :00 and :30 during business hours Mon–Fri
*/15 8,20 * * *     # Every 15 min at 8 AM and 8 PM
0 6-22/2 * * *      # Every 2 hours from 6 AM to 10 PM (6,8,10,...,22)
```

---

## 3. Shorthand macros

These replace the five-field expression entirely:

| Macro | Equivalent | Meaning |
|-------|-----------|---------|
| `@reboot` | _(none)_ | Once at system startup |
| `@yearly` / `@annually` | `0 0 1 1 *` | Jan 1st at midnight |
| `@monthly` | `0 0 1 * *` | 1st of every month at midnight |
| `@weekly` | `0 0 * * 0` | Every Sunday at midnight |
| `@daily` / `@midnight` | `0 0 * * *` | Every day at midnight |
| `@hourly` | `0 * * * *` | Every hour on the hour |

```bash
@reboot  /opt/scripts/startup.sh >> /var/log/startup.log 2>&1
@daily   /opt/scripts/cleanup.sh >> /var/log/cleanup.log 2>&1
@weekly  /opt/scripts/weekly_report.sh >> /var/log/weekly.log 2>&1
```

---

## 4. Expression examples library

### Time-based patterns

```bash
# Every minute
* * * * *

# Every N minutes
*/5 * * * *          # Every 5 min
*/10 * * * *         # Every 10 min
*/15 * * * *         # Every 15 min
*/30 * * * *         # Every 30 min (same as 0,30 * * * *)

# Specific minute of every hour
0 * * * *            # :00 — top of every hour
15 * * * *           # :15 past every hour
45 * * * *           # :45 past every hour

# Every N hours
0 */2 * * *          # Every 2 hours
0 */3 * * *          # Every 3 hours
0 */4 * * *          # Every 4 hours
0 */6 * * *          # Every 6 hours
0 */12 * * *         # Every 12 hours (midnight and noon)
```

### Daily patterns

```bash
0 0 * * *            # Midnight
0 1 * * *            # 1 AM
30 2 * * *           # 2:30 AM (good for overnight backups)
0 6 * * *            # 6 AM
45 7 * * *           # 7:45 AM (before 8 AM standup)
0 12 * * *           # Noon
0 18 * * *           # 6 PM
0 22 * * *           # 10 PM
59 23 * * *          # 11:59 PM
```

### Weekday patterns

```bash
0 8 * * 1-5          # 8 AM Monday–Friday
0 8 * * 1            # 8 AM Monday only
0 8 * * 5            # 8 AM Friday only
0 8 * * 1,3,5        # 8 AM Mon, Wed, Fri
0 8 * * 2,4          # 8 AM Tue, Thu
0 0 * * 6,0          # Midnight on Sat and Sun (weekends)
0 0 * * 0            # Midnight every Sunday
*/5 9-17 * * 1-5     # Every 5 min during business hours
0,30 9-17 * * 1-5    # Every 30 min during business hours
```

### Monthly patterns

```bash
0 2 1 * *            # 1st of every month at 2 AM
0 2 15 * *           # 15th of every month at 2 AM
0 2 1,15 * *         # 1st and 15th at 2 AM
0 2 28-31 * *        # Last few days of month (not always reliable — see §6.1)
0 0 1 */3 *          # First day of every quarter (Jan, Apr, Jul, Oct)
0 0 1 1 *            # January 1st at midnight (same as @yearly)
```

### Specific calendar patterns

```bash
0 9 * * 1#1          # First Monday of the month (GNU cron only)
0 2 * 1 *            # Every day in January at 2 AM
0 2 * 12 *           # Every day in December at 2 AM
0 2 25 12 *          # December 25th at 2 AM
0 9 * 3-5 1-5        # 9 AM weekdays in March, April, May
```

---

## 5. Expression builder

When a user describes a schedule in plain English, map it to a cron expression using this process:

### Step 1 — Identify frequency type

| User says | Start with |
|-----------|-----------|
| "every X minutes" | `*/X * * * *` |
| "every X hours" | `0 */X * * *` |
| "every day at TIME" | `MIN HOUR * * *` |
| "every weekday at TIME" | `MIN HOUR * * 1-5` |
| "every Monday at TIME" | `MIN HOUR * * 1` |
| "every week on DAY at TIME" | `MIN HOUR * * DOW` |
| "every month on the Nth" | `MIN HOUR N * *` |
| "every year on DATE" | `MIN HOUR DOM MON *` |
| "at startup / on boot" | `@reboot` |

### Step 2 — Convert time to fields

```
"3:30 AM"   →  minute=30  hour=3
"8:00 AM"   →  minute=0   hour=8
"12:00 PM"  →  minute=0   hour=12
"5:45 PM"   →  minute=45  hour=17
"11:59 PM"  →  minute=59  hour=23
"midnight"  →  minute=0   hour=0
"noon"      →  minute=0   hour=12
```

### Step 3 — Convert day names to numbers

```
Sunday=0, Monday=1, Tuesday=2, Wednesday=3,
Thursday=4, Friday=5, Saturday=6, Sunday=7 (also valid)
```

### Step 4 — Worked examples

| Plain English | Expression |
|---------------|-----------|
| Every 5 minutes | `*/5 * * * *` |
| Every hour at :30 | `30 * * * *` |
| Daily at 2:30 AM | `30 2 * * *` |
| Weekdays at 7:45 AM | `45 7 * * 1-5` |
| Every Monday at 9 AM | `0 9 * * 1` |
| First of every month at midnight | `0 0 1 * *` |
| Every 15 min during business hours | `*/15 9-17 * * 1-5` |
| Twice a day at 8 AM and 8 PM | `0 8,20 * * *` |
| Every Sunday at 3:45 AM | `45 3 * * 0` |
| Every 6 hours starting midnight | `0 */6 * * *` |
| Every 30 min on weekends | `*/30 * * * 6,0` |
| Jan 1st at midnight | `0 0 1 1 *` |

---

## 6. Edge cases and gotchas

### 6.1 — Day-of-month AND day-of-week are ORed, not ANDed

When you set both `day-of-month` and `day-of-week` to something other than `*`, cron runs if EITHER condition matches — not both:

```bash
0 2 15 * 5   # Runs on the 15th of every month AND every Friday
             # NOT "the 15th only if it's a Friday"

# To run ONLY on Fridays that fall on the 15th, use a script-level check:
0 2 15 * *  [ "$(date +%u)" = "5" ] && /opt/scripts/myjob.sh
```

### 6.2 — Minimum interval is 1 minute

Cron wakes up once per minute. For sub-minute scheduling, use a loop inside a per-minute job:

```bash
# Run every 10 seconds (6 times per minute)
* * * * * for i in 1 2 3 4 5 6; do /opt/scripts/poll.sh & sleep 10; done
```

### 6.3 — Timezone is the system timezone

Cron uses the system timezone (`/etc/localtime`). To force a specific timezone:

```bash
# Set in the crontab file header
TZ=UTC
0 2 * * * /opt/scripts/backup.sh

# Or inline per job (GNU cron)
TZ=America/New_York 0 9 * * 1-5 /opt/scripts/report.sh
```

### 6.4 — `@reboot` timing

`@reboot` runs after crond starts, which may be before your application, database, or network are ready. Add a sleep or use `systemd` service ordering for production use:

```bash
@reboot sleep 30 && /opt/scripts/startup.sh >> /var/log/startup.log 2>&1
```

### 6.5 — Last day of month

There is no `L` in standard cron (that's Quartz/enterprise schedulers). Workaround:

```bash
# Run on the last day of the month using a script check
0 2 28-31 * * [ "$(date -d tomorrow +%d)" = "01" ] && /opt/scripts/month_end.sh
```

### 6.6 — February and 31-day months

`0 0 31 * *` runs only in months that have 31 days. If you want end-of-month reliably, use the technique in §6.5.

### 6.7 — AWS / GCP / Quartz cron differences

Standard Unix cron ≠ cloud schedulers:

| Feature | Unix cron | AWS EventBridge | Quartz (Java) |
|---------|-----------|----------------|---------------|
| Fields | 5 | 6 (adds year) | 6–7 (adds seconds/year) |
| `?` in day fields | No | Required in one of dom/dow | Supported |
| `L` (last) | No | Yes | Yes |
| `W` (weekday) | No | No | Yes |
| `#` (Nth weekday) | GNU only | No | Yes |

AWS example — every day at 2 AM UTC:
```
cron(0 2 * * ? *)
#               ^ year field required; ? required in dom or dow (not both)
```
