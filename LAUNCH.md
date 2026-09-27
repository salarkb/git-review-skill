# GitHub launch and discoverability

Use this page when publishing `git-review-skill` as a public repository. Search placement depends on the query, competing pages, indexing, and user behavior; no repository settings can guarantee a first-place result. The goal is to make the project easy to find **and** useful when someone lands on it.

## Repository metadata to paste into GitHub

**Name:** `git-review-skill`

**Description:** `Agent Skill for evidence-based GitHub PR and Git commit reviews with Codex, Claude Code, Cursor, and Gemini CLI.`

**Suggested topics:** `code-review`, `pull-request`, `git`, `github`, `agent-skills`, `codex`, `claude-code`, `cursor`, `gemini-cli`

Keep only topics that accurately describe the tested release. GitHub [uses topics to help people discover repositories](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics). Add the description and topics in the repository's **About** panel after publishing.

## Release checklist

1. Publish the project as `salarkb/git-review-skill` with its root `README.md`, MIT license, tests, complete `skills/git-review/` folder, and plugin manifests. Validate the Claude marketplace with `claude plugin validate . --strict` and the Codex package with `plugin-creator`'s validator before tagging a release.
2. With the public GitHub URL, test the README's Codex and Claude Code marketplace commands and Gemini extension command on clean profiles, then import the repository in Cursor. Static manifest validation does not prove that a remote install works. Submit the Cursor plugin for [marketplace review](https://prod.cursor.com/docs/plugins) if you want a public one-click listing.
3. Run the evaluation cases and publish an honest result with the agent, model, date, raw outputs, and misses. The included fixture tests check tooling; they do not measure review quality by themselves.
4. Show one real, permission-safe PR review example that demonstrates an actionable finding and one avoided false positive. Explain what changed and how the finding was verified.
5. Add a clear social preview image after the repository is public. GitHub [supports a repository social preview](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview); it helps people recognize shared links, though it is not a ranking guarantee.
6. Share the repository where developers actually discuss agent skills and code review, with a useful example or lesson. Invite reproducible feedback and turn confirmed misses or false positives into public evaluation cases.
7. Revisit the README and examples when host installation paths or behavior change. Keep claims tied to what has been tested.

## Search intent to serve

The README should answer the questions behind searches such as “AI PR review skill,” “GitHub pull request review agent,” “Git commit review skill,” and “Claude Code / Codex / Cursor / Gemini CLI code review skill.” The title, opening paragraph, installation instructions, report example, and FAQ each answer a real user question. Avoid repeating keywords without adding information; Google recommends [descriptive titles and helpful, people-first content](https://developers.google.com/search/docs/fundamentals/seo-starter-guide).

After publication, check whether the repository appears for the project name and relevant task queries. Record the query, date, locale, and result position if measuring visibility; a single search result is not a stable global rank. If you later create a site you control, use Search Console to inspect indexing and queries. A GitHub repository alone gives less control over page metadata and indexing than a site you own.
