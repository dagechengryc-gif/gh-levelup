#!/usr/bin/env python3
"""Write dated commits into a log repo — the "green squares" filler.

The contribution graph only counts *commit dates*, so a backfilled history is
visually identical to real daily work while containing none of it. Use it for
demos and screenshots; the parts of the score that actually matter (merged PRs,
stars, CI, reviews) cannot be faked this way.

Usage:
    python3 scripts/backfill.py --repo /path/to/log-repo --days 60 --per-day 2
    python3 scripts/backfill.py --days 30 --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import random
import subprocess
import sys
from pathlib import Path

TOPICS = [
    "notes/reading", "notes/til", "worklog", "notes/debug", "notes/design",
]
SNIPPETS = [
    "记录一条今天真正学到的东西。",
    "记下一个踩过的坑，以及最后怎么绕过去的。",
    "把一段能复用的命令存下来。",
    "写清一个决定，以及当时的取舍。",
    "摘一段读到的源码，用一句话说明它为什么这样写。",
]


def git(repo: Path, *args: str, env: dict | None = None) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def run(repo: Path, days: int, per_day: int, seed: int, dry_run: bool) -> int:
    rng = random.Random(seed)
    today = dt.date.today()
    made = 0
    for offset in range(days, 0, -1):
        day = today - dt.timedelta(days=offset)
        for slot in range(rng.randint(0, per_day)):
            hour = 9 + (slot * 3) % 11
            minute = rng.randint(0, 59)
            stamp = dt.datetime(day.year, day.month, day.day, hour, minute, 0)
            iso = stamp.isoformat()
            target = repo / f"{rng.choice(TOPICS)}-{day.isoformat()}.md"
            body = f"# {day.isoformat()} #{slot + 1}\n\n{rng.choice(SNIPPETS)}\n"
            marker = hashlib.sha1(body.encode()).hexdigest()[:8]
            if dry_run:
                print(f"[dry] {iso}  {target.relative_to(repo)}  {marker}")
                made += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as fh:
                fh.write(body)
            git(repo, "add", "-A")
            env = {
                "GIT_AUTHOR_DATE": iso,
                "GIT_COMMITTER_DATE": iso,
                "PATH": __import__("os").environ.get("PATH", ""),
            }
            git(repo, "commit", "-q", "-m", f"notes: {day.isoformat()} #{slot + 1}",
                env=env)
            made += 1
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description="把带日期的日志提交写进一个仓库")
    ap.add_argument("--repo", type=Path, default=Path.cwd(), help="目标仓库（需已 git init）")
    ap.add_argument("--days", type=int, default=30, help="往前补多少天")
    ap.add_argument("--per-day", type=int, default=2, help="每天最多几个提交")
    ap.add_argument("--seed", type=int, default=7, help="随机种子，保证可复现")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    args = ap.parse_args()

    if not (args.repo / ".git").exists() and not args.dry_run:
        print(f"{args.repo} 不是 git 仓库，先 git init", file=sys.stderr)
        return 2
    n = run(args.repo, args.days, args.per_day, args.seed, args.dry_run)
    print(f"{'计划' if args.dry_run else '已生成'} {n} 个提交")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
