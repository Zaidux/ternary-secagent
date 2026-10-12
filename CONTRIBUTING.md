# Contributing

## Two things are useful

**1. Corrections to the measurement argument.** Our central claim is that
aggregate scores hide compression damage in tool-calling agents, and that
tightened error budgets expose it. If you have a counterexample — a setup where
compression genuinely is free, or a tighter diagnostic than per-channel rates
plus budget tightening — that is the most valuable thing you could send. We
would rather be corrected now than publish a wrong methodology.

**2. Independent replication.** Run `eval/metrics.py` on your own model and
compressed variant. Report per-channel rates and tightened-budget success. If
your numbers disagree with ours, that is interesting.

## What is not useful

- Generic "this looks promising" feedback
- Proposals to add capability before we have baseline numbers
- Pull requests containing datasets, model weights, or corpus shards — see
  [`PRIVACY.md`](PRIVACY.md)

## Data contributions

We do not accept real vulnerability data, engagement-derived material, or
anything containing live hostnames. If you want to contribute evaluation data,
it must be either synthetic or from a third-party source we can verify the
licence of.

## Standards

- Metrics must stay dependency-free and standard-library only
- New metrics need a documented rationale and a fixture exercising them
- Claims about compression need a tightened-budget number, not an aggregate
- Any result we publish states its checkpoint, export format, kernel,
  calibration data, and cutoff date — or says plainly that these are unknown

## Reporting security issues

See [`SECURITY.md`](SECURITY.md).
