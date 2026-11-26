#!/usr/bin/env python3
"""Entrypoint orchestrator for updating GitHub organization profile README and SVG assets.

Combines validated GitHub Application Programming Interface (API) telemetry from
github_telemetry.py with svg_charts.py to refresh Markdown sections and Scalable Vector
Graphics (SVG) charts across profile/README.md and root README.md.
"""

import os
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import org_config
from github_telemetry import fetch_live_stats
from svg_charts import generate_activity_svg, generate_languages_svg

PROFILE_README_PATH = os.path.join(SCRIPT_DIR, "../profile/README.md")
ROOT_README_PATH = os.path.join(SCRIPT_DIR, "../README.md")
LANGUAGES_SVG_PATH = os.path.join(SCRIPT_DIR, "../assets/languages.svg")
ACTIVITY_SVG_PATH = os.path.join(SCRIPT_DIR, "../assets/activity.svg")


def _activity_tier_label(commits_30_days):
    """Maps 30-day domain commit velocity to a human-readable activity tier."""
    if commits_30_days > 500:
        return "🔥 Peak Activity"
    if commits_30_days > 200:
        return "🔥 High Activity"
    if commits_30_days > 50:
        return "🟢 Steady Activity"
    return "⚪ Active Maintenance"


def build_stats_markdown(stats, config=org_config):
    """Formats the Global Activity & Infrastructure bulleted summary block."""
    languages = stats["languages"]
    total_lang_size = sum(languages.values())
    lang_pcts = {
        lang: ((size / total_lang_size) * 100.0 if total_lang_size > 0 else 0.0)
        for lang, size in languages.items()
    }
    top_langs = [lang for lang, _ in sorted(lang_pcts.items(), key=lambda x: x[1], reverse=True)[:8]]
    primary_langs_str = ", ".join(top_langs) if top_langs else "Python"

    lines = [
        config.STATS_HEADING,
        f"*   **Total Repositories:** {stats['total_repos']} Repositories ({stats['private_repos']} Private, {stats['public_repos']} Public)",
        f"*   **Organization Members:** {stats['org_members']} Active Members",
        f"*   **Total Lifetime Commits:** {stats['total_commits_lifetime']:,} Cumulative Commits",
        f"*   **Rolling 30-Day Velocity:** {stats['total_commits_30_days']:,} {config.VELOCITY_UNIT_LABEL}",
        f"*   **{config.ACTIVE_CONTRIBUTORS_LABEL}:** {stats['active_devs']} Core Contributors",
        f"*   **Primary Languages:** {primary_langs_str}",
        "",
    ]
    return "\n".join(lines)


