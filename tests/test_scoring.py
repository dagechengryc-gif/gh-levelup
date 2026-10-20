import unittest

from levelup.model import Profile, Repo
from levelup.scoring import BADGE_CAP, BASE_MAXIMUM, audit, level_for, tier


def blank(**kw):
    return Profile(login="tester", **kw)


def full():
    repos = [
        Repo("tool", description="does a thing", language="Python", stars=40,
             has_readme=True, has_license=True, has_ci=True, has_tests=True, pushed_at="2026-10-01"),
        Repo("notes", description="notes", language="Go", stars=2, has_readme=True),
        Repo("web", description="web thing", language="TypeScript", stars=1, has_readme=True),
        Repo("cli", description="cli", language="Rust", has_readme=True),
        Repo("lib", description="lib", language="C", has_readme=True),
    ]
    return Profile(
        login="tester", name="Tester", bio="backend engineer, Go & Python",
        blog="https://example.com", location="Shanghai", company="@acme",
        avatar_url="https://avatars.example.com/u/1",
        followers=60, contributions_year=900, commit_days_30=30, current_streak=12,
        merged_prs=70, reviews=35, issues=10, has_profile_readme=True,
        achievements=["pull-shark", "yolo", "quickdraw", "pair-extraordinaire",
                      "starstruck", "galaxy-brain", "public-sponsor"],
        repos=repos,
    )


class TestTier(unittest.TestCase):
    def test_zero_value_scores_zero(self):
        self.assertEqual(tier(0, ((0, 0), (10, 20))), 0)

    def test_highest_reached_threshold_wins(self):
        steps = ((0, 0), (10, 20), (50, 60))
        self.assertEqual(tier(9, steps), 0)
        self.assertEqual(tier(10, steps), 20)
        self.assertEqual(tier(49, steps), 20)
        self.assertEqual(tier(5000, steps), 60)


class TestLevel(unittest.TestCase):
    def test_floor_and_ceiling(self):
        code, title, floor, ceiling = level_for(0)
        self.assertEqual((code, floor, ceiling), ("L1", 0, 150))
        code, title, floor, ceiling = level_for(400)
        self.assertEqual((code, floor, ceiling), ("L3", 320, 500))

    def test_top_level_has_no_ceiling_gap(self):
        code, _, floor, ceiling = level_for(950)
        self.assertEqual(code, "L7")
        self.assertEqual(floor, 900)
        self.assertEqual(ceiling, 950)


class TestAudit(unittest.TestCase):
    def test_empty_profile_is_bottom_of_the_ladder(self):
        report = audit(blank())
        self.assertLess(report.total, 60)
        self.assertEqual(report.grade[0], "L1")

    def test_full_profile_is_top_of_the_ladder(self):
        report = audit(full())
        self.assertGreaterEqual(report.total, 900)
        self.assertEqual(report.grade[0], "L7")

    def test_sections_never_exceed_their_maximum(self):
        for profile in (blank(), full()):
            for section in audit(profile).sections:
                self.assertLessEqual(section.points, section.maximum, section.key)
                for item in section.items:
                    self.assertLessEqual(item.points, item.maximum, item.key)

    def test_total_is_the_sum_of_sections(self):
        report = audit(full())
        self.assertEqual(report.total, sum(s.points for s in report.sections))
        self.assertEqual(sum(x.points for x in report.sections if x.key != "bonus"), report.total - report.by_key()["bonus"].points)
        self.assertEqual(report.maximum, BASE_MAXIMUM + BADGE_CAP)

    def test_missing_bio_is_flagged(self):
        report = audit(blank())
        bio = next(i for s in report.sections for i in s.items if i.key == "bio")
        self.assertEqual(bio.points, 0)
        self.assertIn("简介", bio.reason)

    def test_profile_readme_is_the_biggest_single_profile_win(self):
        with_readme = audit(blank(has_profile_readme=True)).by_key()["profile"].points
        without = audit(blank()).by_key()["profile"].points
        self.assertEqual(with_readme - without, 70)

    def test_bonus_is_capped(self):
        many = [f"badge-{i}" for i in range(20)]
        bonus = audit(blank(achievements=many)).by_key()["bonus"]
        self.assertEqual(bonus.points, BADGE_CAP)

    def test_duplicate_badges_count_once(self):
        once = audit(blank(achievements=["yolo"])).by_key()["bonus"].points
        twice = audit(blank(achievements=["yolo", "yolo"])).by_key()["bonus"].points
        self.assertEqual(once, twice)

    def test_quests_are_sorted_by_value_and_non_empty(self):
        quests = audit(blank()).quests()
        self.assertTrue(quests)
        values = [q[0] for q in quests]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertTrue(all(v > 0 for v in values))

    def test_quests_shrink_as_the_profile_improves(self):
        empty = sum(p for p, _ in audit(blank()).quests(20))
        strong = sum(p for p, _ in audit(full()).quests(20))
        self.assertGreater(empty, strong)

    def test_weakest_targets_the_biggest_absolute_gap(self):
        top = audit(blank()).weakest(1)[0]
        self.assertEqual(top.maximum - top.points, 230)  # contributions tier


class TestModel(unittest.TestCase):
    def test_flagship_prefers_stars(self):
        profile = full()
        self.assertEqual(profile.flagship.name, "tool")

    def test_languages_are_unique_and_sorted(self):
        self.assertEqual(full().languages, sorted(set(full().languages)))

    def test_roundtrip_through_dict(self):
        profile = full()
        again = Profile.from_dict(profile.to_dict())
        self.assertEqual(audit(again).total, audit(profile).total)
        self.assertEqual([r.name for r in again.repos], [r.name for r in profile.repos])

    def test_unknown_keys_are_ignored(self):
        again = Profile.from_dict({"login": "x", "bogus": 1, "repos": [{"name": "a", "bogus": 2}]})
        self.assertEqual(again.login, "x")
        self.assertEqual(again.repos[0].name, "a")

    def test_archived_repos_do_not_count_as_own(self):
        profile = Profile(login="x", repos=[Repo("a"), Repo("b", archived=True)])
        self.assertEqual([r.name for r in profile.own_repos], ["a"])


if __name__ == "__main__":
    unittest.main()
