# NOTICE

## Our code

`eval/metrics.py`, the benchmark specification, and documentation in this
repository are MIT licensed — see [`LICENSE`](LICENSE).

## Third-party components referenced but NOT redistributed

This repository contains **no** third-party model weights, datasets, or
vendored source. We reference the following; each retains its own licence and
must be obtained from its own distribution.

| Component | Licence | Where |
|---|---|---|
| CAT-Q / BitTern | Apache-2.0 | `github.com/IntelChina-AI/BitTern` |
| TernaryQuench | Apache-2.0 | `github.com/penk/ternary-quench` |
| Qwen3.8-27B (base model family) | Apache-2.0 | Hugging Face |
| BitNet b1.58 (kernels: `bitnet.cpp`) | MIT / see upstream | `github.com/microsoft/BitNet` |
| LoTA-QAF | see paper | `github.com/KingdalfGoodman/LoTA-QAF` |
| Low-Rank Ternary Adaptation | see repo | `github.com/alexmanoo/ternary_adaptation` |
| QVAC Fabric BitNet | see repo | `github.com/tetherto/qvac-rnd-fabric-llm-bitnet` |
| FORGE / FORGE-Curated | see source | `github.com/shenyimings/FORGE-Artifacts` |
| ARVO | see source | OSS-Fuzz / OSS-Fuzz-Gen ecosystem |
| FuzzingBrain-Bench | see paper | arXiv:2608.25158 |

Citations for the literature we build on are in
[`docs/RELATED-WORK.md`](docs/RELATED-WORK.md).

## Data provenance

`bench/sample/` is **synthetic**. No real hostnames, requests, findings, or
engagement-derived material appear anywhere in this repository. See
[`PRIVACY.md`](PRIVACY.md).

## No affiliation

References to third-party products, models, and papers are for identification
and citation. No endorsement is implied, and no affiliation with any cited
author or organisation is claimed.
