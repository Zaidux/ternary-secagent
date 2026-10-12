# Related work

Annotated survey. Our reading of each paper, including where we think it does
and does not transfer to our setting.

Reviewed 2026-10-12. Citations verified against primary sources.

---

## Ternary / low-bit quantization

### CAT-Q — *Cost-efficient and Accurate Ternary Quantization for LLMs*
arXiv:2606.26650 · ICML 2026 (Oral) · Apache-2.0 · `IntelChina-AI/BitTern`

Post-training ternary quantization: weights to `{−1, 0, +1}`, ~1.58 bits. Two
components — **learnable modulation** (three learnable factors redistributing
weights and the ternary threshold) and **softened ternarization** (a
differentiable `tanh` transition annealing from identity to hard threshold),
over a **sliding-window output reconstruction** objective borrowed from
SliderQuant.

**Reported:** 512 calibration samples (~1M tokens) suffice for 1.7B–8B models,
beating BitNet b1.58 v1/v2 trained on 100B tokens — roughly a 100,000×
reduction in calibration tokens. Scales 1.7B–235B including MoE. 1–60 h on
8×A100-80GB.

**Deployment:** llama.cpp `TQ1_0` (CPU) / `TQ2_0` (GPU). Reported Qwen3-4B at
1.01 GB, 37.35 tok/s CPU vs 19.31 for Q4_K_M; 320 vs 226 tok/s on a 4090.

**Our reading — the caveat that matters.** Appendix E reports the same method on
harder tasks:

| | MATH-500 | GSM8K | Omni-MATH | HumanEval+ | MBPP+ |
|---|---|---|---|---|---|
| FP16 | 96.80 | 88.10 | 34.64 | 85.37 | 64.81 |
| CAT-Q, C4 calibration | 0.00 | 14.48 | 2.71 | **0.00** | **0.00** |
| CAT-Q+, matched calibration | 58.40 | 61.56 | 14.93 | 53.98 | 39.15 |

**Generic calibration does not degrade ternary models, it destroys their coding
ability entirely.** Any ternary result quoted without naming its calibration
data is not comparable to anything.

### ScaleQ-1.58 / AYOT — *Attend to Your Own Thoughts*
arXiv:2608.01078 · Intel Labs China

Identifies the cause: ternary PTQ collapses on reasoning tasks because the
calibration data lacks the model's own logical patterns. **AYOT** replaces generic
calibration with *the target model's own generated chain-of-thought traces over
domain prompts*, then ternarizes with that as context.

**Reported:** 4M calibration tokens; beats BitNet b1.58 2B4T (trained on 4T
tokens) by 8.97% averaged over math and code on ternary Qwen3-4B, using ~1,000,000×
fewer tokens. Accuracy still improving at 16M calibration tokens — no plateau.

**Our reading — the transferable finding.** Self-generated traces beat traces
from a *stronger* teacher (DeepSeek-R1-671B). Calibration must preserve the
reasoning patterns of the specific model being compressed. This is the single
most actionable result in the sub-2-bit literature for anyone with domain data
but no large teacher budget.

### BitNet b1.58
arXiv:2402.17764 · Microsoft

Introduces **BitLinear** — a drop-in `nn.Linear` replacement that quantizes
weights during the forward pass while retaining high-precision latent weights,
trained with a straight-through estimator. Ternary weights + 8-bit activations
(W1.58A8).

**Reported:** matches FP16 in perplexity and end-task performance from ~3B
upward at matched size and token count. 3B: 3.55× less memory, 2.71× faster.
71.4× arithmetic-operations energy saving on matmul at 7nm.

**BitNet b1.58 2B4T** (arXiv:2504.12285): first open native 1-bit model at 2B
scale, 4T training tokens. 0.4 GB non-embedding weights, 29 ms CPU decode.
**Weaker than its size peer on code** — HumanEval+ 38.4 vs Qwen2.5-1.5B's 50.6,
MBPP+ 47.19 vs 56.79.

