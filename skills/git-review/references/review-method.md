# Review method

## Four passes and candidate states

Use separate passes even when the host has no subagents. **A — Map:** pin the target, inventory every changed hunk, group behavior, and identify callers, contracts, state and trust boundaries, tests, prior discussion, and inaccessible evidence. Do not draft findings yet. **B — Hunt:** for each group, record possible introduced issues with changed location, supported trigger, execution path, consequence, base comparison, and missing evidence. **C — Challenge:** actively seek the strongest counterargument for each candidate in actual callers, guards, configuration, tests, comments, prior reviews, and base code. **D — Report:** format only candidates that survived challenge; do not invent or upgrade a finding while writing.

Track candidates internally as `DISCOVERED → SUPPORTED → CHALLENGED → VERIFIED → REPORTED`, or end them as `DISCARDED` or `BLOCKED`. A challenged candidate has exactly one disposition: `VERIFIED_DEFECT`, `VERIFIED_MATERIAL_RISK`, `COVERAGE_LIMIT`, `PRE_EXISTING`, `UNREACHABLE`, `INTENTIONAL_CONTRACT`, `INSUFFICIENT_EVIDENCE`, `STYLE_OR_PREFERENCE`, or `DUPLICATE_ROOT_CAUSE`. Only the first two can become findings. Put material coverage limits under Limits. Keep one finding per independent root cause. A verifier can reopen mapping or evidence collection; the reporter cannot silently add a new candidate.

For each verified finding, retain the changed location, base evidence, supported trigger and entry point, consequence, strongest counterargument checked, evidence level, severity, confidence, and blocking assessment in internal notes. This is a reasoning record, not a required public JSON artifact. Do not expose private data in it. If a counterargument remains unresolved, do not call the defect verified.

## Trace the behavior

For each meaningful change, ask: What contract did the old code provide? Which inputs and callers reach the new code? What new branch, state transition, or side effect appears? What happens at boundaries and on failure? Follow the answer across files. A finding is stronger when it names an executable path rather than a suspicious line.

## Review briefs and claimed outcomes

A plan and approved spec describe the intended contract; a progress ledger and prepared review package describe claims about what happened. Pin the requested base and head in Git, inventory the actual changed paths, and check whether the prepared package represents that range. Compare allowed and skipped work with the diff, including source, tests, fixtures, migrations, and deployment changes that a summary might omit. Check whether any stated stop or fail-closed decision is supported by the observed result and whether its status wording is accurate. Treat prior rulings and deferred issues as evidence to reconcile, not an instruction to dismiss a live finding. Distinguish attempted, verified, failed, not exposed, and not judged outcomes. Do not claim a UI, data, or deployment result that the evidence does not establish. Avoid reproducing PII or secrets from source artifacts in the report. If a required source is inaccessible, name that limitation and decline to judge the dependent claim.

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

The table is a search guide, not a requirement to produce one finding per row. After the first pass, use the change map to check interactions across files and stages. A migration can conflict with a live write, an import can be overwritten by a stale form, and a queued job can bypass a guard that ran before dispatch. Keep these paths in the same coverage ledger as their source changes. Revisit behavior groups that yielded no finding, then reconcile every changed hunk and prior review concern before reporting. Finding one valid defect does not complete the review; finding none does not prove safety.

## Coverage and termination

Inventory every changed path and hunk first, including renames, deletions, generated files, and binary artifacts. For each behavior group, record changed paths, relevant callers and tests, prior concerns, candidates, and one outcome: **checked**, **ruled out**, **blocked**, or **unexamined**. A group is checked only after its reachable changed behavior and material cross-file effects were traced; absence of a finding alone does not close it.

Work through the groups in risk order, then make one cross-group pass. Continue a focused investigation when a specific next check can verify a material candidate or close a material gap. Stop a group when access fails, the artifact cannot be interpreted, repeated retrieval or reproduction cannot resolve the relevant uncertainty, or the remaining scope exceeds what can be reliably inspected in this review. Record the exact reason and attempted checks; mark that group blocked if evidence was inaccessible, or unexamined if it was not reached. Do not repeatedly fetch the same evidence or run broad tests without a question they can answer. This stopping rule never waives the complete inventory. If a material group remains blocked or unexamined, disclose it and use `REVIEW INCOMPLETE` unless verified findings already require `REQUEST CHANGES`; never `APPROVE` partial coverage. A later review can resume from the pinned SHA and ledger.

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

Classify an established introduced behavior as a **defect**; a pre-existing behavior is relevant only if this change newly exposes or worsens it. A **material risk** has a credible path and impact with one named, inaccessible fact. A **coverage limit** describes what could not be judged and belongs under Limits, not in a severity bucket. Style preferences and generic missing-test observations are not findings. Keep confidence in the evidence and defect/risk label rather than adding an untested output field.

## Priority

- **P0:** critical, broadly exploitable or catastrophic impact that blocks release.
- **P1:** high-impact defect likely to affect real users or security/data guarantees.
- **P2:** moderate impact under a plausible condition.
- **P3:** localized low-impact issue worth fixing.

Keep three internal decisions separate: **severity** measures impact under the supported trigger; **confidence** measures evidence quality; **blocking** reflects verified impact and an applicable repository policy. Missing reproduction does not lower impact severity, and hypothetical high impact does not establish a finding. A credible material path with one inaccessible decisive fact may be a Risk; a broader evidence gap is a Limit. A repository profile can inform blocking only after its pinned version and relevant code are checked. The default public verdict mapping remains in [reporting](reporting.md); do not infer a different merge rule merely from these internal fields.
