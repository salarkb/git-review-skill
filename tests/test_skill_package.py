import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "git-review" / "SKILL.md"


class SkillPackageTests(unittest.TestCase):
    def test_portable_manifest_and_references(self):
        text = SKILL.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md needs YAML frontmatter")
        fields = dict(
            line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line
        )
        self.assertEqual(fields.get("name"), SKILL.parent.name)
        self.assertTrue(1 <= len(fields.get("description", "")) <= 1024)
        self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        for link in re.findall(r"\]\((references/[^)]+|scripts/[^)]+)\)", text):
            self.assertTrue((SKILL.parent / link).is_file(), link)

    def test_distribution_manifests_point_to_the_skill(self):
        def read(path):
            return json.loads((ROOT / path).read_text(encoding="utf-8"))

        claude_plugin = read(".claude-plugin/plugin.json")
        claude_marketplace = read(".claude-plugin/marketplace.json")
        cursor_plugin = read(".cursor-plugin/plugin.json")
        cursor_marketplace = read(".cursor-plugin/marketplace.json")
        gemini_extension = read("gemini-extension.json")

        for manifest in (claude_plugin, cursor_plugin, gemini_extension):
            self.assertEqual(manifest["name"], SKILL.parent.name)
        for marketplace in (claude_marketplace, cursor_marketplace):
            self.assertEqual(marketplace["name"], "git-review-skill")
            self.assertEqual(len(marketplace["plugins"]), 1)
            self.assertEqual(marketplace["plugins"][0]["name"], SKILL.parent.name)
            self.assertEqual(marketplace["plugins"][0]["source"], ".")
        self.assertTrue(SKILL.is_file())

    def test_codex_plugin_bundles_the_same_skill(self):
        bundled = ROOT / "plugins" / "git-review" / "skills" / "git-review"
        original = SKILL.parent
        original_files = {
            path.relative_to(original): path.read_bytes()
            for path in original.rglob("*") if path.is_file()
        }
        bundled_files = {
            path.relative_to(bundled): path.read_bytes()
            for path in bundled.rglob("*") if path.is_file()
        }
        self.assertEqual(bundled_files, original_files)

        plugin = json.loads(
            (ROOT / "plugins" / "git-review" / ".codex-plugin" / "plugin.json")
            .read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(plugin["name"], original.name)
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(marketplace["name"], "git-review-skill")
        self.assertEqual(marketplace["plugins"][0]["name"], plugin["name"])
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/git-review")


if __name__ == "__main__":
    unittest.main()
