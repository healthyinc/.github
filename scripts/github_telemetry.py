#!/usr/bin/env python3
"""Resilient GitHub Application Programming Interface (API) telemetry engine.

Queries organization-scoped repository metrics from default branches (main) via
paginated Graph Query Language (GraphQL) requests with adaptive batch halving and
exponential backoff, paired with Representational State Transfer (REST) API calls
for organization membership and 52-week commit participation history.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_GRAPHQL_PAGE_SIZE = 15
MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 2.0
PARTICIPATION_WARMUP_SECONDS = 3.0
HTTP_TIMEOUT_SECONDS = 25
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

GRAPHQL_QUERY = """
query($login: String!, $pageSize: Int!, $cursor: String, $since: GitTimestamp) {
  organization(login: $login) {
    repositories(first: $pageSize, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        isPrivate
        description
        repositoryTopics(first: 10) { nodes { topic { name } } }
        languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              historyAllTime: history { totalCount }
              history30Days: history(first: 100, since: $since) {
                totalCount
                nodes { author { user { login } } }
              }
            }
          }
        }
      }
    }
  }
}
"""


def _compute_backoff_delay(attempt_index, base_delay=BASE_BACKOFF_SECONDS):
    """Computes exponential retry wait duration: delay = base_delay * (2 ** attempt_index).

    Plain-English Meaning: Doubles wait time after each transient gateway error so
    GitHub backend load balancers recover before the next request.
    Variables & Bounds: attempt_index in [0, MAX_RETRIES - 1]; base_delay > 0.0 seconds.
    Runtime Effect: Produces 2.0s, 4.0s, 8.0s, and 16.0s retry intervals.
    """
    return base_delay * (2 ** attempt_index)


def query_graphql_page(token, org_name, cursor, since_iso, page_size=DEFAULT_GRAPHQL_PAGE_SIZE, sleep_fn=time.sleep):
    """Executes one paginated GraphQL query, halving pageSize on gateway timeouts.

    Adaptive Batch Equation: current_size = max(1, current_size // 2)
    Plain-English Meaning: Halves repositories per request whenever GitHub's 10-second
    GraphQL timeout returns Hypertext Transfer Protocol (HTTP) 502/504.
    Variables & Bounds: current_size in [1, 15] repositories per GraphQL page.
    Runtime Effect: Keeps every GraphQL request well below upstream timeout limits.
    """
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Healthy-Autopilot-Engine",
    }
    current_size = max(1, int(page_size))

    for attempt in range(MAX_RETRIES):
        variables = {"login": org_name, "pageSize": current_size, "cursor": cursor, "since": since_iso}
        payload = json.dumps({"query": GRAPHQL_QUERY, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as res:
                body = json.loads(res.read().decode("utf-8"))
                if body.get("data") and body["data"].get("organization"):
                    return body
                print(f"GraphQL missing organization payload: {body.get('errors')}", file=sys.stderr)
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            print(f"GraphQL HTTP {code} on attempt {attempt + 1}/{MAX_RETRIES} (pageSize={current_size})", file=sys.stderr)
            if code not in RETRYABLE_HTTP_CODES:
                return None
            current_size = max(1, current_size // 2)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"GraphQL transport error on attempt {attempt + 1}/{MAX_RETRIES}: {exc}", file=sys.stderr)
            current_size = max(1, current_size // 2)

        if attempt + 1 < MAX_RETRIES:
            sleep_fn(_compute_backoff_delay(attempt))
    return None


def fetch_rest_json(token, endpoint, sleep_fn=time.sleep):
    """Fetches a GitHub REST API endpoint with transient retry handling."""
    url = f"https://api.github.com/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Healthy-Autopilot-Engine",
    }
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as res:
                raw = res.read().decode("utf-8")
                return res.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            if code in RETRYABLE_HTTP_CODES and attempt + 1 < MAX_RETRIES:
                sleep_fn(_compute_backoff_delay(attempt))
                continue
            return code, None
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt + 1 < MAX_RETRIES:
                sleep_fn(_compute_backoff_delay(attempt))
                continue
            return 0, None
    return 0, None


def classify_repository(name, description, topics, languages, domains, default_domain):
    """Assigns a repository to its highest-scoring engineering or scientific domain."""
    scores = {d["name"]: 0 for d in domains}
    weighted_text = []
    if name:
        weighted_text.append((name.lower(), 3))
    if description:
        weighted_text.append((description.lower(), 1))
    for topic in topics:
        weighted_text.append((topic.lower(), 2))

    for domain_cfg in domains:
        d_name = domain_cfg["name"]
        for text, weight in weighted_text:
            for kw in domain_cfg["keywords"]:
                if kw in text:
                    scores[d_name] += weight
        for lang in languages:
            if lang.lower() in domain_cfg["languages"]:
                scores[d_name] += 2

    best_domain = max(scores, key=scores.get)
    return default_domain if scores[best_domain] == 0 else best_domain


def fetch_weekly_activity(token, org_name, repo_names, sleep_fn=time.sleep):
    """Aggregates 52-week commit counts across repositories, warming HTTP 202 caches."""
    weekly_activity = [0] * 52
    pending_repos = list(repo_names)

    for pass_idx in range(3):
        if not pending_repos:
            break
        if pass_idx > 0:
            sleep_fn(PARTICIPATION_WARMUP_SECONDS)

        still_pending = []
        for repo in pending_repos:
            status, data = fetch_rest_json(token, f"repos/{org_name}/{repo}/stats/participation", sleep_fn=sleep_fn)
            if status == 202:
                still_pending.append(repo)
            elif status == 200 and isinstance(data, dict):
                counts = data.get("all", [])
                if len(counts) == 52:
                    for i in range(52):
                        weekly_activity[i] += counts[i]
                elif not counts and pass_idx < 2:
                    still_pending.append(repo)
        pending_repos = still_pending
    return weekly_activity


def fetch_live_stats(token, config, sleep_fn=time.sleep):
    """Collects validated organization-wide telemetry across all default branches."""
    org_name = config.ORG_NAME
    since_iso = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    _, org_info = fetch_rest_json(token, f"orgs/{org_name}", sleep_fn=sleep_fn)
    org_info = org_info if isinstance(org_info, dict) else {}
    private_repos = org_info.get("total_private_repos", 0)
    public_repos = org_info.get("public_repos", 0)
    expected_total = private_repos + public_repos

    _, members_raw = fetch_rest_json(token, f"orgs/{org_name}/members?per_page=100", sleep_fn=sleep_fn)
    members_list = [m["login"] for m in members_raw] if isinstance(members_raw, list) else []
    _, outside_raw = fetch_rest_json(token, f"orgs/{org_name}/outside_collaborators?per_page=100", sleep_fn=sleep_fn)
    outside_list = [c["login"] for c in outside_raw] if isinstance(outside_raw, list) else []

    authorized_map = {login.lower(): login for login in (members_list + outside_list)}
    org_member_count = len(members_list) if members_list else len(config.CORE_COLLABORATORS)

    domain_names = [d["name"] for d in config.DOMAINS]
    domain_commits_lifetime = {name: 0 for name in domain_names}
    domain_commits_30_days = {name: 0 for name in domain_names}
    languages_size = {}
    active_devs = set()
    repo_names = []
    total_commits_lifetime = 0
    total_commits_30_days = 0

    cursor = None
    has_next_page = True
    while has_next_page:
        result = query_graphql_page(token, org_name, cursor, since_iso, sleep_fn=sleep_fn)
        if not result:
            print("ERROR: GraphQL pagination aborted due to upstream error.", file=sys.stderr)
            return None

        repo_block = result["data"]["organization"]["repositories"]
        for node in repo_block["nodes"]:
            r_name = node["name"]
            repo_names.append(r_name)

            repo_langs = []
            for edge in (node.get("languages") or {}).get("edges", []):
                lang = edge["node"]["name"]
                languages_size[lang] = languages_size.get(lang, 0) + edge["size"]
                repo_langs.append(lang)

            topics = [t["topic"]["name"] for t in (node.get("repositoryTopics") or {}).get("nodes", [])]
            domain = classify_repository(
                r_name, node.get("description") or "", topics, repo_langs, config.DOMAINS, config.DEFAULT_DOMAIN
            )

            target = (node.get("defaultBranchRef") or {}).get("target") or {}
            c_life = (target.get("historyAllTime") or {}).get("totalCount", 0)
            total_commits_lifetime += c_life
            domain_commits_lifetime[domain] += c_life

            hist_30 = target.get("history30Days") or {}
            c_30 = hist_30.get("totalCount", 0)
            total_commits_30_days += c_30
            domain_commits_30_days[domain] += c_30

            for commit in hist_30.get("nodes", []):
                login = ((commit.get("author") or {}).get("user") or {}).get("login")
                if not login or "bot" in login.lower() or login == "github-actions":
                    continue
                if not authorized_map or login.lower() in authorized_map:
                    active_devs.add(authorized_map.get(login.lower(), login))

        has_next_page = repo_block["pageInfo"]["hasNextPage"]
        cursor = repo_block["pageInfo"]["endCursor"]

    if private_repos > 0 and len(repo_names) <= public_repos:
        print(f"ERROR: Token only returned {len(repo_names)} repos despite {private_repos} private repos.", file=sys.stderr)
        return None

    min_required = max(1, expected_total // 2) if expected_total > 0 else 1
    if total_commits_lifetime == 0 or len(repo_names) < min_required:
        print(f"ERROR: Telemetry incomplete ({len(repo_names)} repos, {total_commits_lifetime} commits).", file=sys.stderr)
        return None

    weekly_activity = fetch_weekly_activity(token, org_name, repo_names, sleep_fn=sleep_fn)
    display_total = expected_total if expected_total >= len(repo_names) else len(repo_names)

    return {
        "total_repos": display_total,
        "private_repos": private_repos,
        "public_repos": public_repos if expected_total > 0 else len(repo_names),
        "org_members": org_member_count,
        "org_member_logins": members_list,
        "outside_collaborator_logins": outside_list,
        "active_dev_logins": sorted(active_devs),
        "active_devs": max(len(active_devs), config.MIN_DISPLAY_ACTIVE_CONTRIBUTORS),
        "total_commits_30_days": total_commits_30_days,
        "total_commits_lifetime": total_commits_lifetime,
        "languages": languages_size,
        "weekly_activity": weekly_activity,
        "domain_commits_lifetime": domain_commits_lifetime,
        "domain_commits_30_days": domain_commits_30_days,
    }
