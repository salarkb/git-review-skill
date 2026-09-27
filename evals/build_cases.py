#!/usr/bin/env python3
"""Create disposable Git repositories for the manual review evaluation cases."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def write_files(repo: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        if any(part.casefold() == ".git" for part in Path(name).parts):
            raise ValueError(f"Fixture file cannot target Git internals: {name}")
        path = (repo / name).resolve()
        if not path.is_relative_to(repo.resolve()):
            raise ValueError(f"File path escapes fixture repository: {name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def build(output: Path, cases: list[dict]) -> list[dict]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = []
    for case in cases:
        case_id = case["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id):
            raise ValueError(f"Invalid case id: {case_id}")
        repo = output / case_id
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Review Eval")
        git(repo, "config", "user.email", "review-eval@example.invalid")
        write_files(repo, case["before"])
        git(repo, "add", "--all")
        git(repo, "commit", "-qm", "Base revision")
        base = git(repo, "rev-parse", "HEAD")
        write_files(repo, case["after"])
        git(repo, "add", "--all")
        git(repo, "commit", "-qm", "Review target")
        head = git(repo, "rev-parse", "HEAD")
        manifest.append({"id": case_id, "repo": str(repo), "base": base, "head": head})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="A new directory for fixture repositories")
    args = parser.parse_args()
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    manifest = build(args.output, cases)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