**Our reading.** Native ternary requires training from scratch at trillions of
tokens — not a route for most groups. Relevant as a *comparison point* for what
PTQ can achieve against a natively-trained ternary model, and as the origin of the
`bitnet.cpp` serving kernel. Note the model card's own warning: **do not expect
efficiency gains via `transformers`** — the specialised kernels are required.

### BiLLM
arXiv:2402.04291 · ICML 2024

1.08-bit post-training binarization. Identifies salient weights structurally,
splits them into a binary residual, and binarizes the remainder with an optimal
grouped segmentation. Llama2-70B WikiText-2 PPL 8.41; a 7B binarizes in 0.5 h
on one GPU.

**Our reading.** A *baseline*, not a pipeline. Its nominal bit-width is inflated
by binary residuals and sparse indices, so sub-2-bit comparisons against BiLLM
need the actual bits-per-weight, not the headline "1.08 bits."

### LoftQ
arXiv:2310.08659 · NeurIPS 2023

Jointly solves for a quantized backbone and a low-rank LoRA initialization,
narrowing the gap between quantized and full-precision fine-tuning. Strongest
relative gains at 2-bit, where plain QLoRA fails to converge.

**Our reading.** Often misdescribed as producing "a quantized base plus an
adapter" at arbitrary bit-widths. It initializes an adapter **for** a quantized
model; it does not perform ternary quantization. Superseded at the sub-2-bit end
by CAT-Q.

### NanoQuant
arXiv:2602.06694 · 2026-06

Sub-1-bit PTQ by low-rank binary factorization with an ADMM solver. Compresses
Llama2-70B 25.8× in 13 h on one H100; a 0.55-bit 70B runs in 5.86 GB on an
8 GB RTX 3050 at 20 tok/s (seq len 32). Llama2-7B at 1 bit: PPL 10.34 with 0.26M
calibration tokens and **1.7 GPU-hours**.

**Our reading.** The cheapest reported sub-1-bit path, and the honest comparison
for "how little compute does this take." Its 1.7 GPU-hour 7B result is the
right anchor for our own planning.

### LittleBit-2 / LittleBit
arXiv:2603.00042

Quantization-aware knowledge distillation with geometric alignment for sub-1-bit.
Llama-3 8B PPL 11.53 at 1.0 bpp, 14.01 at 0.55 bpp, 23.74 at 0.1 bpp.
FP16 reference is 6.10.

**Our reading.** The quality frontier for sub-1-bit on an 8B. Notably, at 0.55 bpp
the gap to FP16 is still wide — evidence that very low bit-width is a genuinely
hard regime regardless of method.

### Others worth knowing

- **TernaryLLM**, **TriLM**, **Tequila**, **EfficientQAT** — QAT-family
  baselines for CAT-Q's comparisons.
- **TernaryQuench** — `penk/ternary-quench`, Apache-2.0. Open CAT-Q
  reimplementation with resumable checkpoints, MLX export, and Qwen3.5/Qwen3.8
  text-decoder support. **Ternarization only — no SFT.**
- **LoTA-QAF** — NeurIPS 2025. Lossless ternary adapter merge.
- **Low-Rank Ternary Adaptation** — ECCV 2026,
  `alexmanoo/ternary_adaptation`. Multiplicative ternary update: each base weight
  kept / zeroed / sign-flipped.

---

## Measuring compression damage

### *Flat Score, Amplified Failures*
arXiv:2607.27275 · 2026-07

**The paper that shaped our evaluation design.** See
[`EVAL-DESIGN.md`](EVAL-DESIGN.md) §2. Summary: aggregate scores stayed flat
while per-call failures rose 2.5×; quantization rescales the existing failure set
rather than creating new ones; tightening the error budget from K=10 to K=2
widened the FP16-vs-INT4 gap from 1.3 to 16.7 points; recovery rate was unchanged
at 55% across precisions.

### *From Signal Degradation to Computation Collapse*
ACL 2026 Findings

Two qualitatively distinct PTQ failure modes, and the boundary between them is
not at a fixed bit-width but at the *kind* of damage. Computationally:
quantizing the first two layers of Llama-3 to 2-bit dropped factual recall
100% → 41.65%, and 30 subsequent FP16 layers could not recover it.

### Quantization and hallucination

