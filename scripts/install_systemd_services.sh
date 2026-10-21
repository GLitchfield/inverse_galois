#!/usr/bin/env bash
# Install resilient systemd USER services for the 24/7 IGP24 search, so the pipeline survives a
# terminal close / WSL teardown instead of dying with the session (the old failure mode).
#
#   igp24-searchd.service    the search daemon (consumer)         Restart=on-failure
#   igp24-dashboard.service  read-only dashboard on :5057         Restart=on-failure
#   igp24-tick.timer         runs `search_ctl tick` every 15 min  (producers + rank + refresh)
#   igp24-feed.timer         runs `search_ctl feed` every 5 min   (produce-only; keeps queue full)
#
# enable-linger keeps the user manager (and these services) running with no login session, and
# auto-starts them when WSL next boots. The daemon exits cleanly only on `search_ctl stop`
# (code 0 -> on-failure does NOT restart), so stop still works; crashes restart after 10s.
#
# Run:  bash scripts/install_systemd_services.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO/.venv/bin/python"
UNIT="$HOME/.config/systemd/user"
mkdir -p "$UNIT"

cat > "$UNIT/igp24-searchd.service" <<EOF
[Unit]
Description=IGP24 search daemon
[Service]
Type=simple
WorkingDirectory=$REPO
ExecStart=$PY scripts/searchd.py
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
EOF

cat > "$UNIT/igp24-dashboard.service" <<EOF
[Unit]
Description=IGP24 read-only dashboard
[Service]
Type=simple
WorkingDirectory=$REPO
ExecStart=$PY scripts/dashboard/app.py --port 5057
MemoryMax=4G
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
EOF

cat > "$UNIT/igp24-tick.service" <<EOF
[Unit]
Description=IGP24 search maintenance tick (producers + rank + ensure daemon)
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$PY scripts/search_ctl.py tick
EOF

cat > "$UNIT/igp24-tick.timer" <<EOF
[Unit]
Description=Run the IGP24 tick periodically
[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Persistent=true
[Install]
WantedBy=timers.target
EOF

# feed = lightweight produce-only cycle on a FAST timer (5 min), so the daemon's queue stays topped
# up between the 15-min full ticks instead of draining to 0 and idling (throughput lever B).
cat > "$UNIT/igp24-feed.service" <<EOF
[Unit]
Description=IGP24 fast produce-only feed (keeps the daemon queue topped up)
[Service]
Type=oneshot
WorkingDirectory=$REPO
ExecStart=$PY scripts/search_ctl.py feed
EOF

cat > "$UNIT/igp24-feed.timer" <<EOF
[Unit]
Description=Run the IGP24 produce-only feed frequently
[Timer]
OnBootSec=3min
OnUnitActiveSec=5min
Persistent=true
[Install]
WantedBy=timers.target
EOF

loginctl enable-linger "$USER" || true
systemctl --user daemon-reload
systemctl --user enable --now igp24-searchd.service igp24-dashboard.service igp24-tick.timer \
  igp24-feed.timer
echo "--- installed; status ---"
systemctl --user --no-pager --type=service list-units 'igp24-*'
systemctl --user --no-pager list-timers 'igp24-*'
