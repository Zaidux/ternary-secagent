# Method

Published at **method-shape resolution**. The pipeline structure and the
evaluation contract are public. Exact hyperparameters, corpus composition
ratios, and dataset identifiers are withheld — see [`../PRIVACY.md`](../PRIVACY.md)
and [`STRATEGY.md`](STRATEGY.md).

---

## The claim being tested

> Sub-2-bit (1.58-bit) weight compression of a capable vision-language model
> preserves cybersecurity, code, and tool-calling capability well enough to run
> as an autonomous security agent inside a scope-enforcing harness.

We treat this as a falsifiable question with a specific failure mode, not as a
tuning exercise.

---

## Pipeline

```
                     ┌─────────────────────────────────────────┐
   base model ──────►│ (A) TERNARY PTQ                        │
   (open weights,    │  post-training, CAT-Q-style:           │
    Apache-2.0)      │  sliding-window reconstruction +       │
                     │  learnable modulation +                │
                     │  softened ternarization                │
                     │  W ∈ {−1, 0, +1}, 1.58 bits            │
                     └──────────────┬──────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────────────┐
   domain corpus ───►│ (B) DOMAIN CALIBRATION                 │
   (proprietary)     │  self-generated reasoning traces over  │
                     │  domain prompts (AYOT-style)           │
                     └──────────────┬──────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────────────┐
                     │ (C) RECOVERY SFT                       │
                     │  LoRA on the FROZEN ternary base,      │
                     │  ternary forward / FP16 adapter         │
                     └──────────────┬──────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────────────┐
                     │ (D) EVALUATION                         │
                     │  per-channel + tightened budget        │
                     │  group-locked, post-cutoff splits      │
                     └──────────────┬──────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────────────────┐
                     │ (E) SCOPE-ENFORCED DEPLOYMENT         │
                     │  the model proposes; the gate disposes │
                     └─────────────────────────────────────────┘
```

Stages A, B, and C are the compression-and-recovery pipeline. D is where the
measurement problem lives and is the part we contribute. E is the deployment
contract.

---

## Stage A — Ternary post-training quantization

Post-training, not quantization-aware training. Rationale: native ternary QAT
requires training from scratch at trillions of tokens (BitNet b1.58 2B4T used 4T),
which is out of reach outside a handful of groups. PTQ reaches comparable
accuracy at a small fraction of the cost.

Weights map to `{−1, 0, +1}` with a per-group scale. Activations stay at 8 or 16
bits. Two properties matter:

1. **~10× weight-memory reduction** over FP16.
2. **Float multiply becomes integer add/subtract**, so the arithmetic is
   hardware-friendly — but only with specialised kernels. See §"Kernels" below.

We use a released open ternary build rather than deriving our own, both for cost
and to keep our compute budget for the parts that are actually novel.

## Stage B — Domain calibration

The stage that decides whether anything works.

CAT-Q's own Appendix E documents the failure: with generic web-text calibration,
a ternary model scores **0.00** on HumanEval+ and MBPP+. With matched
calibration, 53.98 and 39.15. Same method, same weights, different calibration
data.

AYOT's finding generalizes it: calibrate on **the target model's own generated
reasoning traces over domain prompts**. Self-generated traces outperform traces
from a stronger teacher, because calibration must preserve the specific
reasoning patterns of the model being compressed — not a different model's.

**Consequence:** a group with domain data and no large teacher budget is not
disadvantaged here. That is the most useful property of this whole literature.

## Stage C — Recovery SFT

LoRA on the frozen ternary base. Ternary forward pass, FP16 adapter, gradients
reaching the adapter only.

**What the data is for.** Not primarily to teach security — the base already
knows it. Two jobs:

1. **Restore** what ternary quantization degraded, especially code and structured
   tool use.
2. **Reduce baseline error rates**, because of the rescaling property in
   [`EVAL-DESIGN.md`](EVAL-DESIGN.md) §2.1: compression multiplies whatever
   error rate remains. Halving the baseline halves the post-compression rate
   twice over — once directly, once through the multiplier. This is why
   hallucination-reduction and abstention data should outperform
   capability-teaching data *specifically under compression*, a prediction we
   have not yet tested.

**Tooling caveat.** Stock PEFT/TRL cannot train on a packed ternary checkpoint —
there is no ternary `nn.Linear` in the standard stack. Two viable routes:

- *ternary-native*: train an FP16 adapter directly over the ternary forward pass.
  Precedent exists and runs on consumer hardware.
- *dense-then-compress*: LoRA on the full-precision base, merge, re-ternarize
  with stock tooling.

We run both at an early checkpoint and compare. Published evidence points both
ways — one line of work finds dense LoRA *superior* for task-specific tuning —
so we settle it empirically rather than by argument. They answer different
questions and we label them separately.

## Stage D — Evaluation

The substance of [`EVAL-DESIGN.md`](EVAL-DESIGN.md). Summary of the contract:

- per-channel error rates, reported separately
- success under tightened error budgets (K=2, K=5)
- failure-set rank correlation against the full-precision baseline
- error-driven recovery rate
- group-locked, post-cutoff splits
- sub-2-bit early-layer collapse diagnostic

Four eval families: coding · cybersecurity knowledge and reasoning · tool-calling
agentic gate · per-capability specs.

## Stage E — Scope-enforced deployment

The architectural constraint: **the model's reasoning is never the authority that
grants it permissions.**

```
┌─ scope gate ── authoritative; reads RULES.md, decides in/out of scope
│
├─ model ── chooses tools, forms hypotheses, interprets evidence
├─ evidence store ── requests, responses, logs, reproduction steps
├─ change manager ── diffs plus a required written rationale per change
└─ verification engine ── reruns tests before anything deploys
```

The model may read its own source to self-diagnose, but deploying a change
requires passing tests and an approval gate outside the model.

---

## Kernels — a caveat that applies to every efficiency claim

Ternary weights are not efficiently usable through standard libraries. BitNet's
own model card warns against expecting speed or energy gains via `transformers`;
the specialised CPU and GPU kernels are required.

**So a ternary checkpoint's "1.58-bit" size does not by itself imply a fast
model.** If we report a throughput or energy figure, it comes from a specified
kernel on specified hardware, never from arithmetic on the bit-width. The CAT-Q
deployment table — Qwen3-4B at 1.01 GB, 37 tok/s CPU vs 19 for 4-bit — is the
kind of measurement we require of ourselves.

One further caveat specific to our base: whether the **vision tower** is itself
ternarized is not always stated in export descriptions. If it is not, a strong
screenshot score describes a full-precision vision path, and that confound is
reported rather than buried.

---

## What we will publish when results exist

- Measured per-channel and tightened-budget deltas, FP16 vs ternary.
- Whether the rescaling prediction holds on our data: does training reduce the
  amplification factor, or only the baseline?
- Where the model breaks first, and whether it is recoverable.
- The evaluation harness, so the numbers are reproducible.

What we will not publish: weights, corpus, ground truth, or exact
hyperparameters. See [`../PRIVACY.md`](../PRIVACY.md).