import base64
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_cases", ROOT / "evals" / "build_cases.py")
build_cases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_cases)


class EvalFixtureTests(unittest.TestCase):
    def test_fixture_files_cannot_modify_git_internals(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_cases.write_files(Path(temp), {".git/hooks/pre-commit": "exit 0"})
            with self.assertRaises(ValueError):
                build_cases.write_binary_files(Path(temp), {".git/config": "AA=="})
            with self.assertRaises(ValueError):
                build_cases.remove_files(Path(temp), ["../outside.txt"])

    def test_builds_independent_repos_with_reviewable_commits(self):
        cases = build_cases.load_cases()
        frozen = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cases), len(frozen) + len(json.loads(
            (ROOT / "evals" / "regression_cases.json").read_text(encoding="utf-8")
        )) + len(json.loads(
            (ROOT / "evals" / "adversarial_cases.json").read_text(encoding="utf-8")
        )))
        by_id = {case["id"]: case for case in cases}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "fixtures"
            manifest = build_cases.build(output, cases)
            self.assertEqual(len(manifest), len(cases))
            for item in manifest:
                repo = Path(item["repo"])
                self.assertTrue((repo / ".git").exists())
                head = subprocess.check_output(
                    ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
                ).strip()
                self.assertEqual(head, item["head"])
                self.assertNotEqual(item["base"], item["head"])
                self.assertFalse((repo / "cases.json").exists())
                self.assertFalse((repo / "regression_cases.json").exists())
                case = by_id[item["id"]]
                message = subprocess.check_output(
                    ["git", "-C", str(repo), "log", "-1", "--format=%B"], text=True
                ).strip()
                self.assertEqual(message, case.get("head_message", "Review target"))
                for name in case.get("remove", []):
                    self.assertFalse((repo / name).exists())
                for name, encoded in case.get("binary_after", {}).items():
                    self.assertEqual((repo / name).read_bytes(), base64.b64decode(encoded))
                expected = case["expected"]
                findings = expected.get("findings", [expected] if expected["actionable_findings"] else [])
                self.assertEqual(len(findings), expected["actionable_findings"])
                changed = set(subprocess.check_output(
                    ["git", "-C", str(repo), "diff", "--name-only", "--no-renames",
                     item["base"], item["head"]], text=True
                ).splitlines())
                for finding in findings:
                    path, line = finding["location"].split(":", 1)
                    self.assertIn(path, changed)
                    revision = item["head"] if (repo / path).exists() else item["base"]
                    source = subprocess.check_output(
                        ["git", "-C", str(repo), "show", f"{revision}:{path}"], text=True
                    )
                    self.assertLessEqual(int(line.split()[0]), len(source.splitlines()))

    def test_duplicate_case_ids_are_rejected_before_output_creation(self):
        case = {"id": "duplicate", "before": {"a.txt": "base"}, "after": {"a.txt": "head"}}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "fixtures"
            with self.assertRaises(ValueError):
                build_cases.build(output, [case, case])
            self.assertFalse(output.exists())

    def test_mutation_requires_one_exact_match(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "app.py").write_text("safe\nsafe\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_cases.apply_mutations(repo, [{"path": "app.py", "old": "safe", "new": "unsafe"}])
            self.assertEqual((repo / "app.py").read_text(), "safe\nsafe\n")
            with self.assertRaises(ValueError):
                build_cases.apply_mutations(repo, [{"path": "../escape.py", "old": "a", "new": "b"}])


if __name__ == "__main__":
    unittest.main()
