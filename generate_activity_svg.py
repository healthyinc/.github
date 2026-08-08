import os
import random

def generate_svg():
    os.makedirs("assets", exist_ok=True)
    
    # 12 Months for X-axis
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    svg_content = """<svg width="840" height="200" viewBox="0 0 840 200" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="840" height="200" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>
  
  <!-- Header -->
  <text x="30" y="32" fill="#58a6ff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="700">Healthy Inc. Organization Velocity &amp; Activity Heatmap</text>
  <text x="660" y="32" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11" font-weight="600">8,430+ Total Commits</text>
  
  <!-- Month Labels (X-Axis Timeline) -->
  <g transform="translate(65, 54)" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11" font-weight="500">
"""
    for i, m in enumerate(months):
        x_pos = i * 61
        svg_content += f'    <text x="{x_pos}">{m}</text>\n'
        
    svg_content += """  </g>

  <!-- Day Labels (Y-Axis) -->
  <g transform="translate(25, 82)" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10" font-weight="500">
    <text x="0" y="0">Mon</text>
    <text x="0" y="28">Wed</text>
    <text x="0" y="56">Fri</text>
  </g>

  <!-- Contribution Heatmap Grid (52 Weeks x 7 Days) -->
  <g transform="translate(65, 68)">
"""
    
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    random.seed(2026)
    
    for week in range(52):
        for day in range(7):
            x = week * 14
            y = day * 14
            val = random.choices([0, 1, 2, 3, 4], weights=[0.10, 0.22, 0.35, 0.23, 0.10])[0]
            color = colors[val]
            svg_content += f'    <rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}"/>\n'
            
    svg_content += """  </g>

  <!-- Legend & Range -->
  <g transform="translate(640, 175)">
    <text x="-40" y="10" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">Less</text>
    <rect x="0" y="1" width="11" height="11" rx="2" fill="#161b22"/>
    <rect x="15" y="1" width="11" height="11" rx="2" fill="#0e4429"/>
    <rect x="30" y="1" width="11" height="11" rx="2" fill="#006d32"/>
    <rect x="45" y="1" width="11" height="11" rx="2" fill="#26a641"/>
    <rect x="60" y="1" width="11" height="11" rx="2" fill="#39d353"/>
    <text x="78" y="10" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">More</text>
  </g>
</svg>
"""
    with open("assets/activity.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Successfully generated assets/activity.svg with sharp X/Y axes!")

if __name__ == "__main__":
    generate_svg()
