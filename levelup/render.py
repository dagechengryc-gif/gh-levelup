"""Terminal + Markdown rendering. No third-party deps, no colours required."""

from __future__ import annotations

import unicodedata
from typing import List

from .scoring import Report

BAR_FULL = "#"
BAR_EMPTY = "."
WIDTH = 24


def disp_width(text: str) -> int:
    """Terminal columns used by `text` (CJK glyphs are double width)."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - disp_width(text))


def bar(ratio: float, width: int = WIDTH) -> str:
    filled = int(round(max(0.0, min(1.0, ratio)) * width))
    return BAR_FULL * filled + BAR_EMPTY * (width - filled)


def character_sheet(report: Report) -> str:
    p = report.profile
    code, title, floor, ceiling = report.grade
    span = max(1, ceiling - floor)
    into_level = max(0, report.total - floor)
    lines: List[str] = []

    lines.append("")
    lines.append("=" * 62)
    lines.append(f"  GITHUB CHARACTER SHEET  @{p.login}")
    lines.append("=" * 62)
    if p.name or p.bio:
        lines.append(f"  {p.name or ''}  {('| ' + p.bio) if p.bio else ''}".rstrip())
    lines.append(f"  等级 {code} {title}   {report.total} / {report.maximum}")
    lines.append(f"  进度条 {bar(into_level / span)} {into_level}/{span}")
    if ceiling > report.total:
        lines.append(f"  距离下一级还差 {ceiling - report.total} 分")
    lines.append("  基础数据 " + "  ".join([
        f"仓库 {len(p.own_repos)}",
        f"star {p.total_stars}",
        f"followers {p.followers}",
        f"年贡献 {p.contributions_year}",
        f"30天活跃 {p.commit_days_30}",
        f"连击 {p.current_streak}",
        f"merged PR {p.merged_prs}",
    ]))
    if p.achievements:
        lines.append("  徽章 " + " ".join(f"[{a}]" for a in p.achievements))
    lines.append("-" * 62)

    for s in report.sections:
        lines.append(f"  {pad(s.label, 20)} {s.points:>4}/{s.maximum:<4} {bar(s.ratio, 20)}")
        for item in s.items:
            mark = "ok" if item.points == item.maximum else (".." if item.points else "!!")
            lines.append(f"    [{mark}] {pad(item.label, 18)} {item.points:>4}/{item.maximum:<4} {item.reason}")
    lines.append("-" * 62)

    quests = report.quests()
    if quests:
        lines.append("  下一步任务（按收益排序）")
        for idx, (pts, text) in enumerate(quests, 1):
            lines.append(f"    {idx}. +{pts:<3} {text}")
    lines.append("=" * 62)
    return "\n".join(lines)


def markdown(report: Report) -> str:
    p = report.profile
    code, title, floor, ceiling = report.grade
    out: List[str] = []
    out.append(f"# @{p.login} · GitHub 战力面板\n")
    out.append(f"**等级** `{code} {title}` · **总分** `{report.total}/{report.maximum}`\n")
    out.append("| 维度 | 得分 | 满格 |")
    out.append("| --- | ---: | ---: |")
    for s in report.sections:
        out.append(f"| {s.label} | {s.points} | {s.maximum} |")
    out.append("")
    out.append("| 指标 | 数值 |")
    out.append("| --- | --- |")
    out.append(f"| 原创仓库 | {len(p.own_repos)} |")
    out.append(f"| Star 合计 | {p.total_stars} |")
    out.append(f"| Followers | {p.followers} |")
    out.append(f"| 近一年贡献 | {p.contributions_year} |")
    out.append(f"| 近 30 天活跃天数 | {p.commit_days_30} |")
    out.append(f"| 当前连击 | {p.current_streak} |")
    out.append(f"| 已合并 PR | {p.merged_prs} |")
    out.append(f"| 徽章 | {', '.join(p.achievements) or '无'} |")
    out.append("")
    out.append("## 下一步任务\n")
    for idx, (pts, text) in enumerate(report.quests(10), 1):
        out.append(f"{idx}. `+{pts}` {text}")
    out.append("")
    return "\n".join(out)
