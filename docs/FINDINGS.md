# Findings

No results yet. This file records what we measure, in what order, and — just as
importantly — what each result would and would not prove.

Last updated: 2026-10-12

---

## Status

| # | Question | State |
|---|---|---|
| F1 | Does ternary compression of the base preserve capability at all? | ⬜ |
| F2 | Where does it break first? | ⬜ |
| F3 | Does domain calibration recover the loss? | ⬜ |
| F4 | Does domain training reduce *amplification*, or only the baseline? | ⬜ |
| F5 | Is tool-calling capability preserved across multi-turn episodes? | ⬜ |
| F6 | Is there early-layer "Computation Collapse"? | ⬜ |
| F7 | Can it find vulnerability patterns absent from base training data? | ⬜ |
| F8 | Can it operate inside a scope-enforcing harness? | ⬜ |

---

## F1 — Does ternary compression preserve capability?

The gating question. If this fails, nothing downstream matters.

**Measure:** FP16 vs ternary on all eval families, per-channel and per-budget.
**Kill criterion:** early-layer collapse → no amount of fine-tuning recovers it;
the method is not fit for this architecture and the honest conclusion is to stop
and report that.

---

## F2 — Where does it break first?

Prior expectation from the literature: code and math before anything else, with
tools and agentic behaviour following. If breakage appears in tool-calling
*before* coding, that is a different and more serious result.

---

## F3 — Does domain calibration recover the loss?

Prior expectation: substantially, and specifically on code — the domain-matched
calibration result is the one difference between a 0.00 and a usable score.

**Measure:** ternary-with-domain-calibration vs the released build's generic
calibration, same weights, same method, calibration data the only variable.

---

## F4 — The prediction we most want to be wrong about

**Hypothesis.** If compression rescales the existing failure set, then training
that reduces the baseline error rate should reduce post-compression error rate
*more than proportionally*.

**Why we think it:** amplification is multiplicative on whatever error rate
remains. Halving the baseline halves the compressed rate twice over.

**If it holds:** hallucination, abstention and verified-negative data are worth
more under compression than capability-teaching data. That would be a broadly
useful finding for anyone shipping a compressed agent.

**If it does not hold:** the amplification factor is not a simple constant, and
the whole intervention strategy in [`METHOD.md`](METHOD.md) Stage C is wrong.
Report it.

**Measure:** amplification factor = (ternary per-channel error rate) ÷ (FP16
per-channel error rate), before and after domain training. Both must be reported;
a baseline improvement with no change in the factor is a negative result here.

---

## F5 — Tool-calling across multi-turn episodes

No published ternary tool-calling benchmark exists as far as we can determine, so
there is nothing to compare against and no prior to lean on.

**Measure:** tool-name hallucination rate · argument validity · malformed-output
rate · out-of-scope attempts · recovery rate after a failed call · truncation
rate.

**Note:** aggregate episode success is expected to look fine. Per
[`EVAL-DESIGN.md`](EVAL-DESIGN.md) §2, that is the trap. Tightened-budget
success is the metric that moves.

---

## F6 — Early-layer collapse

Sub-2-bit can produce irreversible damage that later full-precision layers
cannot undo. **This must be checked before interpreting any other result**,
because a positive result obtained through collapse would be meaningless.

---

## F7 — Novel vulnerability patterns

The capability of most interest and the hardest to evaluate honestly.

**Design:** recall on findings that **postdate the base model's training**, with
provenance recorded per item. Group-locked so no investigation straddles splits.

**Precision matters as much as recall.** Fuzz-driver generation is roughly 70%
false-positive by default, and maintainers reasonably lose trust in a tool that
drowns them in noise. Report recall **and** false-positive rate, always together.

**Negative result is publishable and valuable.** "Compression preserved recall but
destroyed precision" is a real finding that tells practitioners not to ship it.

---

## F8 — Scope-enforced operation

The deployment test: given a scope, does the model stay inside it; does it
justify its changes; does it stop when it should?

The architectural claim under test is that the **gate**, not the model, is
authoritative. A model that proposes an out-of-scope action and is correctly
blocked is the system working. A model that proposes out-of-scope actions
repeatedly is a data problem, and `stop_decision` is the relevant capability.

---

## Reporting rules

Every result published here states:

1. the checkpoint and its provenance
2. the export format and kernel used
3. the calibration data, including its date relative to the base model's
4. group-lock status and the cutoff date of the eval set
5. per-channel rates **and** tightened-budget success
6. failure-set rank correlation against the full-precision baseline
7. whether the vision path was ternarized

If any of these is unknown, say so rather than omitting it. An honest
"we could not determine whether the vision tower was ternarized" is more useful
than a clean-looking number with a hidden confound.