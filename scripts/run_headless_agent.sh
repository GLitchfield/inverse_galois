#!/usr/bin/env bash
# Headless Claude Code runner for the hands-off IGP24 downtime loops, invoked by systemd timers
# (igp24-research.timer / igp24-audit.timer) so research + audit run 24/7 WITHOUT a live interactive
# session.
#
# WHY: the old approach used in-session Claude crons. Those fire only while the interactive REPL is
# alive AND idle, and — worse — the main thread BLOCKS the moment it hits a permission prompt, so an
# unattended session stalls everything (no cron fires, nothing records) until a human clicks approve.
# A headless `claude -p` run has no human attached, so it never blocks on approval; systemd + linger
# (already used by the search daemon) makes it truly session-independent.
#
# AUTH: uses the claude.ai SUBSCRIPTION. ANTHROPIC_API_KEY is unset here defensively (it was a
# low-credit key that took precedence over the subscription and broke headless runs). Per the user's
# explicit "full autonomy" choice we pass --dangerously-skip-permissions so the run is never gated.
#
# Usage: run_headless_agent.sh {research|audit}
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
export PATH="$HOME/.local/bin:$PATH"        # systemd's minimal PATH lacks ~/.local/bin (the claude CLI)

KIND="${1:-research}"
MODEL="${IGP_HEADLESS_MODEL:-claude-opus-4-8}"   # Opus (2026-07-02: Fable dives hit the subscription session limit; reverted per user)
EFFORT="${IGP_HEADLESS_EFFORT:-high}"            # reasoning effort; verified valid via `claude --effort`
PROMPT_FILE="$REPO/scripts/headless_prompts/${KIND}.md"
LOG="$REPO/logs/headless_${KIND}.log"
JSON="$REPO/logs/.headless_${KIND}.json"         # last run's raw json result (for the cost summary)
mkdir -p "$REPO/logs"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "run_headless_agent: unknown kind '$KIND' (no $PROMPT_FILE)" >&2
  exit 2
fi

echo "===== $(date -Is) headless ${KIND} run starting (model ${MODEL}, effort ${EFFORT}) =====" >> "$LOG"
# --output-format json so the run reports total_cost_usd + usage; json goes to $JSON, warnings to $LOG.
env -u ANTHROPIC_API_KEY claude -p "$(cat "$PROMPT_FILE")" \
  --model "$MODEL" --effort "$EFFORT" \
  --output-format json --dangerously-skip-permissions \
  > "$JSON" 2>> "$LOG"
rc=$?
.venv/bin/python "$REPO/scripts/headless_cost_summary.py" "$JSON" >> "$LOG" 2>&1
echo "===== $(date -Is) headless ${KIND} run finished (exit ${rc}) =====" >> "$LOG"
