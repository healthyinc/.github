#!/usr/bin/env python3
"\""
update_readme.py
Updates the healthyinc GitHub profile README with live statistics.
Supports in-memory aggregation of private repository activity to protect IP.
Requires ORG_PROFILE_TOKEN to run.
"\""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

ORG_NAME = "healthyinc"
READ_ME_PATH = os.path.join(os.path.dirname(__file__), "../profile/README.md")
LANGUAGES_SVG_PATH = os.path.join(os.path.dirname(__file__), "../assets/languages.svg")
ACTIVITY_SVG_PATH = os.path.join(os.path.dirname(__file__), "../assets/activity.svg")

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
    except Exception as e:
        print(f"GraphQL Query Error: {e}", file=sys.stderr)
        return None

def fetch_participation_stats(token, repo_name):
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/stats/participation"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Healthy-Autopilot-Engine"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("all", [])
    except Exception as e:
        print(f"Failed to fetch participation for {repo_name}: {e}", file=sys.stderr)
        return []

def fetch_live_stats(token):
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    variables = {"login": ORG_NAME, "cursor": None, "since": since_date}
    
    total_commits = 0
    languages_size = {}
    active_devs = set()
    has_solana_repo = False
    repo_names = []
    
    has_next_page = True
    while has_next_page:
        result = query_graphql(token, variables)
        if not result or "data" not in result or not result["data"]["organization"]:
            print("GraphQL query failed.", file=sys.stderr)
            return None
            
        repo_data = result["data"]["organization"]["repositories"]
        for node in repo_data["nodes"]:
            repo_names.append(node["name"])
            
            if "solana" in node["name"].lower() or "svm" in node["name"].lower():
                has_solana_repo = True
                
            if node["languages"]:
                for edge in node["languages"]["edges"]:
                    lang = edge["node"]["name"]
                    size = edge["size"]
                    languages_size[lang] = languages_size.get(lang, 0) + size
            
            ref = node["defaultBranchRef"]
            if ref and ref["target"] and "history" in ref["target"]:
                history = ref["target"]["history"]
                total_commits += history["totalCount"]
                for commit in history["nodes"]:
                    author = commit.get("author")
                    if author and author.get("user"):
                        username = author["user"]["login"]
                        if "bot" not in username.lower() and username != "github-actions":
                            active_devs.add(username)
                            
        has_next_page = repo_data["pageInfo"]["hasNextPage"]
        variables["cursor"] = repo_data["pageInfo"]["endCursor"]
        
    weekly_activity = [0] * 52
    for repo in repo_names:
        activity = fetch_participation_stats(token, repo)
        if activity and len(activity) == 52:
            for i in range(52):
                weekly_activity[i] += activity[i]
        
    return {
        "total_commits": total_commits,
        "languages": languages_size,
        "active_devs": len(active_devs) if active_devs else 1,
        "has_solana_repo": has_solana_repo,
        "weekly_activity": weekly_activity
    }

def generate_languages_svg(languages_size):
    os.makedirs(os.path.dirname(LANGUAGES_SVG_PATH), exist_ok=True)
    sorted_langs = sorted(languages_size.items(), key=lambda x: x[1], reverse=True)[:12]
    
    width = 850
    item_height = 24
    header_height = 45
    footer_height = 20
    height = header_height + (len(sorted_langs) * item_height) + footer_height
    
    chart_start_x = 220
    chart_max_width = 580
    
    if not sorted_langs:
        max_kb = 1.0
    else:
        max_kb = max(size for _, size in sorted_langs) / 1024.0
        max_kb = max(max_kb, 100.0)
        
    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>
  <text x="{chart_start_x + (chart_max_width / 2)}" y="22" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11" text-anchor="middle">KB</text>
  <g fill="#c9d1d9" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11">
