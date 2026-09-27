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

    def test_builds_independent_repos_with_reviewable_commits(self):
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
