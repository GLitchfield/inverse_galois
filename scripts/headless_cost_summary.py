"""Print a one-line TOKEN-usage summary from a `claude -p --output-format json` result file.

Used by run_headless_agent.sh to log the real per-dive token usage (input/output/cache + web-tool
counts) so the model/interval can be tuned from data. Dollar cost is intentionally omitted: on a
claude.ai subscription total_cost_usd is a notional API figure that doesn't reflect actual usage --
tokens do. Fail-soft: never raises.
"""

import json
import sys


def main(path: str) -> None:
    try:
        d = json.load(open(path))
    except Exception as e:  # a crashed/killed run may leave no/partial json
        print(f"[cost] unparseable json output ({path}): {e}")
        return
    u = d.get("usage") or {}
    st = u.get("server_tool_use") or {}
    in_t = u.get("input_tokens") or 0
    out_t = u.get("output_tokens") or 0
    cr = u.get("cache_read_input_tokens") or 0
    cc = u.get("cache_creation_input_tokens") or 0
    print("[usage] total_tokens={} in={} out={} cache_read={} cache_create={} turns={} "
          "web_search={} web_fetch={} is_error={}".format(
              in_t + out_t + cr + cc, in_t, out_t, cr, cc, d.get("num_turns"),
              st.get("web_search_requests"), st.get("web_fetch_requests"), d.get("is_error")))
    r = (d.get("result") or "").strip()
    if r:
        print("[result]", r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
