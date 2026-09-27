# Reporting contract

Use these six sections in this exact order. Keep the headings in English as shown; write finding details in the user's language unless requested otherwise. Replace the counts and verdict with the reviewed result.

```text
## 🔴 CRITICAL (0)

None.

## 🟠 HIGH (0)

None.

## 🟡 MEDIUM (2)

1. Defect — Short, specific title
   path/to/file.ext:42 (head SHA abcdef...)
   Trigger: ...
   Impact: ...
   Evidence: ...

2. Risk — Short, specific title
   path/to/other.ext:18 (head SHA abcdef...)
   Trigger: ...
   Impact: ...
   Missing evidence: ...

## 🟢 LOW (1)

1. Defect — Short, specific title
   path/to/file.ext:77 (head SHA abcdef...)
   Trigger: ...
   Impact: ...
   Evidence: ...

## ✅ Positive Security Controls Verified

- Control and the specific check or code path that verified it (file:line).

## Verdict: ⚠️ REQUEST CHANGES

Reason: The two medium findings need fixes before this change is accepted.
Target: PR #123, base <sha>, head <sha> (or commit/range).
Checks: Focused tests and other checks actually run.
Limits: Material files or behaviors not verified.
```

Count only actionable findings that survived verification. Include every severity heading even when its count is zero; write `None.` beneath an empty severity. Do not duplicate one root cause across sections. A risk must name the fact that remains unverified and why the concern is material. A control belongs in **Positive Security Controls Verified** only if you actually traced or tested it in the reviewed scope. If none qualifies, write `None verified in the reviewed scope.` Do not turn a passing test suite into an unsupported claim of security coverage.

When an earlier review raised the same issue, report it only if it remains valid at the pinned head. Mention that history briefly only if it clarifies the current evidence; do not copy an old review as a new finding. If relevant comments or prior review threads were inaccessible, put the material gap in `Limits` under the verdict. Preserve the six-section format.

An empty section is better than a weak finding. Exclude style nits, speculative edge cases with no reachable trigger, generic calls for more tests, and performance claims without a realistic workload. Use the [false-positive gate](review-method.md) before counting a finding.

Use `⚠️ REQUEST CHANGES` if any Critical, High, or Medium finding exists. Use `🟢 OPTIONAL CHANGES` if findings are Low only. Use `✅ NO ACTIONABLE FINDINGS` if every count is zero. This is a chat verdict, not a GitHub review submission or approval action. If the review was materially incomplete, state that limit in the verdict rather than implying the change is safe.

The line reference should point to the smallest relevant changed span in the reviewed head revision. If the issue is caused by a deletion, point to the surrounding surviving line or describe the deleted location clearly. In a hosted review UI, use a supported permalink when possible. Do not cite a line from a moving branch without recording its SHA. Keep the report compact and avoid generic praise or a walkthrough of every file.
