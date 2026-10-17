"""Snapshot fetchers.

Two backends, same output:

* ``gh`` CLI (preferred -- it already handles auth, tokens and SSO)
* REST/GraphQL over urllib with ``GITHUB_TOKEN`` / ``GH_TOKEN``

Network code stays here so :mod:`levelup.scoring` can be tested offline.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import ssl
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .model import Profile, Repo

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"

PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    login name bio websiteUrl location company avatarUrl
    followers { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: [OWNER], isFork: false,
                 privacy: PUBLIC, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description stargazerCount forkCount pushedAt isArchived
        primaryLanguage { name }
        licenseInfo { key }
        readme: object(expression: "HEAD:README.md") { __typename }
        ci: object(expression: "HEAD:.github/workflows") { __typename }
        tests: object(expression: "HEAD:tests") { __typename }
        spec: object(expression: "HEAD:test") { __typename }
      }
    }
  }
}
"""

SEARCH_QUERY = """
query($q: String!) {
  search(query: $q, type: ISSUE, first: 1) { issueCount }
}
"""

BADGE_RE = re.compile(r"achievements/([a-z0-9-]+)/detail")


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------
def _gh() -> Optional[str]:
    return shutil.which("gh")


def _run_gh(args: List[str], stdin: Optional[str] = None) -> Any:
    proc = subprocess.run(
        [_gh(), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()[:400]}")
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def _token() -> Optional[str]:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def graphql(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    if _gh():
        args = ["api", "graphql", "-f", "query=" + query]
        for key, value in variables.items():
            args += ["-F", "{0}={1}".format(key, value)]
        payload = _run_gh(args)
        if payload.get("errors"):
            raise RuntimeError(json.dumps(payload["errors"])[:400])
        return payload["data"]
    token = _token()
    if not token:
        raise RuntimeError("需要 `gh` CLI，或环境变量 GITHUB_TOKEN/GH_TOKEN")
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "gh-levelup",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"])[:400])
    return payload["data"]


def _http(url: str) -> str:
    """Fetch text. curl first (its CA bundle is reliable), urllib as fallback."""
    if shutil.which("curl"):
        proc = subprocess.run(
            ["curl", "-fsSL", "-A", "gh-levelup", url],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            return proc.stdout
    headers = {"User-Agent": "gh-levelup"}
    token = _token()
    if token:
        headers["Authorization"] = "bearer " + token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.URLError:
        # Some Python builds ship without a CA bundle; retry unverified for
        # a public, read-only profile page.
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.read().decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# derived stats
# ---------------------------------------------------------------------------
def streak_and_recent(days: List[Dict[str, Any]], today: Optional[_dt.date] = None) -> Dict[str, int]:
    """Current consecutive-day streak (ending today/yesterday) + active days in 30."""
    today = today or _dt.date.today()
    counts = {d["date"]: int(d.get("contributionCount") or 0) for d in days}
    window = [(today - _dt.timedelta(days=i)).isoformat() for i in range(30)]
    active_30 = sum(1 for d in window if counts.get(d, 0) > 0)

    streak = 0
    cursor = today
    # A streak is still alive if today is empty but yesterday is not.
    if counts.get(cursor.isoformat(), 0) == 0:
        cursor -= _dt.timedelta(days=1)
    while counts.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= _dt.timedelta(days=1)
    return {"commit_days_30": active_30, "current_streak": streak}


def parse_achievements(html: str) -> List[str]:
    """Pull badge slugs out of a rendered profile page."""
    seen: List[str] = []
    for slug in BADGE_RE.findall(html or ""):
        if slug not in seen:
            seen.append(slug)
    return sorted(seen)


def fetch_achievements(login: str) -> List[str]:
    try:
        return parse_achievements(_http(f"https://github.com/{login}"))
    except (urllib.error.URLError, OSError, ValueError):
        return []


# ---------------------------------------------------------------------------
# main entry
# ---------------------------------------------------------------------------
def fetch_profile(login: str, with_achievements: bool = True) -> Profile:
    data = graphql(PROFILE_QUERY, {"login": login})
    user = data.get("user")
    if not user:
        raise RuntimeError(f"用户不存在或不可见：{login}")

    repos: List[Repo] = []
    for node in (user.get("repositories") or {}).get("nodes") or []:
        repos.append(Repo(
            name=node["name"],
            description=(node.get("description") or "").strip() or None,
            language=(node.get("primaryLanguage") or {}).get("name"),
            stars=int(node.get("stargazerCount") or 0),
            forks=int(node.get("forkCount") or 0),
            has_readme=bool(node.get("readme")),
            has_license=bool(node.get("licenseInfo")),
            has_ci=bool(node.get("ci")),
            has_tests=bool(node.get("tests") or node.get("spec")),
            archived=bool(node.get("isArchived")),
            pushed_at=node.get("pushedAt"),
        ))

    calendar = (user.get("contributionsCollection") or {}).get("contributionCalendar") or {}
    days = [d for w in calendar.get("weeks") or [] for d in w.get("contributionDays") or []]
    derived = streak_and_recent(days)

    def count(query: str) -> int:
        try:
            return int(graphql(SEARCH_QUERY, {"q": query})["search"]["issueCount"])
        except (RuntimeError, KeyError, TypeError):
            return 0

    return Profile(
        login=user["login"],
        name=(user.get("name") or "").strip() or None,
        bio=(user.get("bio") or "").strip() or None,
        blog=(user.get("websiteUrl") or "").strip() or None,
        location=(user.get("location") or "").strip() or None,
        company=(user.get("company") or "").strip() or None,
        avatar_url=user.get("avatarUrl"),
        followers=int((user.get("followers") or {}).get("totalCount") or 0),
        contributions_year=int(calendar.get("totalContributions") or 0),
        commit_days_30=derived["commit_days_30"],
        current_streak=derived["current_streak"],
        merged_prs=count(f"author:{login} is:pr is:merged"),
        reviews=count(f"reviewed-by:{login} is:pr"),
        issues=count(f"author:{login} is:issue"),
        has_profile_readme=any(r.name.lower() == login.lower() for r in repos),
        achievements=fetch_achievements(login) if with_achievements else [],
        repos=repos,
        captured_at=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    )
