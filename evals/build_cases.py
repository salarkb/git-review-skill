#!/usr/bin/env python3
"""Create disposable Git repositories for the manual review evaluation cases."""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def fixture_path(repo: Path, name: str) -> Path:
    if any(part.casefold() == ".git" for part in Path(name).parts):
        raise ValueError(f"Fixture file cannot target Git internals: {name}")
    path = (repo / name).resolve()
    if not path.is_relative_to(repo.resolve()):
        raise ValueError(f"File path escapes fixture repository: {name}")
    return path


def write_files(repo: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = fixture_path(repo, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_binary_files(repo: Path, files: dict[str, str]) -> None:
    for name, encoded in files.items():
        path = fixture_path(repo, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded, validate=True))


def remove_files(repo: Path, names: list[str]) -> None:
    for name in names:
        path = fixture_path(repo, name)
        if not path.is_file():
            raise ValueError(f"Fixture file to remove does not exist: {name}")
        path.unlink()


def apply_mutations(repo: Path, mutations: list[dict[str, str]]) -> None:
    """Apply explicit, single-match text mutations to a healthy base fixture."""
    for mutation in mutations:
        path = fixture_path(repo, mutation["path"])
        if not path.is_file():
            raise ValueError(f"Mutation target does not exist: {mutation['path']}")
        old = mutation["old"]
        if not old:
            raise ValueError("Mutation old text cannot be empty.")
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise ValueError(f"Mutation must match exactly once: {mutation['path']}")
        path.write_text(source.replace(old, mutation["new"], 1), encoding="utf-8")


def load_cases() -> list[dict]:
    directory = Path(__file__).parent
    cases = []
    for name in ("cases.json", "regression_cases.json", "adversarial_cases.json"):
        cases.extend(json.loads((directory / name).read_text(encoding="utf-8")))
    return cases


def build(output: Path, cases: list[dict]) -> list[dict]:
    output = output.resolve()
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Fixture case ids must be unique.")
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
        write_binary_files(repo, case.get("binary_before", {}))
        git(repo, "add", "--all")
        git(repo, "commit", "-qm", "Base revision")
        base = git(repo, "rev-parse", "HEAD")
        remove_files(repo, case.get("remove", []))
        apply_mutations(repo, case.get("mutations", []))
        write_files(repo, case["after"])
        write_binary_files(repo, case.get("binary_after", {}))
        git(repo, "add", "--all")
        git(repo, "commit", "-qm", case.get("head_message", "Review target"))
        head = git(repo, "rev-parse", "HEAD")
        manifest.append({"id": case_id, "repo": str(repo), "base": base, "head": head})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="A new directory for fixture repositories")
    args = parser.parse_args()
    cases = load_cases()
    manifest = build(args.output, cases)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
