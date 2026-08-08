import os
import random

def generate_svg():
    os.makedirs("assets", exist_ok=True)
    
    # Generate heatmap grid with X-axis months and Y-axis days
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    days = ["Mon", "Wed", "Fri"]
    
    svg_content = """<svg width="850" height="190" viewBox="0 0 850 190" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="850" height="190" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  
  <!-- Title & Total Metric -->
  <text x="30" y="32" fill="#f0f6fc" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="600">Healthy Inc. Organization Velocity &amp; Contribution Heatmap</text>
  <text x="680" y="32" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11">8,430+ Total Commits (Past 12 Months)</text>
  
  <!-- Month Labels (X-Axis: Time in Months) -->
  <g transform="translate(60, 50)" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">
"""
    for i, m in enumerate(months):
        x_pos = i * 58
        svg_content += f'    <text x="{x_pos}">{m}</text>\n'
        
    svg_content += """  </g>

  <!-- Day Labels (Y-Axis: Days of Week) -->
  <g transform="translate(25, 78)" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">
    <text x="0" y="0">Mon</text>
    <text x="0" y="26">Wed</text>
    <text x="0" y="52">Fri</text>
  </g>

  <!-- Heatmap Grid (52 Weeks x 7 Days) -->
  <g transform="translate(60, 62)">
"""
    
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    random.seed(101)
    
    for week in range(52):
        for day in range(7):
            x = week * 13.5
            y = day * 13
            # Simulate active engineering activity
            val = random.choices([0, 1, 2, 3, 4], weights=[0.12, 0.25, 0.33, 0.20, 0.10])[0]
            color = colors[val]
            svg_content += f'    <rect x="{x:.1f}" y="{y}" width="10.5" height="10.5" rx="2" fill="{color}"/>\n'
            
    svg_content += """  </g>

  <!-- Legend -->
  <g transform="translate(650, 162)">
    <text x="-35" y="10" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10">Less</text>
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
    print("Successfully regenerated assets/activity.svg with labeled X and Y axes!")

if __name__ == "__main__":
    generate_svg()
