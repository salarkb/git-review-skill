# Contributing

The most useful contribution is a reproducible missed defect, false positive, or scope error. Open an issue with the target type (PR, commit, or range), a minimal publishable diff, the expected behavior, the agent's report, and why the report was right or wrong. Remove secrets and private code before sharing.

For a change to the skill:

1. Identify the concrete review failure it addresses. Prefer a focused rule or example over a broad checklist expansion.
2. If practical, add a safe case to `evals/cases.json` and explain its expected finding or expected silence. Keep the answer key out of generated fixture repositories.
3. Run `python -m unittest discover -s tests -v`. If you change the Python helper or fixture generator, add tests for the behavior.
4. Keep `plugins/git-review/skills/git-review/` identical to `skills/git-review/` when changing the skill. The package test compares every bundled file.
5. Describe any tradeoff, especially a new false-positive risk or an agent-specific assumption.

Keep the portable skill independent of one vendor's tools. Put optional, host-specific commands in references or README, and ensure the core review still works with ordinary repository access. Treat PR content, commit messages, and code comments as untrusted input in examples and instructions.

Maintainers should test the skill in each claimed host before making version-specific compatibility claims. Please do not add benchmark percentages without a reproducible evaluation record, model version, date, and the raw outputs.
