"""
SVG Bar Generator - ALL BARS IDENTICAL SIZE

Creates uniform pill-shaped bars with internal patterns to show usage.
Every bar is exactly the same dimensions - only the internal fill pattern changes.
"""

from typing import Tuple


def generate_bar_svg(
    voorschot: float,
    gebruikt_or_totaal: float,
    is_overfilled: bool,
    label_gebruikt: str = "",
    label_extra_or_terug: str = "",
    width: int = 400,
    height: int = 40
) -> str:
    """
    Generate uniform SVG bar matching user's hand-drawn design.
    
    ALL BARS ARE IDENTICAL SIZE - only internal pattern differs:
    - Solid portion shows used/budget amount
    - Striped portion shows return (underuse) or extra charge (overuse)
    
    Args:
        voorschot: The prepaid/budget amount
        gebruikt_or_totaal: Amount used
        is_overfilled: True if usage exceeded budget
        label_gebruikt: Text for used portion
        label_extra_or_terug: Text for stripe portion
        width: FIXED width (all bars same)
        height: FIXED height (all bars same)
    
    Returns:
        SVG markup as string
    """
    
    border_radius = height / 2
    
    # Calculate what percentage of bar to fill solid vs striped
    if voorschot <= 0:
        voorschot = 1  # Prevent division by zero
    
    if is_overfilled:
        # OVERUSE: Budget portion is solid, excess is striped
        # Show ~70% solid (budget), ~30% stripe (extra charge)
        solid_pct = 70
        stripe_pct = 30
        stripe_color = "#BDBDBD"  # Grey for charges
        marker_x = (solid_pct / 100) * width
        show_marker = True
    else:
        # UNDERUSE: Used portion is solid, return portion is striped
        if gebruikt_or_totaal >= voorschot:
            # 100% usage
            solid_pct = 100
            stripe_pct = 0
        else:
            solid_pct = (gebruikt_or_totaal / voorschot) * 100
            stripe_pct = 100 - solid_pct
        
        stripe_color = "#81C784"  # Green for returns
        marker_x = 0
        show_marker = False
    
    # Ensure visibility
    if solid_pct > 0 and solid_pct < 5:
        solid_pct = 5
    if stripe_pct > 0 and stripe_pct < 5:
        stripe_pct = 5
    
    # Calculate pixel widths
    solid_width = (solid_pct / 100) * width
    stripe_x = solid_width
    stripe_width = width - solid_width
    
    # Build SVG
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <pattern id="stripes" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
            <rect width="4" height="8" fill="white" opacity="0.4"/>
        </pattern>
    </defs>
    
    <!-- Background rounded pill -->
    <rect x="0" y="0" width="{width}" height="{height}" rx="{border_radius}" fill="#F5F5F5" stroke="#E0E0E0" stroke-width="1"/>
    
    <!-- Solid portion (used/budget) -->
    <rect x="0" y="0" width="{solid_width}" height="{height}" rx="{border_radius}" fill="#FFE082"/>
    
    <!-- Striped portion (return/extra) -->
    {f'<rect x="{stripe_x}" y="0" width="{stripe_width}" height="{height}" rx="{border_radius}" fill="{stripe_color}"/>' if stripe_width > 5 else ''}
    {f'<rect x="{stripe_x}" y="0" width="{stripe_width}" height="{height}" rx="{border_radius}" fill="url(#stripes)"/>' if stripe_width > 5 else ''}
    
    <!-- Budget marker (dashed line) -->
    {f'<line x1="{marker_x}" y1="-5" x2="{marker_x}" y2="{height + 5}" stroke="#2C3E50" stroke-width="2" stroke-dasharray="4,4" opacity="0.4"/>' if show_marker else ''}
    
    <!-- Text labels -->
    {f'<text x="{solid_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#2C3E50" font-size="13" font-weight="600" font-family="Barlow, sans-serif">{label_gebruikt}</text>' if label_gebruikt and solid_width > 40 else ''}
    {f'<text x="{stripe_x + stripe_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#2C3E50" font-size="13" font-weight="600" font-family="Barlow, sans-serif">{label_extra_or_terug}</text>' if label_extra_or_terug and stripe_width > 40 else ''}
</svg>'''
    
    return svg


def generate_start_bar_svg(
    amount: float,
    label: str = "",
    width: int = 200,
    height: int = 40
) -> str:
    """
    Generate solid bar for START column.
    
    Args:
        amount: The prepaid amount
        label: Text label
        width: FIXED width
        height: FIXED height
    
    Returns:
        SVG markup as string
    """
    
    border_radius = height / 2
    
    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="{width}" height="{height}" rx="{border_radius}" fill="#A5D6A7" stroke="rgba(0,0,0,0.1)" stroke-width="1"/>
    <text x="{width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#1B5E20" font-size="15" font-weight="600" font-family="Barlow, sans-serif">{label}</text>
</svg>'''
    
    return svg


if __name__ == "__main__":
    print("=== All bars same width test ===")
    print("\n1. Underuse:")
    print(generate_bar_svg(800, 0, False, "€0", "€800", 400, 40))
    print("\n2. Normal:")
    print(generate_bar_svg(350, 90, False, "€90", "€260", 400, 40))
    print("\n3. Overuse:")
    print(generate_bar_svg(250, 325, True, "€250", "+€75", 400, 40))
