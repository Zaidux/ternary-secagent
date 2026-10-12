# eval

`metrics.py` — reference implementation of the evaluation contract in
[`../docs/EVAL-DESIGN.md`](../docs/EVAL-DESIGN.md).

Standard library only. No dependencies.

## Why these metrics

Aggregate scores hide compression damage in tool-calling agents. A 2026 study
found **no aggregate score change surviving multiple-comparison correction**
while per-call failures rose **2.5x** — because quantization *rescales the
existing failure set* rather than adding new failure modes, and the aggregate
metric's error budget absorbed the increase. Tightening the budget from 10
tolerated errors to 2 widened the FP16-vs-4-bit gap from 1.3 to 16.7 points.

Full analysis: [`../docs/EVAL-DESIGN.md`](../docs/EVAL-DESIGN.md).

## Usage

```python
from metrics import analyze_trajectories, compare_runs, load_jsonl

fp16 = analyze_trajectories(load_jsonl("fp16.jsonl"), run_id="fp16")
tern = analyze_trajectories(load_jsonl("ternary.jsonl"), run_id="ternary")

# Report these -- never the aggregate alone
print(tern.per_channel())            # per-channel error rates, separately
print(tern.budget_curve())           # success under tightened error budgets
print(tern.recovery_rate())          # recovery after a failed call
print(compare_runs(fp16, tern).amplification_report())
```

## API

| Function / method | Purpose |
|---|---|
| `analyze_trajectories(records, run_id)` | build a report from episode dicts |
| `compare_runs(reference, candidate)` | FP16 baseline vs compressed candidate |
| `load_jsonl(path)` | iterate episode dicts |
| `TrajectoryReport.per_channel()` | per-channel failure rate / total calls |
| `TrajectoryReport.success_at_budget(k)` | success with <=k tolerated failures |
| `TrajectoryReport.recovery_rate()` | of episodes with >=1 failure, share completed |
| `TrajectoryReport.budget_curve()` | success across several budgets |
| `RunComparison.amplification()` | candidate / reference, per channel |
| `RunComparison.failure_set_correlation()` | rank corr. of per-episode failure counts |
| `RunComparison.amplification_report()` | everything, ready to serialize |

## Rules this module encodes

1. **Channels stay separate.** Combining them is what made the original
   measurement look flat.
2. **`out_of_scope` beats the not-in-tool-list heuristic.** Out-of-scope means a
   valid tool aimed at a forbidden target -- a specific signal, not a
   hallucination.
3. **Fallback when `error` is missing.** `ok: false` plus a tool absent from
   `valid_tools` counts as tool-name hallucination.
4. **Truncation is its own outcome**, never folded into "not completed".

## Limitations

- Does not score finding *correctness* -- only process reliability. Ground-truth
  scoring is harness-specific and lives with each eval family.
- Spearman correlation uses ties-averaged ranks on failure counts; adequate for
  the 400-1000 episode range, thin below ~30.
- Assumes one `error` string per failed call. Harnesses that emit structured
  error objects need a normaliser upstream.

## License

MIT -- see [`../LICENSE`](../LICENSE).
