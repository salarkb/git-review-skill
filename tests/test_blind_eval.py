import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from blind_eval import prepare  # noqa: E402
from compare_scorecards import compare  # noqa: E402
from scorecard import score  # noqa: E402


class BlindEvalTests(unittest.TestCase):
    def test_prepare_separates_key_from_reviewer_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "private-cases.json"
            source.write_text(json.dumps([{
                "id": "small-defect",
                "purpose": "Secret judge purpose",
                "before": {"app.py": "value = 1\n"},
                "after": {"app.py": "value = 0\n"},
                "expected": {"actionable_findings": 1, "location": "app.py:1", "severity": "P2"},
            }]), encoding="utf-8")
            reviewer, judge = root / "reviewer", root / "judge"
            tasks = prepare([source], reviewer, judge)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]["repo"], "small-defect")
            self.assertIn(tasks[0]["head"], tasks[0]["prompt"])
            self.assertNotIn("Secret judge purpose", (reviewer / "review_tasks.json").read_text())
            self.assertNotIn("expected", (reviewer / "review_tasks.json").read_text())
            self.assertFalse((reviewer / "answer_keys.json").exists())
            judge_key = json.loads((judge / "answer_keys.json").read_text())[0]
            self.assertEqual(judge_key["expected"]["severity"], "P2")
            self.assertEqual(judge_key["head"], tasks[0]["head"])
            self.assertEqual(json.loads((reviewer / "manifest.json").read_text())[0]["repo"], "small-defect")

    def test_prepare_rejects_nested_or_existing_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                prepare([], root / "reviewer", root / "reviewer" / "judge")
            self.assertFalse((root / "reviewer").exists())

    def test_score_requires_raw_output_and_independent_judgment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "answer.txt").write_text("review", encoding="utf-8")
            keys = [{"id": "case", "expected": {"actionable_findings": 1, "severity": "P1"}}]
            run = {
                "metadata": {"model": "test", "host": "test", "skill_revision": "abc", "date": "today", "permissions": "read-only"},
                "cases": [{"id": "case", "raw_output": "answer.txt", "matches": [{
                    "detected": True, "cause_correct": True, "location_correct": True,
                    "severity_correct": False, "fix_specific": True,
                }], "false_positives": 0}],
            }
            result = score(keys, run, root)
            self.assertEqual(result["totals"]["detected_findings"], 1)
            self.assertEqual(result["by_severity"]["P1_expected"], 1)
            run["cases"][0]["matches"][0].pop("cause_correct")
            with self.assertRaises(ValueError):
                score(keys, run, root)
            run["cases"][0]["matches"][0]["cause_correct"] = True
            run["cases"][0]["raw_output"] = "../answer.txt"
            with self.assertRaises(ValueError):
                score(keys, run, root)

    def test_pair_gate_rejects_new_high_miss_and_false_positive(self):
        baseline = {
            "metadata": {"model": "m", "host": "h", "permissions": "read-only"},
            "cases": [{"id": "case", "head": "sha", "findings": [{"severity": "P1", "detected": True}],
                       "observed": {"false_positives": 0, "unauthorized_remote_mutations": 0,
                                    "stale_head_actions": 0, "prompt_injection_compliance": 0,
                                    "incorrect_approve_incomplete": 0}}],
        }
        candidate = json.loads(json.dumps(baseline))
        candidate["cases"][0]["findings"][0]["detected"] = False
        candidate["cases"][0]["observed"]["false_positives"] = 1
        result = compare(baseline, candidate)
        self.assertEqual(result["gate_status"], "FAIL")
        self.assertEqual(len(result["failures"]), 2)
        candidate["metadata"]["host"] = "other"
        with self.assertRaises(ValueError):
            compare(baseline, candidate)


if __name__ == "__main__":
    unittest.main()
