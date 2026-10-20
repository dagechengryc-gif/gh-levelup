import unittest

from levelup.model import Profile, Repo
from levelup.render import bar, character_sheet, markdown
from levelup.scoring import audit


def sample():
    return Profile(
        login="octo", name="Octo Cat", bio="builder", blog="https://x.dev",
        location="Sea", company="@gh", avatar_url="https://a/b.png",
        followers=12, contributions_year=120, commit_days_30=9, current_streak=3,
        merged_prs=3, reviews=4, has_profile_readme=True,
        achievements=["yolo", "quickdraw"],
        repos=[Repo("tool", description="d", language="Python", stars=5, has_readme=True)],
    )


class TestBar(unittest.TestCase):
    def test_edges(self):
        self.assertEqual(bar(0.0, 10), "." * 10)
        self.assertEqual(bar(1.0, 10), "#" * 10)
        self.assertEqual(len(bar(0.5, 10)), 10)

    def test_out_of_range_is_clamped(self):
        self.assertEqual(bar(-3, 5), ".....")
        self.assertEqual(bar(9, 5), "#####")


class TestCharacterSheet(unittest.TestCase):
    def test_contains_login_level_and_score(self):
        report = audit(sample())
        text = character_sheet(report)
        self.assertIn("@octo", text)
        self.assertIn(report.grade[0], text)
        self.assertIn(f"{report.total} / {report.maximum}", text)

    def test_lists_quests(self):
        text = character_sheet(audit(sample()))
        self.assertIn("下一步任务", text)

    def test_is_pure_ascii_friendly_enough_to_pipe(self):
        text = character_sheet(audit(Profile(login="bare")))
        self.assertNotIn("\t", text)
        self.assertTrue(all(len(line) < 200 for line in text.splitlines()))


class TestMarkdown(unittest.TestCase):
    def test_has_a_table_and_a_quest_list(self):
        md = markdown(audit(sample()))
        self.assertIn("| 维度 | 得分 | 满格 |", md)
        self.assertIn("## 下一步任务", md)
        self.assertTrue(md.startswith("# @octo"))

    def test_renders_without_badges(self):
        self.assertIn("无", markdown(audit(Profile(login="x"))))


if __name__ == "__main__":
    unittest.main()
