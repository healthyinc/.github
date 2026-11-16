#!/usr/bin/env python3
"""Falsifiable unit tests for GitHub GraphQL pagination, backoff, and scope guards."""

import io
import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import github_telemetry
import org_config


class _MockResponse:
    def __init__(self, status, payload):
        self.status = status
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def _repo_node(name, is_priv, lang, size, c_life, c_30, authors):
    return {
        "name": name, "isPrivate": is_priv, "description": "Python model",
        "repositoryTopics": {"nodes": []},
        "languages": {"edges": [{"size": size, "node": {"name": lang}}] if lang else []},
        "defaultBranchRef": {"target": {
            "historyAllTime": {"totalCount": c_life},
            "history30Days": {"totalCount": c_30, "nodes": [
                {"author": {"user": {"login": a}}} for a in authors
            ]},
        }},
    }


class GithubTelemetryTests(unittest.TestCase):
    def test_graphql_502_adaptive_halving_and_multipage_aggregation(self):
        """Verifies 502 retry halves pageSize (15 -> 7) and sums paginated commits accurately."""
        observed_sizes, sleeps = [], []

        def fake_urlopen(req, timeout=25):
            url = req.full_url
            if url.endswith("/graphql"):
                vars_in = json.loads(req.data.decode("utf-8"))["variables"]
                observed_sizes.append(vars_in["pageSize"])
                if len(observed_sizes) == 1:
                    raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, io.BytesIO(b""))
                if vars_in["cursor"] is None:
                    node = _repo_node("r1", True, "Python", 4096, 120, 15, ["Chali-healthy", "alistairewj", "bot[bot]"])
                    return _MockResponse(200, {"data": {"organization": {"repositories": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "c1"}, "nodes": [node],
                    }}}})
                node = _repo_node("r2", False, "Python", 2048, 80, 10, ["anbhimi"])
                return _MockResponse(200, {"data": {"organization": {"repositories": {
                    "pageInfo": {"hasNextPage": False, "endCursor": "c2"}, "nodes": [node],
                }}}})
            if "/orgs/" in url and url.endswith(org_config.ORG_NAME):
                return _MockResponse(200, {"public_repos": 1, "total_private_repos": 1})
            if "/members" in url:
                return _MockResponse(200, [{"login": "Chali-healthy"}, {"login": "anbhimi"}])
            if "/outside_collaborators" in url:
                return _MockResponse(200, [])
            if "/stats/participation" in url:
                return _MockResponse(200, {"all": [1] * 51 + [5]})
            raise AssertionError(f"Unexpected URL: {url}")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            stats = github_telemetry.fetch_live_stats("tok", org_config, sleep_fn=sleeps.append)

        self.assertEqual((observed_sizes[:2], sleeps[0]), ([15, 7], 2.0))
        self.assertEqual((stats["total_commits_lifetime"], stats["total_commits_30_days"]), (200, 25))
        self.assertEqual((stats["languages"]["Python"], stats["weekly_activity"][51]), (6144, 10))
        self.assertEqual(stats["active_dev_logins"], ["Chali-healthy", "anbhimi"])

    def test_private_scope_guard_and_participation_202_warmup(self):
        """Verifies public-only fallback guard aborts and HTTP 202 participation retries sum cleanly."""
        def degraded_urlopen(req, timeout=25):
            url = req.full_url
            if url.endswith("/graphql"):
                node = _repo_node(".github", False, "", 0, 12, 2, [])
                return _MockResponse(200, {"data": {"organization": {"repositories": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [node],
                }}}})
            if "/orgs/" in url and url.endswith(org_config.ORG_NAME):
                return _MockResponse(200, {"public_repos": 1, "total_private_repos": 4})
            return _MockResponse(200, [])

        with patch("urllib.request.urlopen", side_effect=degraded_urlopen):
            self.assertIsNone(github_telemetry.fetch_live_stats("tok", org_config, sleep_fn=lambda _: None))

        attempts = {"n": 0}
        def fake_rest(token, endpoint, sleep_fn=None):
            attempts["n"] += 1
            return (202, {}) if attempts["n"] == 1 else (200, {"all": [0] * 50 + [3, 7]})

        with patch.object(github_telemetry, "fetch_rest_json", side_effect=fake_rest):
            weekly = github_telemetry.fetch_weekly_activity("tok", "org", ["repo-a"], sleep_fn=lambda _: None)
        self.assertEqual((attempts["n"], weekly[50], weekly[51]), (2, 3, 7))


if __name__ == "__main__":
    unittest.main()