Three independent lines, and they point the same way:

- *An Empirical Study on Factuality Hallucination* (arXiv:2401.03205) — 8-bit
  minimal impact; **4-bit significantly increases hallucination.**
- *Secure or Suspect?* (arXiv:2512.08213) — package hallucination rate rises
  sharply at 4-bit; a 0.5B went 53.58% → **98.78%** while a 14B rose only
  **+6.6%**. Vulnerability presence rate also rises as precision drops.
- *Quantized but Deceptive?* (EMNLP 2025) — truthfulness holds at 4-bit but
  **deteriorates up to 40% at 2-bit.** Models ≤8B perform poorly on disjunction;
  ≥70B significantly better.

**Our reading.** Damage scales with model size and with how much the task
demands. This is why our evaluation separates coding, reasoning, and tool-calling
rather than reporting one "capability retention" number.

---

## Benchmarks and datasets

- **FORGE** — ICSE 2026, `shenyimings/FORGE-Artifacts`. 81,390 Solidity files,
  27,497 CWE-annotated findings across 296 CWE categories, from 6,454 real audit
  reports across 47 security teams. Extraction precision 95.6%, inter-rater
  agreement k-α = 0.87. **FORGE-Curated** sources reports from Dec 2024–Feb 2026
  specifically to be leakage-insignificant for pre-2026 models — check the base
  model's date before relying on that.
- **ARVO** — 5,001 C/C++ vulnerabilities detected by OSS-Fuzz across 273
  projects, each with a rebuild environment **and a bug-triggering exploit
  input**. Ground truth is a test, not an opinion. **Note:** ships ~5,001 Docker
  images totalling multiple terabytes; use source + patch + exploit input only.
- **FuzzingBrain-Bench V1** — arXiv:2608.25158. 77 challenges / 43 projects,
  C/C++/Java, sanitizer-graded. **Credits any distinct crash, not just the seeded
  bug** — a design choice made after observing that models kept finding defects
  other than the intended one. Best model (Claude Opus 4.8) found a bug in 60/77.
- **CodeRover-S** — ICSE 2026. LLM agents repairing real unpatched OSS-Fuzz
  vulnerabilities: 45 cases, 73.3% plausible patches, **5 merged into 4 upstream
  projects.**
- **OSS-Fuzz-Gen** — LLM-generated fuzz targets have surfaced **30 previously
  unknown bugs**, including one CVE and several undisclosed findings.

---

## Long context

- **RULER** — tested 17 long-context models; **all 17** degraded as input grew.
  Multi-needle harder than single; distractor diversity matters.
- **Lost-in-the-Middle Is Still Real in 2026** — reproduces the effect on
  1M-token models.
- **Context Rot** (Chroma) — degradation from context length itself; a single
  distractor hurts, four compound it. Agentic pipelines that concatenate many
  tool outputs are especially exposed, because the number of middle positions
  grows with the number of tool calls.

---

## Agentic security evaluation

- **Benchmarking Self-Hosted LLMs for Offensive Security** (TrustedSec, 2026-04)
  — 4,800 runs, 8 challenges, 6 models. Larger parameter count did **not**
  correlate with performance; the 32B model tested was the worst and the slowest.
  Reported a **knowledge–execution gap**: models produce correct SQLi payloads
  but cannot diagnose why a validator rejects them, and describe IDOR attacks
  correctly without changing the request. Concluded scaffolding may matter more
  than the base model.
- **What Makes a Good LLM Agent for Real-world Penetration Testing?** — typed
  tool interfaces alone improved agent performance by 14%.

**Our reading.** We cite this as motivation for measuring the harness as well as
the model — and we note its limits. It evaluated *raw, un-finetuned* general
models, which is not the same question as whether domain training changes the
ordering. Treat single-benchmark cross-model rankings as weak evidence about
causal questions.

---

## Licence note

Everything cited here retains its own licence. The closest are CAT-Q/BitTern and
TernaryQuench (Apache-2.0). We do not redistribute third-party weights or data
here — see [`../PRIVACY.md`](../PRIVACY.md) and [`../NOTICE.md`](../NOTICE.md).