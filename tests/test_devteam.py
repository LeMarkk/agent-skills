"""devteam's skills and agents are well formed, stay small, and every agent preloads skills that exist."""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
PLUGIN = os.path.join(REPO, "plugins", "devteam")
SKILLS = os.path.join(PLUGIN, "skills")
AGENTS = os.path.join(PLUGIN, "agents")

SKILL_BYTES_MAX = 6 * 1024
DESCRIPTION_CHARS_MAX = 320
AGENT_MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
KNOWN_TOOLS = {
    "Read", "Grep", "Glob", "Write", "Edit", "NotebookEdit", "Bash",
    "WebSearch", "WebFetch", "Skill",
}


def frontmatter(path):
    """Parse the simple YAML frontmatter used here: scalars and one-level lists."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        raise AssertionError(f"{path}: no frontmatter")
    fields, key = {}, None
    for line in match.group(1).splitlines():
        item = re.match(r"^\s+-\s+(.+)$", line)
        if item and key:
            fields[key].append(item.group(1).strip())
            continue
        pair = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if not pair:
            raise AssertionError(f"{path}: can't parse frontmatter line {line!r}")
        key, value = pair.group(1), pair.group(2).strip()
        fields[key] = value if value else []
    return fields, match.group(2)


def skill_names():
    return sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))


def agent_files():
    return sorted(f for f in os.listdir(AGENTS) if f.endswith(".md"))


class Skills(unittest.TestCase):
    def test_each_skill_is_named_after_its_folder_and_small(self):
        self.assertGreater(len(skill_names()), 0)
        for name in skill_names():
            path = os.path.join(SKILLS, name, "SKILL.md")
            with self.subTest(skill=name):
                fields, body = frontmatter(path)
                self.assertEqual(fields.get("name"), name)
                self.assertTrue(fields.get("description"), "missing description")
                self.assertLessEqual(len(fields["description"]), DESCRIPTION_CHARS_MAX,
                                     "description loads in every session; keep it short")
                self.assertLessEqual(os.path.getsize(path), SKILL_BYTES_MAX)
                self.assertTrue(body.strip().startswith(f"# {name}"))

    def test_skills_point_only_to_skills_that_exist(self):
        known = set(skill_names()) | {"debug"}  # debug comes from devkit
        for name in skill_names():
            with open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8") as f:
                text = f.read()
            for ref in re.findall(r"the `([a-z-]+)` skill", text):
                with self.subTest(skill=name, ref=ref):
                    self.assertIn(ref, known)


class Agents(unittest.TestCase):
    def test_each_agent_preloads_existing_skills_with_valid_settings(self):
        skills = set(skill_names())
        self.assertEqual(len(agent_files()), 8)
        for filename in agent_files():
            fields, body = frontmatter(os.path.join(AGENTS, filename))
            with self.subTest(agent=filename):
                self.assertEqual(fields.get("name"), filename[:-3])
                self.assertNotIn(":", fields["name"])
                self.assertTrue(fields.get("description"))
                self.assertLessEqual(len(fields["description"]), DESCRIPTION_CHARS_MAX)
                self.assertIn(fields.get("model"), AGENT_MODELS)
                for tool in re.split(r",\s*", fields.get("tools", "")):
                    self.assertIn(tool, KNOWN_TOOLS)
                preload = fields.get("skills")
                self.assertIsInstance(preload, list)
                self.assertGreater(len(preload), 0)
                for ref in preload:
                    self.assertTrue(ref.startswith("devteam:"), ref)
                    self.assertIn(ref.split(":", 1)[1], skills)
                for ignored in ("hooks", "mcpServers", "permissionMode"):
                    self.assertNotIn(ignored, fields, f"{ignored} is ignored for plugin agents")
                self.assertTrue(body.strip())

    def test_read_only_agents_cannot_edit(self):
        for name in ("reviewer", "security"):
            fields, _ = frontmatter(os.path.join(AGENTS, f"{name}.md"))
            with self.subTest(agent=name):
                tools = set(re.split(r",\s*", fields["tools"]))
                self.assertFalse(tools & {"Write", "Edit", "NotebookEdit"})

    def test_every_skill_is_used_by_an_agent_or_is_the_lead(self):
        used = {"team"}
        for filename in agent_files():
            fields, _ = frontmatter(os.path.join(AGENTS, filename))
            used |= {ref.split(":", 1)[1] for ref in fields["skills"]}
        self.assertEqual(used, set(skill_names()))

    def test_team_skill_lists_every_agent(self):
        with open(os.path.join(SKILLS, "team", "SKILL.md"), encoding="utf-8") as f:
            team = f.read()
        for filename in agent_files():
            with self.subTest(agent=filename):
                self.assertIn(f"`devteam:{filename[:-3]}`", team)


class Manifest(unittest.TestCase):
    def test_marketplace_lists_devteam(self):
        with open(os.path.join(REPO, ".claude-plugin", "marketplace.json"), encoding="utf-8") as f:
            market = json.load(f)
        entry = [p for p in market["plugins"] if p["name"] == "devteam"]
        self.assertEqual(len(entry), 1)
        self.assertEqual(entry[0]["source"], "./plugins/devteam")
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            plugin = json.load(f)
        self.assertEqual(plugin["name"], "devteam")
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
