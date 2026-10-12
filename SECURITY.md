# Security

## Scope

This project is for **authorized** security research: bug bounty programs with
written scope, internal testing with owner approval, and defensive work.

**Not in scope:** testing any system without the owner's explicit authorization.
If you are unsure whether you have authorization, you do not.

Tooling described here is intended for targets where you hold written permission.
An authorized scope is one the owner has stated, in writing, for the specific
system and time period.

## Reporting a vulnerability in this project

If you find a security issue in the code, the harness, or the evaluation
methodology: open a **private** security advisory on the repository rather than a
public issue. Please do not include proof-of-concept detail that would be
exploitable against third parties.

## Disclosure of vulnerabilities we find

**We do not disclose vulnerabilities in public channels, ever.**

If we find a vulnerability in a third-party system, the disclosure path is the
program's own — typically the bug bounty program's private report flow. We route
every finding there and disclose nothing unilaterally, regardless of:

- whether the vulnerability has already been fixed
- how it reached us
- whether a deadline appears to be passing
- whether we believe disclosure is in the public interest

If we are not participating in a program for that target, we report it to the
vendor's security contact and do not publish.

**We do not publish findings, PoCs, or vulnerability details in this repository.**
Published findings are limited to cases where the vendor has already published
their own advisory under a permissive licence, and we cite theirs rather than
reproducing the disclosure.

## Scope enforcement in the evaluated system

The architecture under test separates authority from capability: the model's
reasoning is never what grants it permission. A scope gate reads the program's
rules and decides independently what is in and out of scope; the model proposes
actions and the gate disposes of them. See [`docs/METHOD.md`](docs/METHOD.md)
Stage E.

An agent proposing an out-of-scope action and being correctly blocked is the
system working as designed.
