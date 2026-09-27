#!/usr/bin/env python3
"""Resolve a Git review target without checking out or editing source files."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    command = ["git", "-C", str(repo), *args]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Git command failed: {' '.join(args)}\n{detail}")
    return result.stdout


def gh(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["gh", *args], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"GitHub CLI command failed: {' '.join(args)}\n{detail}")
    return result.stdout


def decode(value: bytes) -> str:
    return value.decode("utf-8", errors="surrogateescape")


def commit_sha(repo: Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ValueError("A commit reference must be non-empty and must not start with '-'.")
    return decode(
        git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
    ).strip()


def changed_files(data: bytes) -> list[dict[str, str]]:
    fields = data.split(b"\0")
    if fields[-1] == b"":
        fields.pop()
    files: list[dict[str, str]] = []
    index = 0
    while index < len(fields):
        status = decode(fields[index])
        index += 1
        if not status or index >= len(fields):
            raise ValueError("Unexpected Git name-status output.")
        if status[0] in "RC":
            if index + 1 >= len(fields):
                raise ValueError("Incomplete rename/copy entry in Git output.")
            old_path = decode(fields[index])
            path = decode(fields[index + 1])
            index += 2
            files.append({"status": status, "old_path": old_path, "path": path})
        else:
            files.append({"status": status, "path": decode(fields[index])})
            index += 1
    return files


def scope(repo: Path, mode: str, first: str, second: str | None, merge_base: bool) -> dict:
    root = Path(decode(git(repo, "rev-parse", "--show-toplevel")).strip())
    if mode == "commit":
        head = commit_sha(root, first)
        ancestry = decode(git(root, "rev-list", "--parents", "-n", "1", head)).split()
        parents = ancestry[1:]
        base = parents[0] if parents else None
        comparison = "first-parent" if base else "root"
    else:
        if second is None:
            raise ValueError("Range mode requires two references.")
        requested_base = commit_sha(root, first)
        head = commit_sha(root, second)
        base = (
            decode(git(root, "merge-base", requested_base, head)).strip()
            if merge_base
            else requested_base
        )
        parents = []
        comparison = "merge-base" if merge_base else "direct"

    if base is None:
        names = git(root, "diff-tree", "--root", "--no-commit-id", "-r", "-M", "--name-status", "-z", head)
        diff_command = ["git", "-C", str(root), "show", "--root", "--format=", "--no-ext-diff", head]
    else:
        names = git(root, "diff", "--no-ext-diff", "-M", "--name-status", "-z", base, head, "--")
        diff_command = ["git", "-C", str(root), "diff", "--no-ext-diff", "-M", base, head, "--"]

    result = {
        "schema_version": 1,
        "mode": mode,
        "comparison": comparison,
        "repository": str(root),
        "requested_refs": [first] if second is None else [first, second],
        "base_sha": base,
        "head_sha": head,
        "parents": parents,
        "working_tree_dirty": bool(git(root, "status", "--porcelain", "-z")),
        "changed_files": changed_files(names),
        "diff_command": diff_command,
    }
    if mode == "range":
        result["requested_base_sha"] = requested_base
    return result


def pr_scope(repo: Path, target: str, github_repo: str | None) -> dict:
    root = Path(decode(git(repo, "rev-parse", "--show-toplevel")).strip())
    repo_args = ["--repo", github_repo] if github_repo else []
    fields = "number,url,title,baseRefName,baseRefOid,headRefName,headRefOid,changedFiles,files"
    info = json.loads(decode(gh(root, "pr", "view", target, "--json", fields, *repo_args)))
    base_tip = info["baseRefOid"]
    head = info["headRefOid"]
    try:
        git(root, "cat-file", "-e", f"{base_tip}^{{commit}}")
        git(root, "cat-file", "-e", f"{head}^{{commit}}")
        local_objects = True
    except ValueError:
        local_objects = False

    if local_objects:
        base = decode(git(root, "merge-base", base_tip, head)).strip()
        files = changed_files(
            git(root, "diff", "--no-ext-diff", "-M", "--name-status", "-z", base, head, "--")
        )
        diff_command = ["git", "-C", str(root), "diff", "--no-ext-diff", "-M", base, head, "--"]
        comparison = "merge-base"
    else:
        base = None
        files = [
            {"status": "unknown", "path": item["path"]}
            for item in info["files"]
        ]
        diff_command = ["gh", "pr", "diff", target, "--patch", "--color", "never", *repo_args]
        comparison = "hosted-pr-diff"

    return {
        "schema_version": 1,
        "mode": "pr",
        "comparison": comparison,
        "repository": str(root),
        "requested_refs": [target],
        "pr_number": info["number"],
        "pr_url": info["url"],
        "pr_title": info["title"],
        "base_ref": info["baseRefName"],
        "base_tip_sha": base_tip,
        "base_sha": base,
        "head_ref": info["headRefName"],
        "head_sha": head,
        "local_objects_available": local_objects,
        "changed_file_count": info["changedFiles"],
        "file_inventory_complete": len(files) == info["changedFiles"],
        "working_tree_dirty": bool(git(root, "status", "--porcelain", "-z")),
        "changed_files": files,
        "diff_command": diff_command,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path inside the local Git repository")
    commands = parser.add_subparsers(dest="mode", required=True)
    commit = commands.add_parser("commit", help="Compare a commit with its first parent")
    commit.add_argument("ref")
    revision_range = commands.add_parser("range", help="Compare two commit endpoints")
    revision_range.add_argument("base")
    revision_range.add_argument("head")
    revision_range.add_argument(
        "--merge-base", action="store_true", help="Use PR-style merge-base comparison"
    )
    pull_request = commands.add_parser("pr", help="Inspect a GitHub PR using gh")
    pull_request.add_argument("target", help="PR number or URL")
    pull_request.add_argument("--gh-repo", help="GitHub OWNER/REPO when not inferred from the local remote")
    args = parser.parse_args()
    try:
        if args.mode == "pr":
            report = pr_scope(Path(args.repo).resolve(), args.target, args.gh_repo)
        else:
            report = scope(
                Path(args.repo).resolve(),
                args.mode,
                args.ref if args.mode == "commit" else args.base,
                None if args.mode == "commit" else args.head,
                False if args.mode == "commit" else args.merge_base,
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"review_scope: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
