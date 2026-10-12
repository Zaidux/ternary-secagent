# Ternary Security Agent

**Can a sub-2-bit (1.58-bit) model retain cybersecurity, code, and tool-calling
capability well enough to run as an autonomous security agent?**

An open research programme. Nothing is trained yet.

---

## What this repository is

This is the **public** half. It contains:

- the research question and its motivation
- a survey of the relevant literature
- **the evaluation methodology** — our main methodological contribution so far
- a reference implementation of the metrics that methodology requires

## What this repository is *not*

The trained model, the training corpus, and the training recipe are **not public**
and are not planned to be. See [`PRIVACY.md`](PRIVACY.md) for what is withheld and
why.

This split is deliberate. See [`docs/STRATEGY.md`](docs/STRATEGY.md).

---

## The core measurement problem

Anyone evaluating a quantized agentic model by its aggregate score will conclude
the quantization was free. **It will be wrong.**

On τ²-bench, post-training 4-bit weight quantization of tool-calling agents showed
**no aggregate score change that survived multiple-comparison correction** — yet
per-call failures rose **up to 2.5×** (+17.6 points per task). One channel
(tool-name hallucination) went from 19.5% to 38.3% of all tool calls.

Two properties make this a measurement failure rather than a surprise:

1. **Quantization rescales the existing failure set; it does not create new
   failures.** Failure-set rank correlation against the full-precision model was
   ≥0.94, with 0.18% novel events.
2. **Aggregate scores have an error budget, and it absorbs the damage.** Tighten
   the number of tolerated errors per episode and the gap reappears:

   | Error budget K | FP16 vs 4-bit gap |
   |---|---|
   | 10 (default) | 1.3 points |
   | 5 | 7.5 points |
   | 2 | **16.7 points** |

   Same episodes, same models — only the budget changed.

Recovery rate after a failed tool call was identical at both precisions (~55%).
Quantization did not weaken recovery; it produced more failures to recover from,
and the budget paid for them.

**If you are evaluating a quantized agent, report per-channel error rates and
success under a tightened error budget.** See [`docs/EVAL-DESIGN.md`](docs/EVAL-DESIGN.md)
and [`eval/metrics.py`](eval/metrics.py).

---

## A second warning: sub-2-bit is not 4-bit

Mechanistic work distinguishes two quantization failure modes:

- **Signal Degradation** (≈4-bit) — representations impaired, structure intact.
  The correct signal is still present. Training-free repair can work.
- **Computation Collapse** (≈2-bit and below) — key components stop functioning;
  the signal is destroyed in early layers. **Irreversible.**

Concretely: quantizing only the **first two layers** of Llama-3 to 2-bit dropped
factual recall from 100% to 41.65%, and *30 subsequent full-precision layers
could not recover it*.

1.58-bit is below 2-bit. Methods built for sub-2-bit — CAT-Q's sliding-layer
reconstruction with learnable modulation, and its successor's domain-matched
calibration — exist specifically to avoid this. But any sub-2-bit evaluation
should explicitly check for early-layer degradation.

---

## Research programme

| Stage | Question |
|---|---|
| Baseline | Does ternary compression of a strong VLM preserve security + code + tool-calling? Where does it break first? |
| Calibration | Does **domain-matched** calibration recover what generic calibration destroys? |
| Recovery | Does domain fine-tuning on a frozen ternary base restore agentic capability without recovering pre-existing error modes? |
| Deployment | Can it run inside a scope-enforcing harness, read its own scope, find vulnerabilities, and justify every change it makes? |

---

## Status

| Component | State |
|---|---|
| Literature survey | ✅ [`docs/RELATED-WORK.md`](docs/RELATED-WORK.md) |
| Evaluation methodology | ✅ [`docs/EVAL-DESIGN.md`](docs/EVAL-DESIGN.md) |
| Metric implementation | ✅ [`eval/`](eval/) |
| Benchmark specification | 🚧 [`bench/SPEC.md`](bench/SPEC.md) |
| Baseline model evaluation | ⬜ not started |
| Training corpus | ⬜ not started |
| Training | ⬜ not started |
| Findings | ⬜ [`docs/FINDINGS.md`](docs/FINDINGS.md) |

---

## Related work

- **CAT-Q** — *Cost-efficient and Accurate Ternary Quantization for LLMs*, ICML
  2026 (Oral). Apache-2.0. `IntelChina-AI/BitTern`
- **ScaleQ-1.58 / AYOT** — *Attend to Your Own Thoughts*, arXiv:2608.01078
- **BitNet b1.58** — arXiv:2402.17764 · **BitNet b1.58 2B4T** — arXiv:2504.12285
- **BiLLM** — ICML 2024 · **LoftQ** — NeurIPS 2023
- **LoTA-QAF** — NeurIPS 2025 · **Low-Rank Ternary Adaptation** — ECCV 2026
- **FORGE** — smart-contract vulnerability dataset, ICSE 2026
- **FuzzingBrain-Bench** — arXiv:2608.25158

Full annotations in [`docs/RELATED-WORK.md`](docs/RELATED-WORK.md).

---

## Licence

Code: MIT — see [`LICENSE`](LICENSE).
Third-party model weights and datasets retain their own licences; see
[`NOTICE.md`](NOTICE.md).

## Security scope

This project is for **authorized** security research only. See
[`SECURITY.md`](SECURITY.md).