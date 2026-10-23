#!/usr/bin/env python3
"""Regenerate the stat block inside a profile README.

The block is fenced by ``<!-- LEVELUP:START ... -->`` / ``<!-- LEVELUP:END -->``
markers so the script never touches the rest of the file.

    python3 scripts/sync_profile.py --readme ../profile-repo/README.md --user me
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from levelup.api import fetch_profile  # noqa: E402
from levelup.scoring import audit  # noqa: E402

START = "<!-- LEVELUP:START"
END = "<!-- LEVELUP:END -->"
BLOCK_RE = re.compile(r"<!-- LEVELUP:START.*?<!-- LEVELUP:END -->", re.S)


def block(profile) -> str:
    report = audit(profile)
    code, title, _, _ = report.grade
    rows = [
        ("等级", f"`{code} {title}` · {report.total}/{report.maximum}"),
        ("原创仓库", str(len(profile.own_repos))),
        ("已合并 PR", str(profile.merged_prs)),
        ("近一年贡献", str(profile.contributions_year)),
        ("当前连击", f"{profile.current_streak} 天"),
        ("徽章", ", ".join(profile.achievements) or "暂无"),
    ]
    lines = ["<!-- LEVELUP:START 由 gh-levelup audit 生成，勿手改 -->", "", "| 指标 | 数值 |", "| --- | --- |"]
    lines += [f"| {k} | {v} |" for k, v in rows]
    lines += ["", END]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="同步 profile README 里的战绩块")
    ap.add_argument("--readme", type=Path, required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--check", action="store_true", help="只比对，不写回（CI 用）")
    args = ap.parse_args()

    text = args.readme.read_text(encoding="utf-8")
    if not BLOCK_RE.search(text):
        print(f"{args.readme} 里找不到 LEVELUP 标记", file=sys.stderr)
        return 2

    fresh = block(fetch_profile(args.user))
    if args.check:
        ok = fresh in text
        print("已同步" if ok else "需要更新")
        return 0 if ok else 1

    args.readme.write_text(BLOCK_RE.sub(lambda _: fresh, text, count=1), encoding="utf-8")
    print(f"已更新 {args.readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
