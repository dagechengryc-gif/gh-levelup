"""The scoring engine: deterministic, offline, dependency-free.

Score budget (1000 points):

    profile     200   who you are
    code        250   what you shipped
    activity    250   how consistently
    collab      200   how you work with others
    reach       100   who noticed
    bonus       100   achievements (capped add-on)

So the ceiling is 1000 base + 100 bonus = 1100.

Design rule: every number here is explainable in one line, because the tool
prints the reason next to the score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from .model import Profile

# (threshold, points) pairs, ascending by threshold.
Tiers = Sequence[Tuple[int, int]]


def tier(value: int, steps: Tiers) -> int:
    """Points for the highest threshold `value` reaches."""
    points = 0
    for threshold, score in steps:
        if value >= threshold:
            points = score
    return points


@dataclass
class Item:
    key: str
    label: str
    points: int
    maximum: int
    reason: str

    @property
    def ratio(self) -> float:
        return 0.0 if self.maximum == 0 else self.points / self.maximum


@dataclass
class Section:
    key: str
    label: str
    maximum: int
    items: List[Item] = field(default_factory=list)

    @property
    def points(self) -> int:
        return sum(i.points for i in self.items)

    @property
    def ratio(self) -> float:
        return 0.0 if self.maximum == 0 else self.points / self.maximum


# ---------------------------------------------------------------------------
# Level table
# ---------------------------------------------------------------------------
LEVELS: Sequence[Tuple[int, str, str]] = (
    (0, "L1", "种子 Seed"),
    (150, "L2", "青铜 Bronze"),
    (320, "L3", "白银 Silver"),
    (500, "L4", "黄金 Gold"),
    (680, "L5", "铂金 Platinum"),
    (820, "L6", "钻石 Diamond"),
    (900, "L7", "王者 Legend"),
)

BADGE_POINTS = 15
BADGE_CAP = 100
BASE_MAXIMUM = 1000
TOTAL_MAXIMUM = BASE_MAXIMUM + BADGE_CAP


def level_for(score: int) -> Tuple[str, str, int, int]:
    """Return (code, title, floor, next_threshold|score) for a total score."""
    current = LEVELS[0]
    nxt = None
    for threshold, code, title in LEVELS:
        if score >= threshold:
            current = (threshold, code, title)
        elif nxt is None:
            nxt = (threshold, code, title)
    floor, code, title = current
    ceiling = nxt[0] if nxt else score
    return code, title, floor, ceiling


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def score_profile(p: Profile) -> Section:
    s = Section("profile", "档案 Profile", 200)
    s.items.append(Item("avatar", "头像", 25 if p.avatar_url else 0, 25,
                        "有头像" if p.avatar_url else "没头像，陌生人第一眼就不信任你"))
    s.items.append(Item("name", "显示名", 20 if p.name else 0, 20,
                        "已设置" if p.name else "显示名空白"))
    bio_len = len(p.bio or "")
    s.items.append(Item("bio", "一句话简介", 30 if bio_len >= 10 else (15 if bio_len else 0), 30,
                        f"{bio_len} 字符" if bio_len else "简介空白，别人不知道你做什么"))
    s.items.append(Item("blog", "主页/社交链接", 25 if p.blog else 0, 25,
                        p.blog or "没有外链"))
    s.items.append(Item("location", "地区", 15 if p.location else 0, 15,
                        p.location or "未填"))
    s.items.append(Item("company", "组织/学校", 15 if p.company else 0, 15,
                        p.company or "未填"))
    s.items.append(Item("readme", "同名 Profile README 仓库", 70 if p.has_profile_readme else 0, 70,
                        "已上线" if p.has_profile_readme else "缺少 <login>/<login> 仓库，个人主页一片空白"))
    return s


def score_code(p: Profile) -> Section:
    s = Section("code", "代码资产 Code", 250)
    own = len(p.own_repos)
    s.items.append(Item(
        "repos", "原创仓库", tier(own, ((0, 0), (1, 30), (2, 50), (3, 70), (5, 100), (8, 125), (15, 145))), 145,
        f"{own} 个非 fork 公共仓库"))
    flag = p.flagship
    quality = 0
    if flag:
        quality = (15 if flag.has_readme else 0) + (12 if flag.has_license else 0) + (8 if flag.description else 0)
    s.items.append(Item("quality", "旗舰仓完整度", quality, 35,
                        f"{flag.name}：README{'✓' if flag and flag.has_readme else '✗'} "
                        f"LICENSE{'✓' if flag and flag.has_license else '✗'} "
                        f"简介{'✓' if flag and flag.description else '✗'}" if flag else "没有仓库"))
    has_ci = any(r.has_ci for r in p.own_repos)
    has_tests = any(r.has_tests for r in p.own_repos)
    s.items.append(Item("ci", "CI 流水线", 25 if has_ci else 0, 25,
                        "有 GitHub Actions" if has_ci else "没有 CI，代码可信度打折"))
    s.items.append(Item("tests", "测试目录", 25 if has_tests else 0, 25,
                        "有 tests/" if has_tests else "没有测试"))
    langs = len(p.languages)
    s.items.append(Item("langs", "语言多样性", tier(langs, ((0, 0), (1, 5), (2, 10), (3, 15), (4, 20))), 20,
                        f"{langs} 种：{', '.join(p.languages) or '无'}"))
    return s


def score_activity(p: Profile) -> Section:
    s = Section("activity", "活跃度 Activity", 250)
    c = p.contributions_year
    s.items.append(Item(
        "contrib", "近一年贡献", tier(c, ((0, 0), (10, 20), (50, 60), (150, 110), (300, 160), (500, 200), (800, 230))), 230,
        f"{c} 次 contribution"))
    d = p.commit_days_30
    s.items.append(Item(
        "days", "近30天提交天数", tier(d, ((0, 0), (5, 5), (10, 10), (20, 20), (30, 20))), 20,
        f"{d}/30 天"))
    return s


def score_collab(p: Profile) -> Section:
    s = Section("collab", "协作 Collaboration", 200)
    m = p.merged_prs
    s.items.append(Item(
        "prs", "已合并 PR", tier(m, ((0, 0), (1, 30), (2, 60), (5, 90), (16, 130), (64, 170))), 170,
        f"{m} 个 merged PR"))
    r = p.reviews
    s.items.append(Item(
        "reviews", "代码评审", tier(r, ((0, 0), (3, 10), (10, 20), (30, 30))), 30,
        f"{r} 次 review"))
    return s


def score_reach(p: Profile) -> Section:
    s = Section("reach", "影响力 Reach", 100)
    st = p.total_stars
    s.items.append(Item(
        "stars", "仓库 Star", tier(st, ((0, 0), (3, 15), (10, 30), (16, 45), (50, 65), (150, 85))), 85,
        f"{st} stars"))
    f = p.followers
    s.items.append(Item(
        "followers", "关注者", tier(f, ((0, 0), (3, 5), (10, 10), (50, 15))), 15,
        f"{f} followers"))
    return s


def score_bonus(p: Profile) -> Section:
    s = Section("bonus", "成就 Achievements", BADGE_CAP)
    got = sorted(set(p.achievements))
    pts = min(len(got) * BADGE_POINTS, BADGE_CAP)
    s.items.append(Item("badges", "徽章", pts, BADGE_CAP,
                        f"{len(got)} 枚：{', '.join(got) if got else '还没有'}"))
    return s


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
@dataclass
class Report:
    profile: Profile
    sections: List[Section]

    @property
    def total(self) -> int:
        return sum(s.points for s in self.sections)

    @property
    def maximum(self) -> int:
        return sum(s.maximum for s in self.sections)

    @property
    def grade(self):
        return level_for(self.total)

    def by_key(self) -> Dict[str, Section]:
        return {s.key: s for s in self.sections}

    def weakest(self, n: int = 3) -> List[Item]:
        """Biggest absolute point leaks first — that's where the ROI is."""
        leaks = []
        for s in self.sections:
            for i in s.items:
                if i.maximum - i.points > 0:
                    leaks.append(i)
        leaks.sort(key=lambda i: (i.maximum - i.points), reverse=True)
        return leaks[:n]

    def quests(self, limit: int = 8) -> List[Tuple[int, str]]:
        """Actionable quests derived from the exact gaps, highest value first."""
        g = self.by_key()
        out: List[Tuple[int, str]] = []

        def add(pts: int, text: str) -> None:
            if pts > 0:
                out.append((pts, text))

        if not self.profile.has_profile_readme:
            add(70, "建 `<login>/<login>` 仓库并写 Profile README（模板见本仓 `docs/profile-readme.md`）")
        if not self.profile.bio:
            add(30, "补 profile bio：一句话写清『我是谁 + 我做什么 + 找我合作什么』")
        if not self.profile.blog:
            add(25, "补主页/社交链接（博客、X、掘金、知乎任选）")
        if not self.profile.avatar_url:
            add(25, "上传头像")
        if not self.profile.name:
            add(20, "填显示名")
        if not self.profile.location:
            add(15, "填地区")
        if not self.profile.company:
            add(15, "填组织/学校（在职或在校都可）")

        code = g["code"]
        repo_item = next(i for i in code.items if i.key == "repos")
        add(repo_item.maximum - repo_item.points,
            "把私有项目里可开源的部分抽成 3~5 个原创仓库（每个都要 README + LICENSE + 简介）")
        ci = next(i for i in code.items if i.key == "ci")
        add(ci.maximum - ci.points, "给旗舰仓加 GitHub Actions：`.github/workflows/ci.yml` 跑测试")
        tq = next(i for i in code.items if i.key == "tests")
        add(tq.maximum - tq.points, "加 `tests/`，哪怕先只有 5 个断言，CI 才有意义")
        q = next(i for i in code.items if i.key == "quality")
        add(q.maximum - q.points, "旗舰仓补齐 README/LICENSE/Description 三件套")

        act = g["activity"]
        c = next(i for i in act.items if i.key == "contrib")
        add(min(c.maximum - c.points, 120),
            f"每天至少 1 次有意义的 commit（当前 {self.profile.contributions_year} 次/年，目标 500+）；用 `scripts/backfill.py` 补历史格不算真本事，长期靠习惯")

        collab = g["collab"]
        pr = next(i for i in collab.items if i.key == "prs")
        add(min(pr.maximum - pr.points, 70),
            f"给别人的仓库提 PR（当前 {self.profile.merged_prs} 个已合并）；从文档纠错、i18n、小 bug 入手，2 个就能拿 Pull Shark")
        rv = next(i for i in collab.items if i.key == "reviews")
        add(rv.maximum - rv.points, "去 review 别人的 PR：3 次起有分，也是最快建立人脉的方式")

        reach = g["reach"]
        st = next(i for i in reach.items if i.key == "stars")
        add(min(st.maximum - st.points, 45),
            "做一件别人真的会用的小工具，发到 V2EX/HN/Reddit/r/Python，16 star 即解锁 Starstruck")

        bonus = g["bonus"]
        b = bonus.items[0]
        add(min(b.maximum - b.points, 60),
            "徽章：Pull Shark(2 merged PR) / YOLO(无 review 合并自己的 PR) / Quickdraw(5 分钟内关 issue) / Pair Extraordinaire(合并 PR 里带 Co-authored-by) / Galaxy Brain(Discussion 被采纳 2 次) / Starstruck(16 star)")

        out.sort(key=lambda x: -x[0])
        return out[:limit]


def audit(p: Profile) -> Report:
    return Report(profile=p, sections=[
        score_profile(p),
        score_code(p),
        score_activity(p),
        score_collab(p),
        score_reach(p),
        score_bonus(p),
    ])
