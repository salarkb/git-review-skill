#!/usr/bin/env python3
"""Prepare separate reviewer fixtures and judge keys for manual blind evals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_cases import build


def prepare(case_files: list[Path], reviewer_dir: Path, judge_dir: Path) -> list[dict]:
    reviewer_dir = reviewer_dir.resolve()
    judge_dir = judge_dir.resolve()
    if reviewer_dir == judge_dir or reviewer_dir in judge_dir.parents or judge_dir in reviewer_dir.parents:
        raise ValueError("Reviewer and judge directories must be separate, non-nested paths.")
    if reviewer_dir.exists() or judge_dir.exists():
        raise ValueError("Both output directories must be new.")

    cases = []
    for source in case_files:
        loaded = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise ValueError(f"Case file must contain a list: {source}")
        for case in loaded:
            if not isinstance(case, dict) or "expected" not in case:
                raise ValueError(f"Case has no judge key: {source}")
            cases.append(case)
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Case ids must be unique across all files.")

    manifest = build(reviewer_dir, cases)
    tasks = [
        {
            "id": item["id"],
            "repo": item["id"],
            "base": item["base"],
            "head": item["head"],
            "prompt": f"Use git-review to review commit {item['head']}. Report only actionable findings and risks.",
        }
        for item in manifest
    ]
    (reviewer_dir / "manifest.json").write_text(
        json.dumps([{**item, "repo": item["id"]} for item in manifest], indent=2) + "\n",
        encoding="utf-8",
    )
    (reviewer_dir / "review_tasks.json").write_text(
        json.dumps(tasks, indent=2) + "\n", encoding="utf-8"
    )

    judge_dir.mkdir(parents=True)
    revisions = {item["id"]: item for item in manifest}
    keys = [
        {
            "id": case["id"],
            "base": revisions[case["id"]]["base"],
            "head": revisions[case["id"]]["head"],
            "purpose": case.get("purpose"),
            "expected": case["expected"],
        }
        for case in cases
    ]
    (judge_dir / "answer_keys.json").write_text(
        json.dumps(keys, indent=2) + "\n", encoding="utf-8"
    )
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, nargs="+", required=True)
    parser.add_argument("--reviewer-dir", type=Path, required=True)
    parser.add_argument("--judge-dir", type=Path, required=True)
    args = parser.parse_args()
    tasks = prepare(args.cases, args.reviewer_dir, args.judge_dir)
    print(f"Prepared {len(tasks)} blind review tasks in {args.reviewer_dir}")
    print(f"Judge keys stored separately in {args.judge_dir}")


if __name__ == "__main__":
    main()
