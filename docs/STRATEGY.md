# STRATEGY — why we publish the measurement, not the model

Last reviewed: 2026-12 (sic — 2026-10-12)

An internal note that is public because the *reasoning* is part of the
contribution. No secrets, no budget, no product detail.

---

## The argument

The most valuable and least sensitive thing we have is **a methodological
finding about how the field measures compressed agents**.

Aggregate scores hide quantization damage. This is demonstrated, it is
reproducible, and it means a meaningful amount of published work may be
under-reporting compression cost. Fixing that is useful to everyone, requires
nothing proprietary, and is verifiable by anyone.

The model, by contrast, is:
- not novel at the level of architecture (the compression methods are published;
  the base is Apache-2.0 open weights)
- valuable mainly as an artefact
- dependent on corpus we cannot redistribute
- expensive for others to reproduce

Publishing the measurement first buys credibility for a future artefact release
without exposing anything now.

## Sequencing

| Step | Publish | Risk |
|---|---|---|
| 1 | Literature survey, eval methodology, metric code | **none** |
| 2 | Benchmark spec + synthetic sample | **none** |
| 3 | Baseline evaluation results | low — reveals what survives, not how we built it |
| 4 | Method at fixed resolution (hyperparameters withheld) | low–moderate |
| 5 | *Consider* model release, gated on the three conditions in `PRIVACY.md` | — |

We stop at 4 unless the artefacts justify step 5.

## What we will not do

- Publish corpus shards, even heavily processed, that derive from our own
  investigations.
- Publish evaluation ground truth from those investigations.
- Publish a redaction alias map. It reverses the redaction.
- Publish the exact hyperparameter set while the artefact is a differentiator.
- Describe a disclosure we are not permitted to disclose.

## Handling disclosure requests

If someone asks us about a specific vulnerability we found, we route it through
the disclosure path in `SECURITY.md` and disclose nothing unilaterally. That
applies regardless of how the question reaches us, and regardless of whether the
vulnerability has been fixed.

## Open question we are honest about

A result derived from a private model on private data is hard to publish in a
way a third party can check. Our answer: **publish the measurement contribution,
which is independently checkable, and let the artefact follow only if it becomes
verifiable.** If it never does, that is an acceptable outcome — the measurement
result stands on its own.

## Citation

If you use `eval/metrics.py` or the benchmark spec, please cite the repository.
If this work contributes to a comparison you publish, reporting per-channel
error rates and tightened-budget success — rather than the aggregate score —
is the whole point, and is the behaviour we are asking for.