'''
    ticks = 10
    for i in range(1, ticks + 1):
        t = (max_kb / ticks) * i
        tx = chart_start_x + (t / max_kb) * chart_max_width
        svg_content += f'    <text x="{tx:.1f}" y="35" text-anchor="middle">{int(t)}</text>\n'
        svg_content += f'    <line x1="{tx:.1f}" y1="38" x2="{tx:.1f}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'
        
    axis_start_x = chart_start_x
    axis_end_x = chart_start_x + chart_max_width
    svg_content += f'    <line x1="{axis_start_x}" y1="43" x2="{axis_end_x}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg_content += f'    <line x1="{chart_start_x}" y1="43" x2="{chart_start_x}" y2="{height - 15}" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg_content += "  </g>\n\n  <g>\n"
    
    orange_color = "#f0883e"
    total_size = sum(size for _, size in sorted_langs)
    
    for i, (lang, size) in enumerate(sorted_langs):
        y_pos = header_height + (i * item_height)
        kb = size / 1024.0
        pct = (size / total_size) * 100 if total_size > 0 else 0
        bar_len = (kb / max_kb) * chart_max_width
        label_str = f"{lang} ({pct:.1f}%)"
        
        svg_content += f'    <text x="{chart_start_x - 10}" y="{y_pos + 12}" fill="#c9d1d9" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="12" text-anchor="end">{label_str}</text>\n'
        svg_content += f'    <rect x="{chart_start_x + 1}" y="{y_pos + 1}" width="{bar_len:.1f}" height="15" rx="1" fill="{orange_color}"/>\n'
        
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    svg_content += f'  <text x="30" y="{height - 5}" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="10">Last updated: {current_time}</text>\n'
    svg_content += "  </g>\n</svg>\n"
    
    with open(LANGUAGES_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated languages SVG.")

def generate_activity_svg(weekly_activity):
    os.makedirs(os.path.dirname(ACTIVITY_SVG_PATH), exist_ok=True)
    width = 850
    height = 220
    
    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>
  <text x="30" y="32" fill="#f0f6fc" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="700">Organization Activity History (Last 52 Weeks)</text>
  <g fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">
'''
    max_commits = max(weekly_activity) if weekly_activity and max(weekly_activity) > 0 else 10
    for i in range(4, -1, -1):
        y_val = int((max_commits / 4) * i)
        y_pos = 172 - (i * 30)
        svg_content += f'    <text x="30" y="{y_pos + 3}">{y_val}</text>\n'
        if i > 0:
            svg_content += f'    <line x1="60" y1="{y_pos}" x2="810" y2="{y_pos}" stroke="#21262d" stroke-width="1" stroke-dasharray="2 2"/>\n'
        else:
            svg_content += f'    <line x1="60" y1="{y_pos}" x2="810" y2="{y_pos}" stroke="#30363d" stroke-width="1.5"/>\n'
            
    svg_content += "  </g>\n  <g transform=\"translate(60, 0)\">\n"
    
    bar_width = 10
    gap = 4
    
    for i, count in enumerate(weekly_activity):
        x = i * (bar_width + gap)
        h = (count / max_commits) * 120
        y = 172 - h
        if h > 0:
            svg_content += f'    <rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{h:.1f}" fill="#39d353" rx="1"/>\n'
            
    svg_content += "  </g>\n"
    svg_content += f'''  <g transform="translate(60, 192)" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">
    <text x="0">1 Year Ago</text>
    <text x="375" text-anchor="middle">6 Months Ago</text>
    <text x="750" text-anchor="end">Now</text>
  </g>
'''
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    svg_content += f'  <text x="30" y="{height - 5}" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="10">Last updated: {current_time}</text>\n'
    svg_content += "</svg>\n"
    
    with open(ACTIVITY_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated activity SVG.")

def build_stats_markdown(stats):
    total_commits = stats["total_commits"]
    active_devs = stats["active_devs"]
    languages = stats["languages"]
    
    total_lang_size = sum(languages.values())
    lang_pcts = {}
    for lang, size in languages.items():
        lang_pcts[lang] = (size / total_lang_size) * 100 if total_lang_size > 0 else 0
        
    sorted_langs = sorted(lang_pcts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    stats_md = f"### 📈 Global Activity (Last 30 Days)\n"
    stats_md += f"*   **Total Commits:** {total_commits:,} commits\n"
    stats_md += f"*   **Active Developers:** {active_devs} developers\n"
    stats_md += f"*   **Primary Languages:** {', '.join([l[0] for l in sorted_langs])}\n"
    
    return stats_md

def update_readme(stats_md):
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
    
    if not token or token == '""' or token.strip() == "":
        print("ERROR: No API token provided. Script cannot run live stats.", file=sys.stderr)
        sys.exit(1)
        
    print("Token found. Accessing live GitHub API...")
    stats = fetch_live_stats(token)
    if not stats:
        print("ERROR: Failed to fetch live stats. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    stats_md = build_stats_markdown(stats)
    update_readme(stats_md)
    generate_languages_svg(stats["languages"])
    generate_activity_svg(stats["weekly_activity"])

if __name__ == "__main__":
    main()
