# Continuous Learning Setup

Run knowledge-engine on a schedule so it accumulates knowledge autonomously.

## How It Works

The scheduler checks `knowledge/schedule.yaml` every 15 minutes (via cron or
systemd timer) and runs any tasks that are due. Each task is a named action
(research, distill, export, etc.) with its own model, schedule, and parameters.

State and config are kept separate:

- `knowledge/schedule.yaml` — what to run and when (config, commit this)
- `knowledge/state.yaml` — last run times and outcomes (runtime state, gitignore)

## Setup

```bash
# 1. Install and configure
cp examples/continuous-learning/config.yaml ke.yaml
cp examples/continuous-learning/schedule.yaml knowledge/schedule.yaml

# Edit the schedule to fit your topics
vim knowledge/schedule.yaml

# 2. Test — run all due tasks once
ke schedule --once

# 3. Test a specific task
ke schedule --task daily-research-ml
```

## Automation Options

### Cron (simplest)

```bash
# Add to crontab: crontab -e
*/15 * * * * cd /path/to/your/project && ke schedule --once >> logs/heartbeat.log 2>&1
```

### systemd timer (more reliable on Linux)

Create `/etc/systemd/user/ke-heartbeat.service`:

```ini
[Unit]
Description=knowledge-engine heartbeat

[Service]
Type=oneshot
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/ke schedule --once
```

Create `/etc/systemd/user/ke-heartbeat.timer`:

```ini
[Unit]
Description=knowledge-engine heartbeat timer

[Timer]
# Wall-clock timer — avoids drift (use OnCalendar, not OnUnitActiveSec)
OnCalendar=*:0/15

[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now ke-heartbeat.timer
systemctl --user status ke-heartbeat.timer
```

## Monitor

```bash
# Check what ran and when
ke status

# View token usage over last 7 days
# (ke budget report — coming soon)

# View recent mutations
tail -n 20 knowledge/mutation.log | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(f\"{e['timestamp'][:16]}  {e['action']:8}  {e['title'][:50]}  score={e['gate_score']:.2f}\")
"
```

## Customizing the Schedule

The schedule format supports:

- `daily 02:30` — every day at 02:30
- `weekly monday 04:00` — every Monday at 04:00
- `weekly monday,wednesday,friday 08:00` — Mon/Wed/Fri at 08:00
- `interval 60m` — every 60 minutes

For research tasks, choose topics that are:

- Specific enough to produce atomic notes
- Changing fast enough to warrant weekly research
- Within your daily token budget

## Budget Planning

With `token_budget_daily: 500000` and Sonnet:

- 1 research session (2 waves + skeptic) ≈ 30,000–50,000 tokens
- Budget supports ≈ 10–15 sessions per day
- Local model sessions are free (Ollama, GPU)

Adjust `token_budget_daily` in ke.yaml to match your Anthropic plan.