def build_matrix_markdown(stats, config=org_config):
    """Formats the 5-column domain capability matrix with live commit counters."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    col_domain, col_stack, col_scope = config.MATRIX_HEADERS

    lines = [
        f"> Last updated: {now_utc} · {config.MATRIX_SUBTITLE}",
        "",
        f"| {col_domain} | {col_stack} | {col_scope} | Lifetime Commits | 30-Day Velocity |",
        "| :--- | :---: | :--- | :---: | :---: |",
    ]
    for domain_cfg in config.DOMAINS:
        d_name = domain_cfg["name"]
        badges = " ".join(config.BADGE_LIBRARY[b] for b in domain_cfg["badges"])
        c_life = stats["domain_commits_lifetime"].get(d_name, 0)
        c_30 = stats["domain_commits_30_days"].get(d_name, 0)
        tier = _activity_tier_label(c_30)
        lines.append(
            f"| **{d_name}** | {badges} | {domain_cfg['scope']} | 📦 {c_life:,} Commits | 🚀 {c_30:,} Commits<br>{tier} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_collaborators_markdown(stats, config=org_config):
    """Builds the circular GitHub avatar strip for organization contributors and maintainers."""
    seen_lower = set()
    ordered_entries = []

    for login, title in config.CORE_COLLABORATORS:
        seen_lower.add(login.lower())
        ordered_entries.append((login, title))

    candidate_logins = list(stats.get("active_dev_logins", []))
    if config.AUTO_INCLUDE_ALL_ORG_MEMBERS:
        candidate_logins.extend(stats.get("org_member_logins", []))
        candidate_logins.extend(stats.get("outside_collaborator_logins", []))

    for login in candidate_logins:
        if login and login.lower() not in seen_lower and "bot" not in login.lower():
            seen_lower.add(login.lower())
            ordered_entries.append((login, f"@{login}"))

    lines = ['<p align="left">']
    for login, title in ordered_entries:
        safe_login = escape(login, {'"': "&quot;"})
        safe_title = escape(title, {'"': "&quot;"})
        lines.append(
            f'  <a href="https://github.com/{safe_login}" title="{safe_title}">'
            f'<img src="https://github.com/{safe_login}.png" width="56" height="56" '
            f'style="border-radius: 50%; margin-right: 12px; border: 2px solid #58a6ff;" '
            f'alt="@{safe_login}" /></a>'
        )
    lines.append("</p>")
    return "\n".join(lines)


def replace_tag_block(content, start_tag, end_tag, replacement):
    """Replaces text enclosed between start_tag and end_tag comment markers."""
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return content, False
    updated = content[: start_idx + len(start_tag)] + "\n" + replacement + "\n" + content[end_idx:]
    return updated, True


def update_readme_files(stats_md, matrix_md, collaborators_md=None, profile_path=PROFILE_README_PATH, root_path=ROOT_README_PATH):
    """Writes updated telemetry sections to profile/README.md and mirrors to root README.md."""
    if not os.path.exists(profile_path):
        print(f"ERROR: Profile README not found at {profile_path}", file=sys.stderr)
        return False

    with open(profile_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    content, ok_stats = replace_tag_block(content, "<!-- START_STATS -->", "<!-- END_STATS -->", stats_md)
    if not ok_stats:
        print("ERROR: START_STATS / END_STATS markers missing in profile/README.md", file=sys.stderr)
        return False

    content, ok_matrix = replace_tag_block(content, "<!-- START_MATRIX -->", "<!-- END_MATRIX -->", matrix_md)
    if not ok_matrix:
        print("ERROR: START_MATRIX / END_MATRIX markers missing in profile/README.md", file=sys.stderr)
        return False

    if collaborators_md and "<!-- START_COLLABORATORS -->" in content:
        content, _ = replace_tag_block(content, "<!-- START_COLLABORATORS -->", "<!-- END_COLLABORATORS -->", collaborators_md)

    with open(profile_path, "w", encoding="utf-8") as handle:
        handle.write(content)

    if root_path:
        with open(root_path, "w", encoding="utf-8") as handle:
            handle.write(content)

    print("README.md (profile/ and root) updated with live telemetry.")
    return True


def main():
    """CLI entrypoint invoked by GitHub Actions twice-daily scheduled workflow."""
    primary_token = (os.environ.get("ORG_PROFILE_TOKEN") or "").strip()
    fallback_token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    token = primary_token if primary_token and primary_token != '""' else fallback_token

    if not token or token == '""':
        print("ERROR: No GitHub API token provided in ORG_PROFILE_TOKEN or GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching live telemetry for @{org_config.ORG_NAME} from GitHub API...")
    stats = fetch_live_stats(token, org_config)
    if not stats:
        print("ERROR: Telemetry collection failed validation. Preserving existing profile files.", file=sys.stderr)
        sys.exit(1)

    stats_md = build_stats_markdown(stats, org_config)
    matrix_md = build_matrix_markdown(stats, org_config)
    collaborators_md = build_collaborators_markdown(stats, org_config)

    if not update_readme_files(stats_md, matrix_md, collaborators_md):
        sys.exit(1)

    generate_languages_svg(stats["languages"], LANGUAGES_SVG_PATH)
    generate_activity_svg(stats["weekly_activity"], ACTIVITY_SVG_PATH)
    print("All organization profile Markdown and SVG assets updated cleanly.")


if __name__ == "__main__":
    main()
