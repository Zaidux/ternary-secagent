# PRIVACY.md — what is public, what is not, and why

Last reviewed: 2026-10-12

This repository is **public**. It contains research questions, methodology, and
evaluation code. It does **not** contain the model, the corpus, or the training
recipe. This document says exactly where each lives and why.

---

## Public (this repository)

| Path | Contents |
|---|---|
| `README.md` | Research question, motivation, programme outline |
| `docs/RELATED-WORK.md` | Literature survey with our critical annotations |
| `docs/EVAL-DESIGN.md` | Evaluation methodology — our main contribution so far |
| `docs/METHOD.md` | Method at publishable resolution |
| `docs/FINDINGS.md` | Results, as they are validated |
| `eval/` | Metric implementation (MIT, no dependencies) |
| `bench/SPEC.md` | Benchmark specification and data schema |
| `bench/sample/` | **Synthetic** sample data only |

## Not public

| Asset | Where it lives | Why it is withheld |
|---|---|---|
| Trained model weights | private storage | The artefact. Its value is the point. |
| LoRA adapters / checkpoints | private storage | Same — an adapter is the model. |
| Training corpus | private storage | Built in part from **proprietary, non-public material** that cannot be redistributed even redacted. |
| Exact training recipe | private planning docs | The specific pipeline is the reproducible IP. Method shape is published; parameters are not. |
| Evaluation ground truth | private storage | Derived from real investigations. Publishing it would disclose information about systems that have not consented. |
| Redaction alias maps | private storage | These **reverse** the redactions. Publishing one unmasks everything the redaction was protecting. |
| Compute budget, funding | private planning docs | Operational, and commercially sensitive. |
| Product roadmap / unrelated source | separate private repos | Not this project's business. |

---

## The rule that governs all of it

> **Redaction is not anonymisation, and it is not permission.**

A "redacted" finding still encodes: which class of bug a team of developers made,
what their architecture looked like, how their tooling was misconfigured, and how
long it took them to notice. Across enough findings, that is a description of
their security posture — and in several jurisdictions, disclosing the existence
of an unpatched vulnerability you discovered is itself a legal matter.

So: **corpus and ground truth never leave private storage.** Not in aggregate, not
"anonymised", not "as an example". If a finding is to appear in public code, it
comes from a *third-party public dataset* (FORGE, ARVO, an audit report already
published under a permissive licence) — never from our own investigations.

---

## Enforcement

`.gitignore` in this repository blocks weights, adapters, corpus files, databases,
logs, secrets, and the private planning documents. It is deliberately paranoid.

**A single `git add -A` should not be able to publish anything sensitive.** If it
ever looks like it could, fix the `.gitignore` before committing — not after.

Before the first push, and before any release:

```bash
git ls-files | xargs -I{} sh -c 'test -f "{}" && du -h "{}"' | sort -rh | head -20
git grep -nEi '(api[_-]?key|secret|token|password|BEGIN [A-Z ]*PRIVATE KEY)[[:space:]]*[:=]' -- . \
  || echo "no obvious secret patterns"
git ls-files | grep -Ei '\.(gguf|pt|safetensors|bin|db|sqlite|jsonl|parquet)$' \
  && echo "!! investigate before pushing"
```

---

## If we later release the model

A public release would be a deliberate decision with three preconditions:

1. **Consent** — no private-derived material in the weights or in any
   contamination-visible form.
2. **Re-derivation** — the released artefact is reproducible from public inputs,
   or the non-reproducible inputs are documented as withheld.
3. **Independent evaluation** — someone outside the project can run our eval
   suite against the release and get our numbers.

Until all three hold, the answer is no. See [`docs/STRATEGY.md`](docs/STRATEGY.md)
for why publishing the *measurement* first is the better sequencing regardless.