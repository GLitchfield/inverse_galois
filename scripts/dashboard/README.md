# IGP24 search dashboard

Read-only, single-page dashboard for the long-running search. Zero new deps (stdlib
`http.server` + Chart.js from CDN); reads the data the search already keeps.

```bash
uv run python scripts/dashboard/app.py        # default port 5057
# then open http://localhost:5057
```

Five panels, auto-refreshing every 10s:

- **Coverage trajectory** — groups + scoreable signatures over time, reconstructed from the git
  history of `data/targets/realized.csv` (cached by commit sha in `data/processed/`).
- **Queue pipeline** — live `search.db` status counts (queued / building / submitted / verified /
  failed / dup / skipped).
- **Throughput** — posts/day (from the daemon's rate-limit ledger) and verified/day.
- **Producers** — per-producer bandit weight (the same ranking the daemon claims by); the table of
  n / scoreable / sole is in the JSON at `/api/data`.
- **Sole realizers** — the teamCount==0 groups, which producer found each, and disc size.

It only reads; it never writes search state. Safe to run alongside the daemon.
