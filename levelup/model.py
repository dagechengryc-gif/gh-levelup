"""Data model for a GitHub account snapshot.

Everything the scorer needs is a plain dataclass, so a snapshot can be
captured once (network) and scored many times (pure function, offline).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Repo:
    """One public, non-fork repository owned by the account."""

    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    has_readme: bool = False
    has_license: bool = False
    has_ci: bool = False
    has_tests: bool = False
    archived: bool = False
    pushed_at: Optional[str] = None

    @property
    def is_documented(self) -> bool:
        return bool(self.has_readme and self.description)

    @property
    def is_complete(self) -> bool:
        """A repo a stranger can actually use and trust."""
        return bool(self.has_readme and self.description and self.has_license)


@dataclass
class Profile:
    """A point-in-time snapshot of one GitHub account."""

    login: str
    name: Optional[str] = None
    bio: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None
    followers: int = 0
    following: int = 0
    contributions_year: int = 0
    commit_days_30: int = 0
    current_streak: int = 0
    merged_prs: int = 0
    reviews: int = 0
    issues: int = 0
    has_profile_readme: bool = False
    achievements: List[str] = field(default_factory=list)
    repos: List[Repo] = field(default_factory=list)
    captured_at: Optional[str] = None

    # -- derived helpers -------------------------------------------------
    @property
    def own_repos(self) -> List[Repo]:
        return [r for r in self.repos if not r.archived]

    @property
    def total_stars(self) -> int:
        return sum(r.stars for r in self.repos)

    @property
    def languages(self) -> List[str]:
        return sorted({r.language for r in self.repos if r.language})

    @property
    def flagship(self) -> Optional[Repo]:
        if not self.repos:
            return None
        return max(self.repos, key=lambda r: (r.stars, r.is_complete, r.pushed_at or ""))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        raw_repos = data.get("repos") or []
        repos = [Repo(**{k: v for k, v in r.items() if k in Repo.__dataclass_fields__}) for r in raw_repos]
        scalars = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "repos"}
        scalars.setdefault("login", "unknown")
        return cls(repos=repos, **scalars)
