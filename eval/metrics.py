"""Metrics for evaluating compression damage to tool-calling agents.

Why this module exists
----------------------
Aggregate benchmark scores hide quantization damage. In a 2026 study of 4-bit
post-training quantization on tool-calling agents (tau^2-bench, 456 episodes per
cell, two model families, dense and MoE), the aggregate score showed **no change
surviving multiple-comparison correction** -- while per-call failures rose up to
**2.5x**.

Two properties caused the masking:

1. Quantization **rescales the model's existing failure set** rather than
   introducing new failure types (failure-set rank correlation >= 0.94 against
   the full-precision baseline; 0.18% novel events).
2. The aggregate metric carries an **error budget**. Extra failures were paid
   for by that budget rather than by the score.

So an evaluator who reports only the headline number will conclude the
compression was free. It was not.

What this module computes
-------------------------
``analyze_trajectories`` produces four things:

* **Per-channel error rates** -- tool-name hallucination, argument errors,
  malformed output, out-of-scope calls -- reported *separately*, never combined.
* **Success under tightened error budgets** (K=2, K=5, K=10). This is the metric
  that actually moves.
* **Failure-set rank correlation** against a reference run, which confirms or
  refutes the "rescaling, not new failures" model on *your* data.
* **Error-driven recovery rate** -- of episodes with >=1 failed call, what
  fraction still completed the task.

Usage
-----
    from metrics import analyze_trajectories, compare_runs

    fp16 = analyze_trajectories(load_jsonl("fp16.jsonl"))
    tern = analyze_trajectories(load_jsonl("ternary.jsonl"))

    print(tern.per_channel())        # <- read these
    print(tern.success_at_budget(2)) # <- and this one
    print(compare_runs(fp16, tern).amplification_report())

Only ``per_channel()`` and ``success_at_budget()`` should ever be quoted as
headline numbers.

License: MIT.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Literal, Sequence

__all__ = [
    "FailureChannel",
    "Episode",
    "TrajectoryReport",
    "RunComparison",
    "analyze_trajectories",
    "compare_runs",
    "load_jsonl",
]

# Failure channels are kept separate on purpose. Combining them is what made
# the original measurement look flat.
FailureChannel = Literal[
    "tool_name_hallucination",  # called a tool not in the declared tool list
    "argument_error",  # malformed args, wrong types, missing required fields
    "malformed_output",  # unparseable / invalid-JSON tool call
    "out_of_scope",  # attempted an action the scope rules forbid
    "other",
]

ALL_CHANNELS: tuple[FailureChannel, ...] = (
    "tool_name_hallucination",
    "argument_error",
    "malformed_output",
    "out_of_scope",
    "other",
)

# Harness error strings we treat as tool-name hallucination. Harnesses disagree
# on vocabulary, so classification falls back to the declared tool list too.
_HALLUCINATION_ERRORS = frozenset({"unknown_tool", "hallucinated_tool", "no_such_tool"})


@dataclass
class Episode:
    """One agent episode.

    Attributes:
        episode_id: unique identifier.
        valid_tools: tools the harness declared for this episode.
        total_calls: every tool call attempted.
        failed_calls: calls that errored, including hallucinated tool names,
            malformed arguments, and out-of-scope attempts.
        channel_counts: per-channel breakdown of ``failed_calls``.
        completed: whether the task reached its success condition.
        truncated: whether the episode hit a turn/time budget rather than
            finishing -- truncation is a failure mode in its own right and
            should not be silently folded into "not completed".
    """

    episode_id: str
    valid_tools: frozenset[str]
    total_calls: int
    failed_calls: int
    channel_counts: Counter
    completed: bool
    truncated: bool = False
    extra: dict = field(default_factory=dict)

    def failures_at(self, budget: int) -> int:
        """Return whether this episode fails under an error budget of ``budget``.

        An episode with more than ``budget`` failed calls is scored as failed
        regardless of whether the agent loop recovered and eventually reported
        success. This is the whole point: the default budget hides damage.
        """
        return int(self.failed_calls > budget)


@dataclass
class TrajectoryReport:
    """Aggregate statistics for one run of the benchmark."""

    run_id: str
    n_episodes: int
    n_truncated: int
    channel_totals: Counter
    total_calls: int
    n_completed: int

    # ---------------------------------------------------------------- scores
    def aggregate_score(self) -> float:
        """The naive headline metric. Do not use alone."""
        return self.n_completed / self.n_episodes if self.n_episodes else 0.0

    def per_channel(self) -> dict[str, float]:
        """Failure rate per channel, as a fraction of all tool calls.

        This is the number that shows damage the aggregate score hides.
        """
        if not self.total_calls:
            return {c: 0.0 for c in ALL_CHANNELS}
        return {
            c: self.channel_totals.get(c, 0) / self.total_calls for c in ALL_CHANNELS
        }

    def per_channel_counts(self) -> dict[str, int]:
        return {c: self.channel_totals.get(c, 0) for c in ALL_CHANNELS}

    def success_at_budget(self, budget: int) -> float:
        """Success rate under a tightened error budget.

        Args:
            budget: maximum tolerated failures per episode. The reference study
                reported gaps of 1.3 / 7.5 / 16.7 points at K=10 / 5 / 2.
        """
        if not self.n_episodes:
            return 0.0
        return sum(1 for e in self.episodes if not e.failures_at(budget)) / len(
            self.episodes
        )

    def recovery_rate(self) -> float:
        """Of episodes with >=1 failed call, the fraction that still completed.

        A drop here means compression has damaged the agent's ability to recover
        from its own mistakes -- a different failure from producing more of them.
        """
        hurt = [e for e in self.episodes if e.failed_calls > 0]
        if not hurt:
            return float("nan")
        return sum(1 for e in hurt if e.completed) / len(hurt)

    episodes: list[Episode] = field(default_factory=list)

    def budget_curve(self, budgets: Sequence[int] = (2, 3, 5, 10, 20)) -> dict[int, float]:
        return {k: self.success_at_budget(k) for k in budgets}

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "n_episodes": self.n_episodes,
            "n_truncated": self.n_truncated,
            "total_calls": self.total_calls,
            "aggregate_score": round(self.aggregate_score(), 6),
            "per_channel_rate": {k: round(v, 6) for k, v in self.per_channel().items()},
            "per_channel_counts": self.per_channel_counts(),
            "success_by_budget": {k: round(v, 6) for k, v in self.budget_curve().items()},
            "recovery_rate": (
                None if math.isnan(self.recovery_rate()) else round(self.recovery_rate(), 6)
            ),
        }


@dataclass
class RunComparison:
    """A reference run versus a candidate run."""

    reference: TrajectoryReport
    candidate: TrajectoryReport

    def amplification(self) -> dict[str, float]:
        """Per-channel ratio of candidate failure rate to reference failure rate.

        A value of 1.0 means compression changed nothing on that channel.
        The reference study found ratios up to 2.5x on the active channel and
        ~1.0x on channels the domain never exercised.
        """
        ref = self.reference.per_channel()
        cand = self.candidate.per_channel()
        out: dict[str, float] = {}
        for c in ALL_CHANNELS:
            if ref[c] <= 0:
                out[c] = float("nan")  # channel not exercised by the reference
            else:
                out[c] = cand[c] / ref[c]
        return out

    def budget_gap(self, budget: int) -> float:
        """Reference minus candidate success at a given error budget."""
        return self.reference.success_at_budget(budget) - self.candidate.success_at_budget(
            budget
        )

    def failure_set_correlation(self) -> float:
        """Spearman-style rank correlation of per-episode failure counts.

        High correlation (>= ~0.9) with few novel events is the signature of
        *rescaling* rather than *new failure modes*. That distinction matters:
        rescaling means the fix is to reduce the baseline error rate, because
        compression will multiply whatever is left.
        """
        a = sorted(e.failed_calls for e in self.reference.episodes)
        b = sorted(e.failed_calls for e in self.candidate.episodes)
        if not a or not b:
            return float("nan")
        return _spearman(a, b)

    def amplification_report(self) -> dict:
        return {
            "aggregate_gap": round(
                self.reference.aggregate_score() - self.candidate.aggregate_score(), 6
            ),
            "budget_gaps": {k: round(self.budget_gap(k), 6) for k in (2, 3, 5, 10)},
            "per_channel_amplification": {
                k: (None if math.isnan(v) else round(v, 4))
                for k, v in self.amplification().items()
            },
            "failure_set_rank_correlation": (
                None
                if math.isnan(self.failure_set_correlation())
                else round(self.failure_set_correlation(), 4)
            ),
            "reference_recovery_rate": _r(self.reference.recovery_rate()),
            "candidate_recovery_rate": _r(self.candidate.recovery_rate()),
        }


def _r(x: float) -> float | None:
    return None if math.isnan(x) else round(x, 6)


def _rankdata(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 2:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else float("nan")


def _spearman(a: list[float], b: list[float]) -> float:
    return _pearson(_rankdata(a), _rankdata(b))


# --------------------------------------------------------------------- input
def load_jsonl(path: str | Path) -> Iterator[dict]:
    """Yield one episode dict per line from a JSONL trajectory file."""
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def analyze_trajectories(
    records: Iterable[dict], run_id: str = "run"
) -> TrajectoryReport:
    """Build a :class:`TrajectoryReport` from raw episode dicts.

    Expected schema per record (see ``bench/SPEC.md``)::

        {
          "episode_id": "ep-0001",
          "valid_tools": ["nmap", "fetch", "sqlmap"],
          "steps": [
            {"type": "tool_call", "tool": "nmap",        "args": {...}, "ok": true},
            {"type": "tool_call", "tool": "nmap -sV",    "args": {},  "ok": false,
             "error": "unknown_tool"},
            {"type": "tool_call", "tool": "sqlmap",      "args": {"bad": 1},
             "ok": false, "error": "argument_error"}
          ],
          "completed": true,
          "truncated": false
        }

    Channel assignment, in order of precedence:

    ``unknown_tool``        -> ``tool_name_hallucination``
    ``argument_error``      -> ``argument_error``
    ``malformed_output``    -> ``malformed_output``
    ``out_of_scope``        -> ``out_of_scope``
    anything else, or ``ok=false`` with no error -> ``other``
    """
    episodes: list[Episode] = []
    channel_totals: Counter = Counter()
    total_calls = 0
    n_truncated = 0
    n_completed = 0

    for rec in records:
        valid = frozenset(rec.get("valid_tools") or ())
        steps = rec.get("steps") or []
        calls = [s for s in steps if s.get("type") == "tool_call"]
        counts: Counter = Counter()
        failed = 0

        for s in calls:
            err = s.get("error")
            if s.get("ok") and err is None:
                continue
            if s.get("ok") and err not in _HALLUCINATION_ERRORS:
                continue  # genuinely succeeded

            failed += 1
            tool = s.get("tool")
            # Precedence matters. An explicit ``out_of_scope`` is a deliberate,
            # specific signal (valid tool, forbidden target) and must not be
            # swallowed by the generic "not in valid_tools" heuristic below.
            if err == "out_of_scope":
                ch: FailureChannel = "out_of_scope"
            elif err == "argument_error":
                ch = "argument_error"
            elif err == "malformed_output":
                ch = "malformed_output"
            elif err in _HALLUCINATION_ERRORS:
                ch = "tool_name_hallucination"
            elif valid and tool and tool not in valid:
                # Fallback: harness gave no specific error, but the tool is not
                # in the declared set. Counts as hallucination.
                ch = "tool_name_hallucination"
            else:
                ch = "other"
            counts[ch] += 1

        total_calls += len(calls)
        channel_totals.update(counts)

        completed = bool(rec.get("completed"))
        trunc = bool(rec.get("truncated"))
        if completed:
            n_completed += 1
        if trunc:
            n_truncated += 1

        episodes.append(
            Episode(
                episode_id=str(rec.get("episode_id", len(episodes))),
                valid_tools=valid,
                total_calls=len(calls),
                failed_calls=failed,
                channel_counts=counts,
                completed=completed,
                truncated=trunc,
            )
        )

    return TrajectoryReport(
        run_id=run_id,
        n_episodes=len(episodes),
        n_truncated=n_truncated,
        channel_totals=channel_totals,
        total_calls=total_calls,
        n_completed=n_completed,
        episodes=episodes,
    )


def compare_runs(
    reference: TrajectoryReport, candidate: TrajectoryReport
) -> RunComparison:
    """Compare a full-precision reference run against a compressed candidate."""
    return RunComparison(reference=reference, candidate=candidate)


if __name__ == "__main__":  # pragma: no cover - smoke test
    demo = [
        {
            "episode_id": "ep-0",
            "valid_tools": ["nmap", "fetch"],
            "steps": [
                {"type": "tool_call", "tool": "nmap", "args": {}, "ok": True},
                {"type": "tool_call", "tool": "scout", "args": {}, "ok": False,
                 "error": "unknown_tool"},
            ],
            "completed": True,
        },
        {
            "episode_id": "ep-1",
            "valid_tools": ["fetch"],
            "steps": [
                {"type": "tool_call", "tool": "fetch", "args": {}, "ok": True},
                {"type": "tool_call", "tool": "exploit", "args": {}, "ok": False,
                 "error": "out_of_scope"},
            ],
            "completed": False,
            "truncated": True,
        },
    ]
    r = analyze_trajectories(demo, run_id="demo")
    print(json.dumps(r.to_dict(), indent=2))