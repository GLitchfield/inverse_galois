#!/usr/bin/env bash
# Install systemd USER timers that run the IGP24 research + audit loops HEADLESSLY (via
# scripts/run_headless_agent.sh -> `claude -p`), so they run 24/7 independent of any interactive
# Claude session. Replaces the old in-session crons, which stalled whenever the main thread hit a
# permission prompt while unattended.
#
#   igp24-research.timer   every 2h at :41   -> one deep research dive, records to auto_log + commits
#   igp24-audit.timer      daily at 08:17    -> one self-audit pass,   records to auto_log + commits
#   igp24-build.timer      every 3h at :23   -> one greenlit build off docs/build_backlog.md Ready,
#                                               produces+gates+enqueues candidates, records + commits
#
# Persistent=true => a run missed while the box was asleep/off fires on next wake. enable-linger keeps
# user timers running with no login session (same mechanism as the search daemon).
#
# Run:  bash scripts/install_headless_loops.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER="$REPO/scripts/run_headless_agent.sh"
UNIT="$HOME/.config/systemd/user"
mkdir -p "$UNIT"
chmod +x "$RUNNER"

loginctl enable-linger "$(whoami)" 2>/dev/null || true

cat > "$UNIT/igp24-research.service" <<EOF
[Unit]
Description=IGP24 headless research dive (one hands-off deep-research pass)
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$RUNNER research
TimeoutStartSec=2400
EOF

cat > "$UNIT/igp24-research.timer" <<EOF
[Unit]
Description=IGP24 research dive every 2 hours
[Timer]
OnCalendar=*-*-* 00/2:41:00
Persistent=true
[Install]
WantedBy=timers.target
EOF

cat > "$UNIT/igp24-audit.service" <<EOF
[Unit]
Description=IGP24 headless self-audit (one hands-off audit pass)
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$RUNNER audit
TimeoutStartSec=2400
EOF

cat > "$UNIT/igp24-audit.timer" <<EOF
[Unit]
Description=IGP24 self-audit daily at 08:17
[Timer]
OnCalendar=*-*-* 08:17:00
Persistent=true
[Install]
WantedBy=timers.target
EOF

cat > "$UNIT/igp24-build.service" <<EOF
[Unit]
Description=IGP24 headless build (one greenlit construction off the backlog -> enqueued candidates)
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$RUNNER build
TimeoutStartSec=3600
EOF

cat > "$UNIT/igp24-build.timer" <<EOF
[Unit]
Description=IGP24 build loop every 3 hours at :23
[Timer]
OnCalendar=*-*-* 00/3:23:00
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now igp24-research.timer igp24-audit.timer igp24-build.timer
echo "installed. timers:"
systemctl --user list-timers --all 'igp24-*' --no-pager
