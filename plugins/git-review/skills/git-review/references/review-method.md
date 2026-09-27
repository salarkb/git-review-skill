# Review method

## Trace the behavior

For each meaningful change, ask: What contract did the old code provide? Which inputs and callers reach the new code? What new branch, state transition, or side effect appears? What happens at boundaries and on failure? Follow the answer across files. A finding is stronger when it names an executable path rather than a suspicious line.

## Risk lenses

Apply the lenses that fit the change, with equal attention to material impacts:

| Lens | Questions worth tracing |
| --- | --- |
| Correctness | Empty inputs, boundaries, ordering, null values, retries, exceptions, partial results, time zones, and state transitions? |
| Security | Can an untrusted actor reach the path? Are authentication, authorization, validation, output encoding, and secret handling preserved? |
| Data integrity | Can writes be lost, duplicated, partially applied, or read under a different schema? Are migrations reversible and compatible during rollout? |
| API and compatibility | Do existing callers, wire formats, flags, and persisted data still satisfy the contract? |
| Concurrency | Are locks, transactions, idempotency, and lifecycle assumptions still valid under simultaneous operations? |
| Performance | Is new work unbounded, repeated per item, or moved onto a hot path? Is there a plausible scale threshold? |
| Failure handling | Are errors surfaced, cleanup completed, and useful signals retained? |
| Tests | Which specific behavior changed without a check that would fail if it regressed? |

The table is a search guide, not a requirement to produce one finding per row.

## Evidence ladder

1. **Reproduced defect:** a focused test or minimal execution demonstrates the introduced behavior.
2. **Proven from code:** the trigger and consequence follow from inspected code and contracts, even if execution is unavailable.
3. **Material risk:** the path is plausible and impact substantial, but a key fact is inaccessible; name that fact and do not overstate certainty.
4. **Speculation:** the path or impact cannot be established. Do not report it as a finding.

For every candidate, try to falsify it: inspect the caller, guard, config, data model, tests, nearby code comments and docstrings, prior review discussion, and the base revision. A comment may document the intended contract; verify the contract in current code before relying on it. An earlier reviewer may have found the same issue; verify whether later commits fixed it and whether the current head still has a reachable path. If a condition cannot occur, discard the finding. If it predates the target change, exclude it unless the change newly exposes or worsens it. Tests are evidence about the paths they exercise; passing tests are not a substitute for tracing uncovered paths.

## False-positive gate

A reportable finding must answer **all** of these questions with evidence:

1. **Introduced?** Did this change create or newly expose the behavior? Compare the base revision.
2. **Reachable?** Can a supported input or realistic state reach it through actual callers, configuration, and guards? Do not assume a private helper is called directly when its only caller enforces the precondition.
3. **Consequential?** Is there a concrete user, security, data, compatibility, reliability, or plausible-scale performance impact? A possible micro-optimization or preferred style is not enough.
4. **Actionable here?** Is the changed line the right place to point, and could the author address this issue in the reviewed change?

If a question cannot be answered, inspect more context or leave it out. A material risk may remain when a specific trigger and impact are credible but one inaccessible fact needs verification; name that fact. Do not use the risk label to launder a guess. Test absence usually belongs in coverage limits unless a concrete high-impact behavior lacks a required check. A low-priority finding still needs an actual defect; do not turn the Low section into a list of nits.

## Priority

- **P0:** critical, broadly exploitable or catastrophic impact that blocks release.
- **P1:** high-impact defect likely to affect real users or security/data guarantees.
- **P2:** moderate impact under a plausible condition.
- **P3:** localized low-impact issue worth fixing.

Severity is impact under the stated trigger, not confidence. Keep confidence visible in the defect/risk label and evidence.
