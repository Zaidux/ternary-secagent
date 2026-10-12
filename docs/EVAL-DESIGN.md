# Evaluation design

The measurement problem, in full. This is the core methodological contribution
of this repository.

---

## 1. The problem

Compression damage to **agentic** models is systematically under-reported.

A 2026 study of 4-bit post-training weight quantization on tool-calling agents
evaluated on τ²-bench across two open-weight model families, dense and MoE
variants, two domains, and eight cells of 456 episodes each at 16-, 8-, and
4-bit weights.

**The aggregate score showed nothing.** No cell showed a score change that
survived multiple-comparison correction. In the cell carrying the largest
process damage, equivalence testing bounded the change within ±7.5 points.

**But per-step, the picture was different.** Quantization raised failed tool
calls per episode from 1.45 to 3.64 — a 2.5× increase in event volume
(1,646 → 1,646* scaled), swelling the ≥5-failure tail from 51 to 173 of 456
episodes and stretching trajectories from 7.3 to 9.4 turns.

---

## 2. Two mechanisms cause the masking

### 2.1 Quantization rescales the failure set; it does not create failures

- The BF16 and INT4 distributions over hallucinated tool names were **nearly
  identical**; invariance held at 8 bits too.
- Failure-set rank correlation across precisions: **≥ 0.94**.
- **0.18% novel events.**

Each domain opened exactly one failure channel, and quantization only amplified
the one already open. Telecom produced zero entity errors; retail produced zero
tool-name events.

**Implication for evaluation:** if the failure set is unchanged, the repair
target is the *baseline* error rate. Compression will multiply whatever is left.

**Implication for training:** the highest-leverage intervention is reducing
pre-existing errors at full precision, because compression then has a smaller
base to multiply. This predicts that data targeting hallucination, abstention,
and verified negatives returns more under compression than data targeting
new capabilities. We have not tested this yet; see [`FINDINGS.md`](FINDINGS.md).

### 2.2 The aggregate metric carries an error budget

The aggregate score stayed flat because the benchmark's **ten-error budget
absorbed the extra failures**. The agentic loop recovered from many of them and
the budget paid for the rest.

Tightening the budget re-exposes the damage — same episodes, same models, same
seeds:

| Error budget K | FP16 vs 4-bit gap |
|---|---|
| 10 (default) | 1.3 points |
| 5 | 7.5 points |
| 2 | **16.7 points** |

Same tightening cost FP16 about 10 points and INT4 about 25 — a ~13× widening of
the gap.

**Recovery rate after at least one failed call was 55% at both precisions.**
Quantization did not weaken recovery. It produced more failures to recover from,
and the budget paid for them. Error-driven recovery also *refunded part of the
compute quantization saved* — the speedup was partly spent buying back mistakes.

---

## 3. What we require of an evaluation

### 3.1 Report these four things

1. **Per-channel error rates**, separately, never combined:
   tool-name hallucination · argument errors · malformed output · out-of-scope
   calls. Report as a fraction of total tool calls.

2. **Success under tightened error budgets** (K=2 and K=5 alongside your normal
   budget). This is the metric that moves. The aggregate score is not.

3. **Failure-set rank correlation** against the full-precision baseline, plus the
   fraction of novel events. ≥0.9 with ~0 novel events confirms the rescaling
   model on your data; anything else means compression introduced new failure
   modes, which is a worse and differently-shaped problem.

4. **Error-driven recovery rate.** A drop means compression damaged the agent's
   ability to recover from its own mistakes — distinct from producing more of
   them.

### 3.2 Report separately

- **Truncation rate.** Episodes hitting a turn or time budget are a failure mode
  in their own right and must not be silently folded into "not completed."
- **Calls per episode.** Longer trajectories at lower precision are a cost, even
  when the score is flat.

### 3.3 Do not report

- The aggregate score alone. Ever.
- "Equivalent within ±X" without the budget it was measured under.
- Retention percentages without the precision, the calibration data, and the
  group-lock status of the eval set.

---

## 4. Long-context discipline

A separate trap, relevant because agentic contexts are long.

**Needle-in-a-haystack is not a sufficient test.** It measures lexical retrieval,
which models pass easily; real questions need reasoning, and that is where
mid-context loss compounds. RULER found that a *single* distractor already
degrades performance and four compound it. Distractor **diversity** matters:
repeating the same synthetic paragraph is the friendliest possible setup, and
real documents drop recall further.

Requirements for long-context evaluation:

- **Multi-needle, not single-needle.** RULER showed multi-needle is meaningfully
  harder.
- **Diverse real distractors**, not repeated synthetic ones.
- **Sweep the needle position** and report the curve, not a mean. Performance is
  U-shaped; a mean hides it. All 17 long-context models in RULER showed
  degradation as input grew — larger windows moved the middle further out rather
  than removing it.
- **Measure state retention across turns.** An agent that establishes facts in
  turn 2 and needs them in turn 20 is a different test from a static needle.
- **Measure truncation detection.** Does the model notice its context was cut?

---

## 5. Sub-2-bit needs its own diagnostic

Compression at ≈4-bit degrades signal; structure survives and training-free repair
can work.

At ≈2-bit and below, **Computation Collapse** — key components stop functioning
and the signal is destroyed in early layers. This is **irreversible**:
quantizing only the first two layers of Llama-3 to 2-bit dropped factual recall
100% → 41.65%, and 30 subsequent full-precision layers could not recover it.

**Any sub-2-bit evaluation must check for early-layer degradation explicitly.**
If it is present, no fine-tuning recovers it, and the honest conclusion is that
the compression method is not fit for that architecture — not that more training
data would help.

---

## 6. Leakage control

- **Group-locked splits.** The same finding, contract, session, or target never
  straddles train/val/test. Not "deduplicated" — *group-locked*, because two
  examples from one investigation are not independent.
- **Post-cutoff test sets.** A dataset is only leak-resistant if it postdates the
  base model's training. Where the base model is recent, this is a live
  constraint: a set that was leak-resistant against a May 2025 base may be
  in-distribution for an August 2026 base.
- **Deduplicate before splitting**, not after. Duplicate detection is a
  correctness requirement, not a cost optimisation.
- **Provenance per item:** source URL, licence, retrieval date. A corpus you
  cannot audit is a corpus you cannot defend.

---

## 7. Implementation

[`eval/metrics.py`](../eval/metrics.py) implements §3. Reference implementation
for [`bench/SPEC.md`](../bench/SPEC.md). No dependencies beyond the standard
library.

```python
from metrics import analyze_trajectories, compare_runs

fp16 = analyze_trajectories(load_jsonl("fp16.jsonl"), run_id="fp16")
tern = analyze_trajectories(load_jsonl("ternary.jsonl"), run_id="ternary")

print(tern.per_channel())
print(tern.budget_curve())
print(compare_runs(fp16, tern).amplification_report())
```

---

## References

- *Flat Score, Amplified Failures: How the Error Budget Masks Damage in
  Quantized LLM Agents* — arXiv:2607.27275
- *From Signal Degradation to Computation Collapse* — ACL 2026 Findings
- *Attend to Your Own Thoughts (ScaleQ-1.58)* — arXiv:2608.01078
- *CAT-Q* — arXiv:2606.26650, ICML 2026 Oral
- RULER; *Lost-in-the-Middle Is Still Real in 2026*; Chroma *Context Rot*
- *How Small Can You Go? LoRA Fine-Tuning 270M–8B* — arXiv:2606.08051
- *FORGE* — ICSE 2026