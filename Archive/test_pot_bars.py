#!/usr/bin/env python3
"""
Quick test of pot-based bar visualization system
Tests the SVG generation with realistic data
"""

from svg_bars import generate_bar_svg, generate_start_bar_svg, generate_overflow_indicator_svg, generate_caption

def test_scenario_underuse():
    """Test underuse: Customer used less than prepaid"""
    print("\n=== SCENARIO 1: UNDERUSE ===")
    print("Borg: €500 prepaid, €150 used → €350 return")

    borg_start = generate_start_bar_svg(500, "€500", 280, 30)
    borg_usage = generate_bar_svg(500, 150, False, "€150", "€350", 280, 30)
    borg_caption = generate_caption(500, 150, 350, 0)

    print(f"\nStart Bar (280px):\n{borg_start}\n")
    print(f"Usage Bar (280px):\n{borg_usage}\n")
    print(f"Caption: {borg_caption}")

    # Save to HTML for visual inspection
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Barlow', sans-serif; padding: 40px; background: #f5f5f5; }}
        .test-row {{ margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
        .label {{ font-weight: 600; margin-bottom: 10px; }}
        .bar-wrapper {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Pot-Based Bar Visualization Test</h1>

    <div class="test-row">
        <div class="label">SCENARIO 1: UNDERUSE (€150 / €500)</div>
        <div class="bar-wrapper">{borg_start}</div>
        <div class="bar-wrapper">{borg_usage}</div>
        <div class="label">{borg_caption}</div>
    </div>
</body>
</html>"""

    with open("test_underuse.html", "w") as f:
        f.write(html)
    print("\n✓ Saved test_underuse.html")


def test_scenario_perfect():
    """Test perfect fit: Customer used exactly what was prepaid"""
    print("\n=== SCENARIO 2: PERFECT FIT ===")
    print("Borg: €500 prepaid, €500 used → €0 return")

    borg_start = generate_start_bar_svg(500, "€500", 280, 30)
    borg_usage = generate_bar_svg(500, 500, False, "€500", "€0", 280, 30)
    borg_caption = generate_caption(500, 500, 0, 0)

    print(f"Caption: {borg_caption}")


def test_scenario_overflow():
    """Test overflow: Customer exceeded prepaid amount"""
    print("\n=== SCENARIO 3: OVERFLOW ===")
    print("GWE: €300 prepaid, €485 used → €185 owed")

    gwe_start = generate_start_bar_svg(300, "€300", 280, 30)
    # For overflow, bar fills to pot (300), overflow shows separately
    gwe_usage = generate_bar_svg(300, 300, False, "€300", "", 280, 30)
    gwe_overflow = generate_overflow_indicator_svg(185, 80, 24)
    gwe_caption = generate_caption(300, 485, 0, 185)

    print(f"\nStart Bar (280px):\n{gwe_start}\n")
    print(f"Usage Bar (280px):\n{gwe_usage}\n")
    print(f"Overflow Badge (80×24px):\n{gwe_overflow}\n")
    print(f"Caption: {gwe_caption}")

    # Save to HTML for visual inspection
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Barlow', sans-serif; padding: 40px; background: #f5f5f5; }}
        .test-row {{ margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
        .label {{ font-weight: 600; margin-bottom: 10px; }}
        .bar-wrapper {{ margin: 10px 0; }}
        .unified-bar-container {{ display: flex; align-items: center; gap: 8px; }}
    </style>
</head>
<body>
    <h1>Pot-Based Bar Visualization Test - Overflow</h1>

    <div class="test-row">
        <div class="label">SCENARIO 3: OVERFLOW (€485 / €300)</div>
        <div class="label">Start:</div>
        <div class="bar-wrapper">{gwe_start}</div>
        <div class="label">Usage (with overflow indicator):</div>
        <div class="unified-bar-container">
            <div class="bar-wrapper">{gwe_usage}</div>
            <div class="overflow-wrapper">{gwe_overflow}</div>
        </div>
        <div class="label">{gwe_caption}</div>
    </div>
</body>
</html>"""

    with open("test_overflow.html", "w") as f:
        f.write(html)
    print("\n✓ Saved test_overflow.html")


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 POT-BASED BAR VISUALIZATION TESTS")
    print("=" * 70)

    test_scenario_underuse()
    test_scenario_perfect()
    test_scenario_overflow()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70)
    print("\n📂 Generated test files:")
    print("   • test_underuse.html - Underuse scenario visualization")
    print("   • test_overflow.html - Overflow scenario visualization")
    print("\n💡 Open these files in your browser to verify the visualization!")
