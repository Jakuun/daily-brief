#!/usr/bin/env python3
"""
Daily Brief — missed-run watchdog (runs on the Mac, via launchd at 07:30).

Why this exists
---------------
Added 12 Aug 2026, after five briefs went missing in three weeks (27 Jul,
30 Jul, 8 Aug, 11 Aug, 12 Aug) with no signal of any kind. The brief task
writes its archive file as the LAST step, so a run that died at 90% left
exactly as much behind as one that died at 5%: nothing. No file, no error,
no notification. The failure was only ever discovered at breakfast.

This closes that gap. At 07:30 it asks one question — does today's archive
file exist? — and if not, says so loudly.

What it CANNOT do: re-run the brief. The brief is a Cowork scheduled task,
not a launchd job, and there's no shell hook to trigger it. So the recovery
step is manual and deliberately spelled out in the notification:
    Cowork sidebar -> daily-media-brief -> Run now

Dependencies: Python 3 standard library only.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF_DIR = os.path.dirname(HERE)              # .../Daily Brief
ARCHIVE = os.path.join(BRIEF_DIR, "Archive")
FEEDS = os.path.join(HERE, "feeds")
LOG = os.path.join(HERE, ".watchdog.log")


def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def notify(title, message):
    """macOS banner. Best-effort: never let a notification failure crash the check."""
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification {json.dumps(message)} with title {json.dumps(title)}'],
            check=False, timeout=10,
        )
    except Exception as e:
        log(f"notification failed: {e}")


def prefetch_state(today):
    """Best-effort read of what the pre-fetch actually did, so the alert can
    distinguish 'no data' from 'data was fine, the run itself died'."""
    p = os.path.join(FEEDS, "status.json")
    if not os.path.exists(p):
        return "pre-fetch status unknown (no status.json)"
    try:
        with open(p) as f:
            s = json.load(f)
    except Exception:
        return "pre-fetch status unreadable"
    finished = (s.get("run_finished") or "")[:10]
    if finished != today:
        return f"pre-fetch data is stale (last finished {finished or 'never'})"
    return "feeds were fine" if s.get("ok") else "feeds ran but reported problems"


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    target = os.path.join(ARCHIVE, f"{today}.md")

    if os.path.exists(target) and os.path.getsize(target) > 0:
        log(f"OK — {today}.md present ({os.path.getsize(target)} bytes)")
        # Clear any stale alert marker from a previous bad day.
        marker = os.path.join(FEEDS, "missed_run.json")
        if os.path.exists(marker):
            # Never let housekeeping fail the check itself. A watchdog that
            # crashes on a GOOD day is worse than no watchdog: it would sit in
            # launchd reporting a non-zero exit every morning and train you to
            # ignore it. (Caught in testing 12 Aug 2026 — os.remove raised
            # PermissionError and took the whole run down on a healthy day.)
            try:
                os.remove(marker)
                log("cleared previous missed-run marker")
            except OSError as e:
                log(f"could not clear missed-run marker (harmless): {e}")
        return 0

    why = prefetch_state(today)
    log(f"*** MISSING — no brief for {today}. Context: {why}")

    with open(os.path.join(FEEDS, "missed_run.json"), "w") as f:
        json.dump({"date": today, "detected_at": datetime.now().isoformat(),
                   "context": why}, f, indent=2)

    notify("Daily Brief didn't run",
           f"No brief for {today} ({why}). "
           f"Cowork sidebar -> daily-media-brief -> Run now.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
