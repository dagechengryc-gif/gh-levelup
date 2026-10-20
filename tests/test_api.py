import datetime as dt
import json
import unittest
from pathlib import Path

from levelup.api import parse_achievements, streak_and_recent
from levelup.model import Profile
from levelup.scoring import audit

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample-profile.json"


def day(offset, count, today=dt.date(2026, 10, 23)):
    return {"date": (today - dt.timedelta(days=offset)).isoformat(), "contributionCount": count}


class TestParseAchievements(unittest.TestCase):
    def test_extracts_unique_slugs_in_order(self):
        html = ('<a href="/octo?achievement=pull-shark&tab=achievements">'
                '<img src="x"></a><a href="/achievements/yolo/detail?hovercard=1"></a>'
                '<a href="/achievements/pull-shark/detail"></a>')
        self.assertEqual(parse_achievements(html), ["pull-shark", "yolo"])

    def test_empty_input(self):
        self.assertEqual(parse_achievements(""), [])
        self.assertEqual(parse_achievements("<html>nothing here</html>"), [])


class TestStreak(unittest.TestCase):
    def test_counts_consecutive_days_including_today(self):
        days = [day(0, 2), day(1, 1), day(2, 3), day(4, 1)]
        out = streak_and_recent(days, today=dt.date(2026, 10, 23))
        self.assertEqual(out["current_streak"], 3)
        self.assertEqual(out["commit_days_30"], 4)

    def test_streak_survives_an_empty_today(self):
        days = [day(1, 1), day(2, 1)]
        out = streak_and_recent(days, today=dt.date(2026, 10, 23))
        self.assertEqual(out["current_streak"], 2)

    def test_no_activity_means_no_streak(self):
        self.assertEqual(streak_and_recent([], today=dt.date(2026, 10, 23))["current_streak"], 0)

    def test_only_last_30_days_count_toward_activity(self):
        days = [day(0, 1), day(45, 5)]
        out = streak_and_recent(days, today=dt.date(2026, 10, 23))
        self.assertEqual(out["commit_days_30"], 1)


class TestOfflineSnapshot(unittest.TestCase):
    def test_sample_snapshot_is_loadable_and_scores_between_bounds(self):
        profile = Profile.from_dict(json.loads(SAMPLE.read_text(encoding="utf-8")))
        report = audit(profile)
        self.assertEqual(profile.login, "dagechengryc-gif")
        self.assertGreater(report.total, 0)
        self.assertLess(report.total, report.maximum)


if __name__ == "__main__":
    unittest.main()
