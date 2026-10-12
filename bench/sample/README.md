# Synthetic fixture — not real data

`synthetic_trajectories.jsonl` exists **solely to exercise `eval/metrics.py`.**

It contains:

- no real hostnames (all use the reserved `.invalid` TLD, RFC 2606)
- no real requests, responses, paths, or credentials
- no real vulnerabilities, and the "findings" described in the text are invented
- no data derived from any real engagement

It is a **fixture**, not an example. Do not cite it as a result and do not
treat its contents as representative of anything.

## Coverage

The five episodes exercise every code path in the metric implementation:

| Episode | Exercises |
|---|---|
| `syn-0001` | Clean episode, zero failures |
| `syn-0002` | `unknown_tool` + `argument_error`, then **recovers** |
| `syn-0003` | `out_of_scope` + `unknown_tool`, ends **truncated** |
| `syn-0004` | `unknown_tool` only |
| `syn-0005` | `malformed_output`, then recovers |

## Run it

```bash
python3 -c "
import json, sys
sys.path.insert(0, '../eval')
from metrics import analyze_trajectories, load_jsonl
r = analyze_trajectories(load_jsonl('synthetic_trajectories.jsonl'), 'fixture')
print(json.dumps(r.to_dict(), indent=2))
"
```

Verified output: 5 episodes, 16 tool calls, 1 truncated, aggregate score **0.8**,
recovery rate 0.75, and a non-zero rate on every channel except `other`
(tool-name hallucination 3, argument error 1, malformed output 1,
out-of-scope 1).
