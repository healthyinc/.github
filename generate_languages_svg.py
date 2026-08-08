import os

def generate_languages_svg():
    os.makedirs("assets", exist_ok=True)
    
    # Data matching Healthy Inc languages & code volume
    lang_data = [
        ("TypeScript", 30.0, 1850),
        ("Python", 24.0, 1480),
        ("Solidity / EVM", 12.0, 740),
        ("JavaScript", 10.0, 615),
        ("Rust / Anchor", 8.0, 490),
        ("Kotlin", 5.0, 310),
        ("Swift", 4.0, 245),
        ("Shell", 3.0, 185),
        ("Docker", 2.0, 125),
        ("HTML", 1.0, 60),
        ("CSS", 1.0, 60),
        ("Markdown", 1.0, 60)
    ]
    
    width = 850
    item_height = 24
    header_height = 45 # Shifted up since title text is removed from SVG internal
    footer_height = 20
    height = header_height + (len(lang_data) * item_height) + footer_height
    
    # X-axis scale (0 to 2000 KB across ~580 pixels)
    chart_start_x = 220
    chart_max_width = 580
    max_kb = 2000.0
    
    svg_content = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>
  
  <!-- Sub-label KB -->
  <text x="{chart_start_x + (chart_max_width / 2)}" y="22" fill="#8b949e" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11" text-anchor="middle">KB</text>
  
  <!-- Top X-Axis Tick Marks & Axis Line (200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000) -->
  <g fill="#c9d1d9" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11">
"""
    
    # Tick marks
    ticks = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]
    for t in ticks:
        tx = chart_start_x + (t / max_kb) * chart_max_width
        svg_content += f'    <text x="{tx:.1f}" y="35" text-anchor="middle">{t}</text>\n'
        svg_content += f'    <line x1="{tx:.1f}" y1="38" x2="{tx:.1f}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'
        
    axis_start_x = chart_start_x
    axis_end_x = chart_start_x + chart_max_width
    svg_content += f'    <line x1="{axis_start_x}" y1="43" x2="{axis_end_x}" y2="43" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg_content += f'    <line x1="{chart_start_x}" y1="43" x2="{chart_start_x}" y2="{height - 15}" stroke="#f0f6fc" stroke-width="1.5"/>\n'
    svg_content += "  </g>\n\n"
    
    # Horizontal Bars (Solid Orange Theme matching KathiraveluLab: #f0883e)
    orange_color = "#f0883e"
    
    svg_content += "  <!-- Language Bars -->\n  <g>\n"
    for i, (lang, pct, kb) in enumerate(lang_data):
        y_pos = header_height + (i * item_height)
        bar_len = (kb / max_kb) * chart_max_width
        label_str = f"{lang} ({pct:.1f}%)"
        
        svg_content += f'    <text x="{chart_start_x - 10}" y="{y_pos + 12}" fill="#c9d1d9" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" font-size="12" text-anchor="end">{label_str}</text>\n'
        svg_content += f'    <rect x="{chart_start_x + 1}" y="{y_pos + 1}" width="{bar_len:.1f}" height="15" rx="1" fill="{orange_color}"/>\n'
        
    svg_content += "  </g>\n</svg>\n"
    
    with open("assets/languages.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Successfully updated assets/languages.svg without internal duplicate title!")

if __name__ == "__main__":
    generate_languages_svg()
