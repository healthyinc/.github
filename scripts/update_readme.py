#!/usr/bin/env python3
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
query($login: String!, $cursor: String, $since: GitTimestamp) {
  organization(login: $login) {
    repositories(first: 100, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        description
        repositoryTopics(first: 10) {
          nodes {
            topic {
              name
            }
          }
        }
        languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
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
              historyAllTime: history {
                totalCount
              }
              history30Days: history(since: $since) {
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

def fetch_rest_api(token, endpoint):
    url = f"https://api.github.com/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Healthy-Autopilot-Engine"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"REST API Error ({endpoint}): {e}", file=sys.stderr)
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
        return []

def classify_repository(name, description, topics, languages):
    scores = {
        "DeFi & Web3 Tokenomics": 0,
        "Agentic AI & LLM Systems": 0,
        "HealthTech & Mobile Ecosystem": 0,
        "Cybersecurity & Compliance": 0
    }
    
    keywords = {
        "DeFi & Web3 Tokenomics": ["token", "web3", "solana", "evm", "defi", "habitcoin", "bioblock", "bio-block", "depin", "contract", "crypto", "blockchain", "shadow", "eclipse", "circom", "zk"],
        "Agentic AI & LLM Systems": ["ai", "llm", "agent", "model", "intelligence", "data-lab", "harness", "machine learning", "ml", "bmad", "golang", "go"],
        "HealthTech & Mobile Ecosystem": ["app", "mobile", "health", "ui", "react", "hospital", "frontend", "portal", "telehealth", "fhir", "hl7", "expo"],
        "Cybersecurity & Compliance": ["security", "threat", "audit", "defense", "posture", "cyber", "zero-trust", "hipaa", "compliance", "nitro", "enclave"]
    }
    
    langs = {
        "DeFi & Web3 Tokenomics": ["solidity", "rust", "circom"],
        "Agentic AI & LLM Systems": ["python", "jupyter notebook", "go"],
        "HealthTech & Mobile Ecosystem": ["kotlin", "swift", "java", "dart", "objective-c", "typescript", "javascript"],
        "Cybersecurity & Compliance": ["shell", "dockerfile", "powershell", "batchfile"]
    }

    text_to_search = []
    if name: text_to_search.append((name.lower(), 3))
    if description: text_to_search.append((description.lower(), 1))
    for t in topics:
        text_to_search.append((t.lower(), 2))

    for domain, kws in keywords.items():
        for text, weight in text_to_search:
            for kw in kws:
                if kw in text:
                    scores[domain] += weight

    for lang in languages:
        l = lang.lower()
        for domain, l_list in langs.items():
            if l in l_list:
                scores[domain] += 2
                
    max_domain = max(scores, key=scores.get)
    if scores[max_domain] == 0:
        return "HealthTech & Mobile Ecosystem"
    return max_domain

BADGE_LIBRARY = {
    "solana": '![Solana](https://img.shields.io/badge/Solana_SVM-14F195?style=flat-square&logo=solana&logoColor=black)',
    "rust": '![Rust Anchor](https://img.shields.io/badge/Rust_Anchor-000000?style=flat-square&logo=rust&logoColor=white)',
    "ethereum": '![Ethereum EVM](https://img.shields.io/badge/Ethereum_EVM-3C3C3D?style=flat-square&logo=ethereum&logoColor=white)',
    "solidity": '![Solidity](https://img.shields.io/badge/Solidity-363636?style=flat-square&logo=solidity&logoColor=white)',
    "typescript": '![TypeScript](https://img.shields.io/badge/TypeScript-2B7489?style=flat-square&logo=typescript&logoColor=white)',
    "eclipse": '![Eclipse SVM](https://img.shields.io/badge/Eclipse_SVM-000000?style=flat-square&logo=e&logoColor=14F195)',
    "shadow": '![Shadow Drive](https://img.shields.io/badge/Shadow_DePIN-7E57C2?style=flat-square&logo=serverless&logoColor=white)',
    "circom": '![Circom ZK](https://img.shields.io/badge/Circom_ZK-FF5722?style=flat-square&logo=webassembly&logoColor=white)',
    "python": '![Python](https://img.shields.io/badge/Python-3572A5?style=flat-square&logo=python&logoColor=white)',
    "go": '![Go](https://img.shields.io/badge/Go_Lang-00ADD8?style=flat-square&logo=go&logoColor=white)',
    "pytorch": '![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)',
    "fastapi": '![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)',
    "bmad": '![BMAD Orchestrator](https://img.shields.io/badge/BMAD_Agentic-6A1B9A?style=flat-square&logo=target&logoColor=white)',
    "vllm": '![vLLM Inference](https://img.shields.io/badge/vLLM-4CAF50?style=flat-square&logo=openai&logoColor=white)',
    "react native": '![React Native](https://img.shields.io/badge/React_Native-61DAFB?style=flat-square&logo=react&logoColor=black)',
    "expo": '![Expo](https://img.shields.io/badge/Expo-000020?style=flat-square&logo=expo&logoColor=white)',
    "kotlin": '![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white)',
    "swift": '![Swift](https://img.shields.io/badge/Swift-FA7343?style=flat-square&logo=swift&logoColor=white)',
    "next.js": '![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=next.js&logoColor=white)',
    "fhir": '![FHIR / HL7](https://img.shields.io/badge/FHIR_HL7-E91E63?style=flat-square&logo=health-icons&logoColor=white)',
    "nitro": '![AWS Nitro](https://img.shields.io/badge/Nitro_Enclaves-FF9900?style=flat-square&logo=amazon-aws&logoColor=white)',
    "tls": '![TLS 1.3](https://img.shields.io/badge/TLS_1.3_mTLS-0288D1?style=flat-square&logo=letsencrypt&logoColor=white)',
    "docker": '![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)',
    "shell": '![Shell](https://img.shields.io/badge/Shell-4EAA25?style=flat-square&logo=gnu-bash&logoColor=white)',
    "hipaa": '![HIPAA Zero-Trust](https://img.shields.io/badge/HIPAA_Zero--Trust-000000?style=flat-square&logo=shield&logoColor=white)',
}

def fetch_live_stats(token):
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    variables = {"login": ORG_NAME, "cursor": None, "since": since_date}
    
    total_commits_30_days = 0
    total_commits_lifetime = 0
    languages_size = {}
    active_devs = set()
    repo_names = []
    
    domain_commits_lifetime = {
        "DeFi & Web3 Tokenomics": 0,
        "Agentic AI & LLM Systems": 0,
        "HealthTech & Mobile Ecosystem": 0,
        "Cybersecurity & Compliance": 0
    }
    
    domain_commits_30_days = {
        "DeFi & Web3 Tokenomics": 0,
        "Agentic AI & LLM Systems": 0,
        "HealthTech & Mobile Ecosystem": 0,
        "Cybersecurity & Compliance": 0
    }
    
    org_info = fetch_rest_api(token, f"orgs/{ORG_NAME}") or {}
    total_private_repos = org_info.get("total_private_repos", 38)
    public_repos = org_info.get("public_repos", 3)
    total_repos = total_private_repos + public_repos
    
    members_data = fetch_rest_api(token, f"orgs/{ORG_NAME}/members") or []
    org_member_count = len(members_data) if members_data else 11
    
    has_next_page = True
    while has_next_page:
        result = query_graphql(token, variables)
        if not result or "data" not in result or not result["data"].get("organization"):
            break
            
        repo_data = result["data"]["organization"]["repositories"]
        for node in repo_data["nodes"]:
            repo_name = node["name"]
            repo_names.append(repo_name)
            
            repo_langs = []
            if node.get("languages"):
                for edge in node["languages"]["edges"]:
                    lang = edge["node"]["name"]
                    size = edge["size"]
                    languages_size[lang] = languages_size.get(lang, 0) + size
                    repo_langs.append(lang)
            
            topics = []
            if node.get("repositoryTopics"):
                for topic_node in node["repositoryTopics"]["nodes"]:
                    topics.append(topic_node["topic"]["name"])
                    
            desc = node.get("description") or ""
            domain = classify_repository(repo_name, desc, topics, repo_langs)
            
            repo_c_30 = 0
            repo_c_life = 0
            ref = node.get("defaultBranchRef")
            if ref and ref.get("target"):
                target = ref["target"]
                
                if "historyAllTime" in target:
                    repo_c_life = target["historyAllTime"]["totalCount"]
                    total_commits_lifetime += repo_c_life
                    domain_commits_lifetime[domain] += repo_c_life
                    
                if "history30Days" in target:
                    history = target["history30Days"]
                    repo_c_30 = history["totalCount"]
                    total_commits_30_days += repo_c_30
                    domain_commits_30_days[domain] += repo_c_30
                    
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
        "total_repos": total_repos,
        "private_repos": total_private_repos,
        "public_repos": public_repos,
        "org_members": org_member_count,
        "total_commits_30_days": total_commits_30_days,
        "total_commits_lifetime": total_commits_lifetime,
        "languages": languages_size,
        "active_devs": len(active_devs) if active_devs else 3,
        "weekly_activity": weekly_activity,
        "domain_commits_lifetime": domain_commits_lifetime,
        "domain_commits_30_days": domain_commits_30_days
    }

def generate_languages_svg(languages_size):
    os.makedirs(os.path.dirname(LANGUAGES_SVG_PATH), exist_ok=True)
    sorted_langs = sorted(languages_size.items(), key=lambda x: x[1], reverse=True)[:25]
    
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

def build_stats_markdown(stats):
    total_repos = stats["total_repos"]
    priv_repos = stats["private_repos"]
    pub_repos = stats["public_repos"]
    org_members = stats["org_members"]
    c_30 = stats["total_commits_30_days"]
    c_life = stats["total_commits_lifetime"]
    active_devs = stats["active_devs"]
    languages = stats["languages"]
    
    total_lang_size = sum(languages.values())
    lang_pcts = {}
    for lang, size in languages.items():
        lang_pcts[lang] = (size / total_lang_size) * 100 if total_lang_size > 0 else 0
        
    sorted_langs = sorted(lang_pcts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    stats_md = f"### 📈 Global Ecosystem Activity & Infrastructure\n"
    stats_md += f"*   **Total Repositories:** {total_repos} Repositories ({priv_repos} Private, {pub_repos} Public)\n"
    stats_md += f"*   **Organization Members:** {org_members} Active Members\n"
    stats_md += f"*   **Total Lifetime Commits:** {c_life:,} Cumulative Commits\n"
    stats_md += f"*   **Rolling 30-Day Velocity:** {c_30:,} Commits across active sprints\n"
    stats_md += f"*   **Active Developers:** {active_devs} Core Contributors\n"
    stats_md += f"*   **Primary Languages:** {', '.join([l[0] for l in sorted_langs])}\n"
    
    return stats_md

def build_matrix_markdown(stats):
    c_life = stats["domain_commits_lifetime"]
    c_30 = stats["domain_commits_30_days"]
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    def get_activity_level(commits_30):
        if commits_30 > 500: return "🔥 Peak Activity"
        elif commits_30 > 200: return "🔥 High Activity"
        elif commits_30 > 50: return "🟢 Steady Activity"
        else: return "⚪ Active Maintenance"

    md = f"> Last updated: {current_time} · Active Ecosystem Capability Overview\n\n"
    md += "| Core Engineering Domain | Technology & Tooling Stack | Domain Scope & Focus | Lifetime Commits | 30-Day Velocity |\n"
    md += "| :--- | :---: | :--- | :---: | :---: |\n"
    
    # 1. DeFi
    cl = c_life["DeFi & Web3 Tokenomics"]
    c30 = c_30["DeFi & Web3 Tokenomics"]
    defi_badges = f"{BADGE_LIBRARY['solana']} {BADGE_LIBRARY['rust']} {BADGE_LIBRARY['eclipse']} {BADGE_LIBRARY['shadow']} {BADGE_LIBRARY['ethereum']} {BADGE_LIBRARY['solidity']} {BADGE_LIBRARY['circom']} {BADGE_LIBRARY['typescript']}"
    md += f"| **DeFi & Web3 Tokenomics** | {defi_badges} | SVM/EVM Smart Contracts, Habitcoin Tokenomics, DePIN Storage & Circom ZK Circuits | 📦 {cl:,} Commits | 🚀 {c30:,} Commits<br>{get_activity_level(c30)} |\n"
    
    # 2. Agentic AI
    cl = c_life["Agentic AI & LLM Systems"]
    c30 = c_30["Agentic AI & LLM Systems"]
    ai_badges = f"{BADGE_LIBRARY['python']} {BADGE_LIBRARY['go']} {BADGE_LIBRARY['pytorch']} {BADGE_LIBRARY['fastapi']} {BADGE_LIBRARY['bmad']} {BADGE_LIBRARY['vllm']}"
    md += f"| **Agentic AI & LLM Systems** | {ai_badges} | Multi-Agent Orchestration, Bio-Engine Modeling, Predictive Health Analytics & Go Microservices | 📦 {cl:,} Commits | 🚀 {c30:,} Commits<br>{get_activity_level(c30)} |\n"
    
    # 3. HealthTech
    cl = c_life["HealthTech & Mobile Ecosystem"]
    c30 = c_30["HealthTech & Mobile Ecosystem"]
    health_badges = f"{BADGE_LIBRARY['react native']} {BADGE_LIBRARY['expo']} {BADGE_LIBRARY['kotlin']} {BADGE_LIBRARY['swift']} {BADGE_LIBRARY['next.js']} {BADGE_LIBRARY['fhir']}"
    md += f"| **HealthTech & Mobile Ecosystem** | {health_badges} | Mobile Telehealth App, Android/iOS Wrappers, FHIR/EHR Data Federation & Clinical Portals | 📦 {cl:,} Commits | 🚀 {c30:,} Commits<br>{get_activity_level(c30)} |\n"
    
    # 4. Cybersecurity
    cl = c_life["Cybersecurity & Compliance"]
    c30 = c_30["Cybersecurity & Compliance"]
    cyber_badges = f"{BADGE_LIBRARY['nitro']} {BADGE_LIBRARY['tls']} {BADGE_LIBRARY['docker']} {BADGE_LIBRARY['shell']} {BADGE_LIBRARY['hipaa']}"
    md += f"| **Cybersecurity & Compliance** | {cyber_badges} | Automated Threat Verification Harnesses, HIPAA Zero-Trust Control Enclaves & Hardware Isolation | 📦 {cl:,} Commits | 🚀 {c30:,} Commits<br>{get_activity_level(c30)} |\n"
    
    return md

def replace_tag_block(content, start_tag, end_tag, replacement):
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx == -1 or end_idx == -1:
        return content, False
        
    new_content = (
        content[:start_idx + len(start_tag)] + 
        "\n" + replacement + "\n" + 
        content[end_idx:]
    )
    return new_content, True

def update_readme(stats_md, matrix_md):
    if not os.path.exists(READ_ME_PATH):
        print(f"Error: README.md not found at {READ_ME_PATH}", file=sys.stderr)
        return False
        
    with open(READ_ME_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    content, ok = replace_tag_block(content, "<!-- START_STATS -->", "<!-- END_STATS -->", stats_md)
    if not ok:
        print("Error: Target tags for STATS not found in README.md", file=sys.stderr)
        return False
        
    content, ok = replace_tag_block(content, "<!-- START_MATRIX -->", "<!-- END_MATRIX -->", matrix_md)
    if not ok:
        print("Error: Target tags for MATRIX not found in README.md", file=sys.stderr)
        return False
        
    with open(READ_ME_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("README.md successfully updated with new stats and matrix.")
    return True

def main():
    token = os.environ.get("ORG_PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token or token == '""' or token.strip() == "":
        print("ERROR: No API token provided. Script cannot run live stats.", file=sys.stderr)
        sys.exit(1)
        
    print("Token found. Fetching live telemetry from GitHub API...")
    stats = fetch_live_stats(token)
    if not stats:
        print("ERROR: Failed to fetch live stats. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    stats_md = build_stats_markdown(stats)
    matrix_md = build_matrix_markdown(stats)
    
    update_readme(stats_md, matrix_md)
    generate_languages_svg(stats["languages"])
    generate_activity_svg(stats["weekly_activity"])
    print("All profile assets updated successfully.")

if __name__ == "__main__":
    main()
