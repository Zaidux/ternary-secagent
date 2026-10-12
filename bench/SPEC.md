# Benchmark specification

**Version 0.1 — draft. No real data published.**

The trajectory schema and eval families. Ground truth for the tool-calling gate
is **not** released, because it derives from real investigations — see
[`../PRIVACY.md`](../PRIVACY.md).

---

## 1. Trajectory record schema

One JSON object per episode. Consumed by [`../eval/metrics.py`](../eval/metrics.py).

```jsonc
{
  "episode_id": "ep-0001",
  "task_id": "tgt-0042",           // target or scenario this ran against
  "split": "test",                 // train | val | test
  "group_id": "inv-8812",          // investigation / session / contract
  "model": "qwen3.8-27b-ternary",  // checkpoint + precision tag
  "run_id": "ternary-r1",

  "valid_tools": ["nmap", "fetch", "semgrep", "browser.snapshot"],

  "steps": [
    {"type": "tool_call", "tool": "nmap", "args": {"target": "..."},
     "ok": true, "turn": 1},
    {"type": "tool_call", "tool": "scoutx", "args": {},
     "ok": false, "error": "unknown_tool", "turn": 4},
    {"type": "tool_call", "tool": "semgrep", "args": {"rule": "..."},
     "ok": false, "error": "argument_error", "turn": 7},
    {"type": "tool_call", "tool": "exploit.run", "args": {"..."},
     "ok": false, "error": "out_of_scope", "turn": 9},
    {"type": "text", "text": "..."}
  ],

  "completed": false,
  "truncated": true,               // hit turn/time budget, not a clean finish
  "outcome": "budget_exhausted"
}
```

### Field requirements

| Field | Required | Notes |
|---|---|---|
| `episode_id` | yes | unique within a run |
| `group_id` | yes | **the leakage control.** Splits are group-locked on this. |
| `valid_tools` | yes | enables tool-name hallucination detection independently of harness error vocabulary |
| `steps[].type` | yes | `tool_call` or `text` |
| `steps[].ok` | yes | `false` counts as a failure even if `error` is absent |
| `steps[].error` | recommended | see below |
| `truncated` | yes | **never** fold into `completed: false` |
| `model`, `run_id` | yes | every run is labelled; unlabelled results are not comparable |

### Error vocabulary

Harnesses disagree, so classification does not depend on it. `error` values we
recognise:

| Value | Channel |
|---|---|
| `unknown_tool`, `no_such_tool`, `hallucinated_tool` | `tool_name_hallucination` |
| `argument_error` | `argument_error` |
| `malformed_output` | `malformed_output` |
| `out_of_scope` | `out_of_scope` |
| anything else, or `ok:false` with no `error` | `other` |

**Precedence:** an explicit `out_of_scope` wins over the generic
"tool not in `valid_tools`" heuristic. Out-of-scope means *a valid tool aimed at
a forbidden target* — a specific, deliberate signal that should not be
reclassified.

**Fallback:** if `error` is absent but the tool is not in `valid_tools`, it is
counted as `tool_name_hallucination`. This catches harnesses that report only
`ok: false`.

---

## 2. Eval families

Four families, each with its own held-out set. **No item is reused across
families.**

### E1 — Coding
Function-level and repository-level tasks: generate, repair, localize, explain.
Includes line-localization tasks with ground-truth line numbers.

Public sanity checks are reported **separately and never as the headline**.

### E2 — Security knowledge and reasoning
CWE classification · attack-pattern reasoning · tool and CLI knowledge ·
vulnerability chaining (low/info → high/critical escalation) · abstention items
where *declining is the correct answer* · agentic security episodes.

### E3 — Tool-calling agentic gate
Full episodes against real targets. **The primary gate.** Metrics per
[`../docs/EVAL-DESIGN.md`](../docs/EVAL-DESIGN.md).

### E4 — Per-capability specs
Long-context discipline (multi-needle with real distractors, state retention
across turns, truncation detection) · triage from report text alone · impact
re-verification · report generation (unsupported-claim rate is primary).

---

## 3. Leakage control

| Requirement | Rule |
|---|---|
| **Group-locked splits** | The same `group_id` never appears in more than one of train/val/test. Two examples from one investigation are not independent. |
| **Post-cutoff test sets** | Test items must postdate the base model's training. Where the base is recent this is a live constraint — a set leak-resistant against a May 2025 base may be in-distribution for an August 2026 one. |
| **Deduplicate before splitting** | Duplicate detection is a correctness requirement, not a cost optimisation. |
| **Provenance per item** | `source_url`, `licence`, `retrieved_at`. A corpus you cannot audit is one you cannot defend. |
| **Record the cutoff date** | In every results table. |

---

## 4. What we publish

- this specification
- `sample/` — synthetic only, clearly labelled, safe to read
- the metric implementation

We do **not** publish real targets, real findings, manifests, or ground truth.

---

## 5. Sample data

[`sample/`](sample/) contains a small **synthetic** trajectory set built only to
exercise the metrics: correct calls, tool-name hallucination, argument errors,
out-of-scope attempts, truncation, and a recovery case.

It contains no real hostnames, paths, requests, or vulnerabilities, and its
"findings" are not real. It is a fixture, not an example.