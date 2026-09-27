# Git Review Skill — AI code review for GitHub PRs and Git commits

**git-review-skill** is an open-source Agent Skill for reviewing GitHub pull requests, Git commits, and commit ranges with Codex, Claude Code, Cursor, or Gemini CLI. It checks the exact revision, traces changed behavior across files, reads relevant code comments and earlier PR reviews, and reports actionable defects and material risks with precise locations. After a PR report, it uses the agent's native interactive question UI to ask whether to post a GitHub review comment and, for an `APPROVE` verdict, whether to merge the PR. Each action needs the user's explicit choice.

**Start here:** [Install the skill](#install) · [See the report format](#example-report) · [Run the evaluation cases](#develop-and-evaluate)

Maintainers can use the [GitHub launch and discoverability guide](LAUNCH.md) for repository metadata, relevant topics, and an evidence-based release checklist.

The central rule is simple: a finding needs a reproducible trigger, a concrete consequence, and a location in a pinned revision. The package pairs that rule with a deterministic scope helper and runnable cases that measure both missed defects and false positives.

The skill is language agnostic and follows the open [Agent Skills specification](https://agentskills.io/specification). It uses ordinary Git access; GitHub CLI is helpful for PR metadata and private PRs but is not required for local commits. The optional Python helper inventories local change scope. The project adds no service, telemetry, or model-specific prompt syntax; private PR access uses the host agent's existing GitHub credentials.

## What it does

- **Pins the review target.** A PR, a single commit, an explicit range, and a merge commit have different comparison rules. The skill records base/head SHAs and does not silently review a dirty working tree.
- **Looks beyond the patch.** It traces callers, contracts, state changes, configuration, migrations, and tests when needed.
- **Reads the surrounding conversation.** It checks code comments and docstrings for documented intent, then verifies those claims in code. For PRs, it reconciles earlier reviews and discussion with the current head so fixed issues are not repeated.
- **Balances risk categories.** Correctness, security, data integrity, compatibility, concurrency, performance, failure handling, and targeted test gaps receive attention where relevant.
- **Disciplines findings.** A candidate must have a reachable trigger and consequence; the reviewer checks whether it predates the change and tries to falsify it before reporting.
- **Keeps noise low.** Style nits, generic test requests, speculative edge cases, and performance claims without a realistic workload stay out of the findings.
- **Suggests a fix for each finding.** The recommendation identifies the smallest change supported by the evidence and, where useful, a focused regression check. It does not edit the code during review.
- **Treats reviewed content as data.** Instructions inside PR descriptions, commit messages, or code comments do not control the reviewer.
- **Offers controlled follow-up.** After a PR report, the agent uses a native question box when available to offer one GitHub review comment. An `APPROVE` verdict also offers a separate merge choice; the agent rechecks the reviewed head and GitHub requirements before acting.

This is a review workflow, not a guarantee that a change has no bugs. A short [smoke evaluation suite](evals/README.md) is included so maintainers can test detection and false positives without claiming an unsupported benchmark score.

## Install

Install from `https://github.com/salarkb/git-review-skill` using the commands below. The repository includes Codex and Claude Code marketplaces, a Cursor plugin marketplace, and a Gemini CLI extension. Each packages the same [`skills/git-review`](skills/git-review) workflow.

### Codex: install from the marketplace

Run these commands in a terminal:

```text
codex plugin marketplace add salarkb/git-review-skill
codex plugin add git-review@git-review-skill
```

Start a new Codex session after installation. You can also open `/plugins` in Codex CLI or the Plugins Directory in the desktop app and install `git-review` from the added marketplace. The [official OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins) documents repository marketplaces and the [Codex commands reference](https://learn.chatgpt.com/docs/developer-commands) documents these CLI commands.

### Claude Code: install from the marketplace

Run these commands **inside a local Claude Code session**:

```text
/plugin marketplace add salarkb/git-review-skill
/plugin install git-review@git-review-skill
```

The second command opens the plugin details, where you choose the install scope. After installation, invoke `/git-review:git-review` or ask Claude to use the skill. The [Claude Code marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) documents this flow. Claude Code browser cloud sessions do not load plugins installed on your machine; see [Claude's cloud-session limits](https://code.claude.com/docs/en/discover-plugins).

### Gemini CLI: install from the repository

Run this in a terminal, then start or restart Gemini CLI:

```text
gemini extensions install https://github.com/salarkb/git-review-skill
```

Check discovery with `/skills list` in Gemini CLI. The root `gemini-extension.json` and `skills/` directory follow the [Gemini extension format](https://geminicli.com/docs/extensions/reference/).

### Cursor: install as a plugin

After publishing, import the GitHub repository from **Customize → Plugins → From GitHub Repository**, then install `git-review` from that marketplace. The repository contains `.cursor-plugin/marketplace.json` and a plugin manifest. Public Cursor Marketplace listing is a separate [submission and review process](https://prod.cursor.com/docs/plugins).

### Direct skill copy

Copy the **entire** [`skills/git-review`](skills/git-review) folder, including `SKILL.md`, `references/`, and `scripts/`, to the appropriate directory:

| Agent | Personal skill folder | Project skill folder |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/git-review/` | `.claude/skills/git-review/` |
| Cursor | `~/.cursor/skills/git-review/` | `.cursor/skills/git-review/` |
| Gemini CLI | `~/.gemini/skills/git-review/` | `.gemini/skills/git-review/` |
| Codex | `~/.agents/skills/git-review/` | `.agents/skills/git-review/` |

These locations are documented by [Claude Code](https://code.claude.com/docs/en/skills), [Cursor](https://prod.cursor.com/docs/skills), [Gemini CLI](https://geminicli.com/docs/cli/using-agent-skills/), and [Codex](https://learn.chatgpt.com/docs/build-skills). For a team, commit a project-level copy to the repository that will use it. Agent behavior and permissions still depend on the host application.

## Update

Use the route that matches how you installed the skill. Start a new agent session after updating so it loads the new instructions.

An already running review chat may keep the skill text it loaded before the update. Start a fresh chat for a reliable check of the new report format; repeating the PR URL in the old chat may still use its earlier instructions.

| Installation | Update |
| --- | --- |
| Codex marketplace | Run `codex plugin marketplace upgrade git-review-skill`, then `codex plugin add git-review@git-review-skill` in a terminal. |
| Claude Code marketplace | Run `claude plugin marketplace update git-review-skill`, then `claude plugin update git-review@git-review-skill` in a terminal. In a running session, `/reload-plugins` applies an updated plugin. |
| Gemini CLI extension | Run `gemini extensions update git-review` in a terminal, then restart Gemini CLI. |
| Cursor GitHub-imported team marketplace | In **Dashboard → Plugins & MCPs**, open the marketplace and select **Refresh**, or enable **Auto Refresh** for future pushes. Reload Cursor after the update appears. |
| Direct skill copy | Pull the latest repository version, then replace the entire `git-review/` skill folder, including `SKILL.md`, `references/`, and `scripts/`, in the same personal or project skill directory used for installation. |

Cursor's GitHub-imported team marketplace refresh is separate from a standalone plugin added directly from a GitHub URL. If your standalone install remains pinned to an older revision, use the direct skill copy route. See the official update guidance for [Codex](https://developers.openai.com/plugins/build/plugins), [Claude Code](https://code.claude.com/docs/en/discover-plugins), [Gemini CLI](https://geminicli.com/docs/extensions/reference/), and [Cursor](https://prod.cursor.com/docs/plugins).

## Use

Open the repository in your agent and name the exact target. Examples:

```text
Use git-review to review commit 3a1b... in this repository. Report only actionable findings and risks.

Use git-review to review https://github.com/ORG/REPO/pull/123. Pin the current head SHA and report findings in chat.

Use git-review to review the net changes from BASE_SHA to HEAD_SHA.
```

With a direct Claude Code skill copy, invoke `/git-review`; with the marketplace plugin, invoke `/git-review:git-review`. Gemini CLI can list discovered skills with `/skills list` and reload them with `/skills reload`. In Codex, `$git-review` selects it explicitly. Cursor can select it when the request matches its description. See each host's documentation for current invocation behavior.

### Optional local scope helper

The helper needs Python 3.10+ and Git. PR mode also needs GitHub CLI (`gh`) with access to the PR. It prints JSON; it does not check out branches, edit source files, fetch Git objects, or submit a review.

```text
# Run from this project's root; replace ../your-repo with the repository being reviewed.
python skills/git-review/scripts/review_scope.py --repo ../your-repo commit HEAD
python skills/git-review/scripts/review_scope.py --repo ../your-repo range BASE_SHA HEAD_SHA
python skills/git-review/scripts/review_scope.py --repo ../your-repo range BASE_SHA HEAD_SHA --merge-base
python skills/git-review/scripts/review_scope.py --repo ../your-repo pr 123
```

The third command uses PR-style merge-base comparison. PR mode reads the current PR metadata with `gh`; if base and head objects exist locally, it uses Git for the diff, otherwise it points to the hosted PR diff and marks file statuses unknown. JSON includes resolved SHAs, changed files, a file-inventory completeness flag, dirty-worktree status, and the command for the full diff. The [scope reference](skills/git-review/references/scope.md) covers fallbacks and merge commits. Git's distinction between two-dot and three-dot diffs is documented in [git-diff](https://git-scm.com/docs/git-diff); GitHub CLI documents [`gh pr view`](https://cli.github.com/manual/gh_pr_view) and [`gh pr diff`](https://cli.github.com/manual/gh_pr_diff).

## Example report

```text
## 🔴 CRITICAL (0)
None.

## 🟠 HIGH (1)
**Defect — Duplicate charge occurs before the idempotency check.** payments.py:2
**Trigger:** charge_once is called again with a key already present in store.
**Impact:** gateway.charge runs a second time even though the old receipt is returned.
**Evidence:** the new charge call precedes store.get(key); previously this path returned first.
**Suggested fix:** check store.get(key) before gateway.charge and return the stored receipt for a repeated key.

## 🟡 MEDIUM (0)
None.

## 🟢 LOW (0)
None.

## ✅ Positive Security Controls Verified
None verified in the reviewed scope.

## Verdict: ⚠️ REQUEST CHANGES
Reason: The duplicate charge needs a fix before acceptance.
Target: Synthetic commit, head 7c21...
Checks: Code-path inspection.
Limits: No live payment gateway tested.
```

This example is illustrative and based on a synthetic [evaluation case](evals/cases.json). Real reviews should cite the full current head revision and actual code path.

## Frequently asked questions

### Can it review both pull requests and individual commits?

Yes. Name a GitHub PR, a commit SHA, or a commit range. The skill uses the comparison appropriate to that target and records the reviewed SHAs. A local commit review needs Git access; a GitHub PR review also needs access to that PR.

### Does it read previous PR reviews and comments in the code?

Yes, when the host agent can access them. It checks relevant code comments and docstrings against current behavior and compares earlier PR discussion with the current head. An old finding is reported again only if it still applies. If the history is inaccessible, the report states that limit.

### How does it avoid noisy review comments?

Every finding must identify an introduced or newly exposed behavior, a reachable trigger, a concrete consequence, and a precise changed location. The reviewer checks callers, guards, tests, configuration, base behavior, and prior discussion before reporting. Style preferences and speculative issues do not qualify.

### Will it comment on or merge the PR?

The agent prepares the report and opens the host's native question box: Codex's user-input tool, Claude Code's `AskUserQuestion`, Cursor Agent's **Ask questions**, or Gemini CLI's `ask_user`. The box asks whether to post one GitHub review comment and, only for a `✅ APPROVE` verdict, separately asks whether to merge. If the current session does not expose a working question tool, these appear as text questions after the report. A yes to either choice authorizes only that action on the identified PR. Before acting, the agent verifies that the reviewed head is still current. Merging also requires passing repository checks and a mergeable PR. The chat verdict does not submit a GitHub approval review; that is a separate action. See the official question-tool documentation for [Claude Code](https://code.claude.com/docs/en/agent-sdk/user-input), [Cursor Agent](https://prod.cursor.com/docs/agent/overview), and [Gemini CLI](https://geminicli.com/docs/tools/ask-user/).

## Project layout

```text
skills/git-review/   Portable skill; copy this folder into an agent's skills directory
  SKILL.md           Core workflow and decision rules
  references/        Scope, review method, and reporting contract
  scripts/           Optional local scope helper
tests/               Cross-platform tests for the helper and fixture generator
evals/               Disposable review cases with separate answer keys
.github/workflows/   CI for helper and fixture tests
.agents/plugins/      Codex repository marketplace
plugins/git-review/    Codex plugin package with a copy of the skill
.claude-plugin/       Claude Code plugin and marketplace manifests
.cursor-plugin/       Cursor plugin and marketplace manifests
gemini-extension.json Gemini CLI extension manifest
```

## Develop and evaluate

```text
python -m unittest discover -s tests -v
python evals/build_cases.py --output ./temporary-review-cases
```

Use a **new** output directory for evaluation fixtures; the builder refuses to overwrite an existing path. Follow [the evaluation guide](evals/README.md) to run fresh agent sessions and record results. Tests verify the deterministic tooling; they cannot prove the quality of an agent's reasoning. Contributions that improve a real missed finding or false positive are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitations

The skill cannot inspect a repository or private PR the host agent cannot access. Binary or generated changes may need separate tooling. The optional helper does not fetch PR refs or submit GitHub reviews. A report should state inaccessible files, unrun checks, and stale PR heads instead of guessing.

## License

[MIT](LICENSE).
