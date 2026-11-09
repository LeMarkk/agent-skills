"""devkit's skills are well formed and stay small."""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "plugins", "devkit", "skills")
SKILL_BYTES_MAX = 12 * 1024  # README: devkit skills stay under 12 KB
DESCRIPTION_CHARS_MAX = 512


class DevkitSkills(unittest.TestCase):
    def test_each_skill_is_well_formed(self):
        names = sorted(os.listdir(SKILLS))
        self.assertIn("safe-rename", names)
        self.assertIn("report-deck", names)
        for name in names:
            path = os.path.join(SKILLS, name, "SKILL.md")
            with self.subTest(skill=name):
                self.assertTrue(os.path.isfile(path), f"{name} has no SKILL.md")
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                m = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", text)
                self.assertIsNotNone(m, f"{name}: frontmatter must start with name and description")
                self.assertEqual(m.group(1).strip(), name)
                self.assertLessEqual(len(m.group(2)), DESCRIPTION_CHARS_MAX, f"{name}: description too long")
                self.assertLessEqual(len(text.encode("utf-8")), SKILL_BYTES_MAX, f"{name}: SKILL.md over 12 KB")

    def test_report_deck_carries_no_personal_settings(self):
        with open(os.path.join(SKILLS, "report-deck", "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotRegex(text, r"claude\.ai/artifact/[A-Za-z0-9]{10,}", "real artifact links belong in ~/.claude/report-deck.json")
        self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
