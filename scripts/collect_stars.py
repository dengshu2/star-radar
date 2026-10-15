#!/usr/bin/env python3
"""汇总 TARGET_USER 关注的人在过去 WINDOW_DAYS 天内 Star 的仓库，输出 JSON 到 stdout。"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
USER = os.environ.get("TARGET_USER", "dengshu2")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = int(os.environ.get("WINDOW_DAYS", "7"))
MAX_STAR_PAGES = 3  # 每人最多翻 3 页（300 条），足够覆盖一周


def get(url, accept="application/vnd.github+json"):
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "star-radar",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 500, 502, 503) and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
            raise


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def list_following():
    logins, page = [], 1
    while True:
        data = get(f"{API}/users/{USER}/following?per_page=100&page={page}")
        if not data:
            break
        logins += [u["login"] for u in data]
        if len(data) < 100:
            break
        page += 1
    return logins


def main():
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=DAYS)
    following = list_following()
    repos, errors = {}, []

    for login in following:
        try:
            for page in range(1, MAX_STAR_PAGES + 1):
                data = get(
                    f"{API}/users/{login}/starred?per_page=100&page={page}"
                    "&sort=created&direction=desc",
                    accept="application/vnd.github.star+json",
                )
                if not data:
                    break
                reached_old = False
                for item in data:
                    starred_at = item["starred_at"]
                    if parse_ts(starred_at) < since:
                        reached_old = True
                        break
                    r = item["repo"]
                    entry = repos.setdefault(
                        r["full_name"],
                        {
                            "full_name": r["full_name"],
                            "html_url": r["html_url"],
                            "description": r.get("description") or "",
                            "language": r.get("language") or "",
                            "topics": r.get("topics") or [],
                            "stargazers_count": r.get("stargazers_count", 0),
                            "forks_count": r.get("forks_count", 0),
                            "created_at": r.get("created_at"),
                            "pushed_at": r.get("pushed_at"),
                            "archived": r.get("archived", False),
                            "fork": r.get("fork", False),
                            "starred_by": [],
                            "first_starred_at": starred_at,
                        },
                    )
                    if login not in entry["starred_by"]:
                        entry["starred_by"].append(login)
                    if starred_at < entry["first_starred_at"]:
                        entry["first_starred_at"] = starred_at
                if reached_old or len(data) < 100:
                    break
        except Exception as ex:  # 单个用户失败不影响整体
            errors.append(f"{login}: {ex}")

    for e in repos.values():
        e["network_star_count"] = len(e["starred_by"])

    ranked = sorted(
        repos.values(),
        key=lambda e: (-e["network_star_count"], -e["stargazers_count"]),
    )[:300]

    out = {
        "user": USER,
        "generated_at": now.isoformat(timespec="seconds"),
        "window_start": since.isoformat(timespec="seconds"),
        "window_end": now.isoformat(timespec="seconds"),
        "window_days": DAYS,
        "following_count": len(following),
        "repo_count": len(ranked),
        "errors": errors,
        "repos": ranked,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
