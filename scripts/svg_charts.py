#!/usr/bin/env python3
"""Scalable Vector Graphics (SVG) chart generator for GitHub organization profiles.

Renders dark-themed GitHub profile charts for repository language byte volume
in kilobytes (KB) and 52-week rolling commit history in Coordinated Universal Time (UTC).
"""

import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape


def generate_languages_svg(languages_size, output_path):
    """Writes the horizontal language distribution bar chart to output_path.

    Bar Scaling Equations:
      - kb = size_bytes / 1024.0
      - pct = (size_bytes / total_displayed_bytes) * 100.0
      - bar_len = (kb / max_kb) * chart_max_width
    Plain-English Meaning: Converts raw repository source byte counts into kilobytes (KB),
    computes each language's percentage share of the top 25 languages, and scales horizontal
    orange bars proportionally against the largest language's KB ceiling.
    Variables & Bounds:
      - size_bytes (int, >= 0): Cumulative byte size per language across repositories.
      - max_kb (float, >= 100.0 KB): Horizontal axis upper bound in KB.
      - chart_max_width (int, 580 pixels): Maximum horizontal bar span inside the 850px SVG.
    Runtime Effect: Dynamically resizes SVG height and axis ticks as languages change.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    sorted_langs = sorted(languages_size.items(), key=lambda x: x[1], reverse=True)[:25]

    width = 850
    item_height = 24
    header_height = 45
    footer_height = 20
    height = header_height + (max(len(sorted_langs), 1) * item_height) + footer_height

    chart_start_x = 220
    chart_max_width = 580

    if not sorted_langs:
        max_kb = 100.0
    else:
        max_kb = max(max(size for _, size in sorted_langs) / 1024.0, 100.0)

    svg = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="{width}" height="{height}" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>\n'
        f'  <text x="{chart_start_x + (chart_max_width / 2)}" y="22" fill="#8b949e" '
        f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
        f'font-size="11" text-anchor="middle">KB</text>\n'
        f'  <g fill="#c9d1d9" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="11">\n'
    )

    ticks = 10
    for i in range(1, ticks + 1):
        tick_val = (max_kb / ticks) * i
        tick_x = chart_start_x + (tick_val / max_kb) * chart_max_width
        svg += f'    <text x="{tick_x:.1f}" y="35" text-anchor="middle">{int(tick_val)}</text>\n'
        svg += f'    <line x1="{tick_x:.1f}" y1="38" x2="{tick_x:.1f}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'

    axis_end_x = chart_start_x + chart_max_width
    svg += f'    <line x1="{chart_start_x}" y1="43" x2="{axis_end_x}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg += f'    <line x1="{chart_start_x}" y1="43" x2="{chart_start_x}" y2="{height - 15}" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg += "  </g>\n\n  <g>\n"

    total_size = sum(size for _, size in sorted_langs)
    for idx, (lang, size) in enumerate(sorted_langs):
        y_pos = header_height + (idx * item_height)
        kb = size / 1024.0
        pct = (size / total_size) * 100.0 if total_size > 0 else 0.0
        bar_len = (kb / max_kb) * chart_max_width
        safe_label = escape(f"{lang} ({pct:.1f}%)")
        svg += (
            f'    <text x="{chart_start_x - 10}" y="{y_pos + 12}" fill="#c9d1d9" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
            f'font-size="12" text-anchor="end">{safe_label}</text>\n'
            f'    <rect x="{chart_start_x + 1}" y="{y_pos + 1}" width="{bar_len:.1f}" height="15" rx="1" fill="#f0883e"/>\n'
        )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    svg += (
        f'  <text x="30" y="{height - 5}" fill="#8b949e" '
        f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
        f'font-size="10">Last updated: {now_utc}</text>\n'
        f'  </g>\n</svg>\n'
    )

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)


def generate_activity_svg(weekly_activity, output_path):
    """Writes the 52-week vertical commit histogram SVG to output_path.

    Bar Scaling Equation: bar_height = (weekly_count / max_commits) * 120.0
    Plain-English Meaning: Normalizes each week's aggregate commit count against the peak
    weekly commit volume over the trailing 52 weeks to fit a 120-pixel vertical plot area.
    Variables & Bounds:
      - weekly_count (int, >= 0): Merged default-branch commits in week index i in [0, 51].
      - max_commits (int, >= 10): Peak weekly commit count (floored at 10 to prevent division by zero).
    Runtime Effect: Renders proportional green bars anchored along the y=172 baseline.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    width = 850
    height = 220
    max_commits = max(weekly_activity) if weekly_activity and max(weekly_activity) > 0 else 10

    svg = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <rect width="{width}" height="{height}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>\n'
        f'  <text x="30" y="32" fill="#f0f6fc" '
        f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
        f'font-size="14" font-weight="700">Organization Activity History (Last 52 Weeks)</text>\n'
        f'  <g fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="10">\n'
    )

    for i in range(4, -1, -1):
        y_val = int((max_commits / 4) * i)
        y_pos = 172 - (i * 30)
        svg += f'    <text x="30" y="{y_pos + 3}">{y_val}</text>\n'
        if i > 0:
            svg += f'    <line x1="60" y1="{y_pos}" x2="810" y2="{y_pos}" stroke="#21262d" stroke-width="1" stroke-dasharray="2 2"/>\n'
        else:
            svg += f'    <line x1="60" y1="{y_pos}" x2="810" y2="{y_pos}" stroke="#30363d" stroke-width="1.5"/>\n'

    svg += '  </g>\n  <g transform="translate(60, 0)">\n'
    bar_width = 10
    gap = 4
    for idx, count in enumerate(weekly_activity[:52]):
        x_pos = idx * (bar_width + gap)
        bar_h = (count / max_commits) * 120.0
        y_pos = 172.0 - bar_h
        if bar_h > 0:
            svg += f'    <rect x="{x_pos:.1f}" y="{y_pos:.1f}" width="{bar_width}" height="{bar_h:.1f}" fill="#39d353" rx="1"/>\n'

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    svg += (
        '  </g>\n'
        '  <g transform="translate(60, 192)" fill="#8b949e" '
        'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="10">\n'
        '    <text x="0">1 Year Ago</text>\n'
        '    <text x="375" text-anchor="middle">6 Months Ago</text>\n'
        '    <text x="750" text-anchor="end">Now</text>\n'
        '  </g>\n'
        f'  <text x="30" y="{height - 5}" fill="#8b949e" '
        f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
        f'font-size="10">Last updated: {now_utc}</text>\n'
        '</svg>\n'
    )

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(svg)
