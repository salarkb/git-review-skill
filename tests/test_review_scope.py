import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "git-review" / "scripts" / "review_scope.py"
SPEC = importlib.util.spec_from_file_location("review_scope", SCRIPT)
review_scope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_scope)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Skill Test")
        self.git("config", "user.email", "skill-test@example.invalid")

    def git(self, *args):
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout.decode().strip()

    def put(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-qm", f"write {name}")
        return self.git("rev-parse", "HEAD")

    def test_root_commit_inventory(self):
        head = self.put("first.py", "print('hello')\n")
        result = review_scope.scope(self.repo, "commit", head, None, False)
        self.assertIsNone(result["base_sha"])
        self.assertEqual(result["comparison"], "root")
        self.assertEqual(result["changed_files"], [{"status": "A", "path": "first.py"}])

    def test_regular_commit_and_rename(self):
        first = self.put("old.txt", "data\n")
        self.git("mv", "old.txt", "new.txt")
        self.git("commit", "-qm", "rename file")
        head = self.git("rev-parse", "HEAD")
        result = review_scope.scope(self.repo, "commit", head, None, False)
        self.assertEqual(result["base_sha"], first)
        self.assertEqual(result["changed_files"], [
            {"status": "R100", "old_path": "old.txt", "path": "new.txt"}
        ])
        self.assertFalse(result["working_tree_dirty"])

    def test_direct_and_merge_base_ranges_differ(self):
        common = self.put("common.txt", "base\n")
        self.git("branch", "base")
        head = self.put("feature.txt", "feature\n")
        self.git("checkout", "-q", "base")
        base = self.put("base-only.txt", "base branch\n")
        direct = review_scope.scope(self.repo, "range", base, head, False)
        pr_style = review_scope.scope(self.repo, "range", base, head, True)
        self.assertEqual(direct["base_sha"], base)
        self.assertEqual(pr_style["base_sha"], common)
        self.assertEqual([f["path"] for f in pr_style["changed_files"]], ["feature.txt"])
        self.assertIn("base-only.txt", [f["path"] for f in direct["changed_files"]])

    def test_invalid_ref_does_not_fall_back_to_head(self):
        self.put("first.txt", "content\n")
        with self.assertRaises(ValueError):
            review_scope.scope(self.repo, "commit", "does-not-exist", None, False)

    def test_pr_uses_local_merge_base_when_objects_exist(self):
        base = self.put("base.txt", "base\n")
        head = self.put("feature.txt", "feature\n")
        info = {
            "number": 42,
            "url": "https://github.com/example/project/pull/42",
            "title": "Feature",
            "baseRefName": "main",
            "baseRefOid": base,
            "headRefName": "feature",
            "headRefOid": head,
            "changedFiles": 1,
            "files": [{"path": "feature.txt"}],
        }
        with patch.object(review_scope, "gh", return_value=json.dumps(info).encode()) as mocked:
            result = review_scope.pr_scope(self.repo, "42", None)
        self.assertEqual(result["comparison"], "merge-base")
        self.assertEqual(result["base_sha"], base)
        self.assertEqual(result["changed_files"], [{"status": "A", "path": "feature.txt"}])
        mocked.assert_called_once()

    def test_pr_falls_back_to_hosted_diff_without_local_objects(self):
        self.put("base.txt", "base\n")
        info = {
            "number": 42,
            "url": "https://github.com/example/project/pull/42",
            "title": "External fork",
            "baseRefName": "main",
            "baseRefOid": "0" * 40,
            "headRefName": "feature",
            "headRefOid": "1" * 40,
            "changedFiles": 2,
            "files": [{"path": "src/file.py"}],
        }
        with patch.object(review_scope, "gh", return_value=json.dumps(info).encode()):
            result = review_scope.pr_scope(self.repo, "42", "example/project")
        self.assertEqual(result["comparison"], "hosted-pr-diff")
        self.assertIsNone(result["base_sha"])
        self.assertEqual(result["changed_files"], [{"status": "unknown", "path": "src/file.py"}])
        self.assertFalse(result["file_inventory_complete"])
        self.assertEqual(result["diff_command"][-2:], ["--repo", "example/project"])


if __name__ == "__main__":
    unittest.main()
