#!/usr/bin/env python3
"""
update_readme.py
Updates the healthyinc GitHub profile README with live statistics.
Supports in-memory aggregation of private repository activity to protect IP.
Automatically falls back to local simulation mode if no API token is provided.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# Configurations
ORG_NAME = "healthyinc"
READ_ME_PATH = os.path.join(os.path.dirname(__file__), "../profile/README.md")

GRAPHQL_QUERY = """
query($login: String!, $cursor: String, $since: DateTime) {
  organization(login: $login) {
    repositories(first: 100, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(since: $since) {
                totalCount
                nodes {
                  author {
                    user {
                      login
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def query_graphql(token, variables):
    """Executes a GraphQL query against the GitHub API."""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Healthy-Autopilot-Engine"
    }
    payload = json.dumps({"query": GRAPHQL_QUERY, "variables": variables}).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        body = e.read().decode("utf-8")
        print(f"Response: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Connection Error: {e}", file=sys.stderr)
        return None

def fetch_live_stats(token):
    """Queries real GitHub API and returns aggregated metrics."""
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    variables = {
        "login": ORG_NAME,
        "cursor": None,
        "since": since_date
    }
    
    total_commits = 0
    languages_size = {}
    active_devs = set()
    has_solana_repo = False
    
    has_next_page = True
    while has_next_page:
        result = query_graphql(token, variables)
        if not result or "data" not in result or not result["data"]["organization"]:
            print("GraphQL query failed. Falling back to local simulation.", file=sys.stderr)
            return None
            
        repo_data = result["data"]["organization"]["repositories"]
        for node in repo_data["nodes"]:
            # Check for Solana/SVM trigger
            if "solana" in node["name"].lower() or "svm" in node["name"].lower():
                has_solana_repo = True
                
            # Aggregate Languages (in-memory only, independent of private/public status)
            if node["languages"]:
                for edge in node["languages"]["edges"]:
                    lang = edge["node"]["name"]
                    size = edge["size"]
                    languages_size[lang] = languages_size.get(lang, 0) + size
            
            # Aggregate Commits
            ref = node["defaultBranchRef"]
            if ref and ref["target"] and "history" in ref["target"]:
                history = ref["target"]["history"]
                total_commits += history["totalCount"]
                for commit in history["nodes"]:
                    author = commit.get("author")
                    if author and author.get("user"):
                        username = author["user"]["login"]
                        # Ignore common bots
                        if "bot" not in username.lower() and username != "github-actions":
                            active_devs.add(username)
                            
        has_next_page = repo_data["pageInfo"]["hasNextPage"]
        variables["cursor"] = repo_data["pageInfo"]["endCursor"]
        
    return {
        "total_commits": total_commits,
        "languages": languages_size,
        "active_devs": len(active_devs) if active_devs else 1,
        "has_solana_repo": has_solana_repo,
        "live": True
    }

def get_simulated_stats():
    """Generates simulated statistics for local testing/fallback."""
    return {
        "total_commits": 1424,
        "languages": {
            "TypeScript": 453920,
            "JavaScript": 320100,
            "Rust": 251340,
            "Solidity": 89400,
            "Python": 143200,
            "Shell": 12400
        },
        "active_devs": 6,
        "has_solana_repo": False,
        "live": False
    }

def build_stats_markdown(stats):
    """Generates the Markdown segment to replace standard activity stats."""
    total_commits = stats["total_commits"]
    active_devs = stats["active_devs"]
    languages = stats["languages"]
    
    # Calculate language percentages
    total_lang_size = sum(languages.values())
    lang_pcts = {}
    for lang, size in languages.items():
        lang_pcts[lang] = (size / total_lang_size) * 100 if total_lang_size > 0 else 0
        
    # Sort languages by size
    sorted_langs = sorted(lang_pcts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Build Mermaid Pie Chart
    mermaid_pie = "```mermaid\npie title Language Distribution\n"
    for lang, pct in sorted_langs:
        mermaid_pie += f'    "{lang}" : {pct:.1f}\n'
    mermaid_pie += "```"
    
    stats_md = f"### 📈 Global Activity (Last 30 Days)\n"
    stats_md += f"*   **Total Commits:** {total_commits:,} commits\n"
    stats_md += f"*   **Active Developers:** {active_devs} developers\n"
    stats_md += f"*   **Primary Languages:** {', '.join([l[0] for l in sorted_langs])}\n\n"
    stats_md += f"### 💻 Code Base Language Distribution\n{mermaid_pie}\n"
    
    if not stats.get("live"):
        stats_md += "\n> [!NOTE]\n> *Note: These statistics are currently running in Simulated Mode because no API token is configured.*"
        
    return stats_md

def update_readme(stats_md):
    """Replaces content between START_STATS and END_STATS placeholders."""
    if not os.path.exists(READ_ME_PATH):
        print(f"Error: README.md not found at {READ_ME_PATH}", file=sys.stderr)
        return False
        
    with open(READ_ME_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_tag = "<!-- START_STATS -->"
    end_tag = "<!-- END_STATS -->"
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx == -1 or end_idx == -1:
        print("Error: Target tags not found in README.md", file=sys.stderr)
        return False
        
    new_content = (
        content[:start_idx + len(start_tag)] + 
        "\n" + stats_md + "\n" + 
        content[end_idx:]
    )
    
    with open(READ_ME_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("README.md successfully updated with new stats.")
    return True

def main():
    token = os.environ.get("ORG_PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    
    if token:
        print("Token found. Accessing live GitHub API...")
        stats = fetch_live_stats(token)
        if not stats:
            print("Failed to fetch live stats. Falling back to simulation...")
            stats = get_simulated_stats()
    else:
        print("No API token provided. Running in simulation mode...")
        stats = get_simulated_stats()
        
    stats_md = build_stats_markdown(stats)
    update_readme(stats_md)

if __name__ == "__main__":
    main()
