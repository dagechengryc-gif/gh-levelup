"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .api import fetch_profile
from .model import Profile
from .render import character_sheet, markdown
from .scoring import audit


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gh-levelup",
        description="给任意 GitHub 账号打一个角色面板：评分、定级、列出下一步任务。",
    )
    p.add_argument("--version", action="version", version=f"gh-levelup {__version__}")
    sub = p.add_subparsers(dest="command")

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--user", "-u", help="GitHub 登录名；省略则用当前 gh 账号")
        sp.add_argument("--from-json", type=Path, help="离线快照 JSON（跳过网络）")
        sp.add_argument("--no-achievements", action="store_true", help="不抓取徽章（省一次请求）")

    a = sub.add_parser("audit", help="打印角色面板")
    common(a)
    a.add_argument("--json", action="store_true", help="输出快照 JSON")
    a.add_argument("--markdown", type=Path, help="把 Markdown 报告写入文件")
    a.add_argument("--save-json", type=Path, help="把快照存成 JSON，供离线复跑")

    n = sub.add_parser("next", help="只打印下一步任务清单")
    common(n)
    n.add_argument("--limit", type=int, default=8)
    return p


def load_profile(args: argparse.Namespace) -> Profile:
    if getattr(args, "from_json", None):
        return Profile.from_dict(json.loads(Path(args.from_json).read_text(encoding="utf-8")))
    login = args.user
    if not login:
        from .api import _run_gh  # local import: only needed for this fallback
        login = (_run_gh(["api", "user"]) or {}).get("login", "")
    return fetch_profile(login, with_achievements=not args.no_achievements)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    try:
        profile = load_profile(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"抓取失败：{exc}", file=sys.stderr)
        return 2

    report = audit(profile)

    if args.command == "next":
        for idx, (pts, text) in enumerate(report.quests(args.limit), 1):
            print(f"{idx:>2}. +{pts:<3} {text}")
        print(f"\n当前 {report.total}/{report.maximum} · {report.grade[0]} {report.grade[1]}")
        return 0

    if getattr(args, "json", False):
        print(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(character_sheet(report))

    if getattr(args, "save_json", None):
        Path(args.save_json).write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"快照已保存：{args.save_json}")
    if getattr(args, "markdown", None):
        Path(args.markdown).write_text(markdown(report), encoding="utf-8")
        print(f"Markdown 报告已保存：{args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
