"""
SVG Bar Generator - POT-BASED VISUALIZATION

Creates pot-based bars where voorschot (pot) = fixed 400px baseline.
- Underuse: solid portion shows usage, stripe shows return (within 400px)
- Overflow: pot fills 400px + small fixed extension indicator (50px)
"""

from typing import Tuple


def generate_bar_svg(
    voorschot: float,
    gebruikt_or_totaal: float,
    is_overfilled: bool,
    label_gebruikt: str = "",
    label_extra_or_terug: str = "",
    pot_width: int = 400,
    height: int = 40
) -> str:
    """
    Generate pot-based SVG bar.
    
    POT-BASED RULES:
    - Pot (voorschot) = fixed 400px baseline (always)
    - Underuse: solid = (used/pot) * 400px, stripe fills rest to 400px
    - Overflow: solid fills 400px + small 50px extension with notch
    
    Args:
        voorschot: The prepaid/budget amount (THE POT)
        gebruikt_or_totaal: Amount used
        is_overfilled: True if usage exceeded budget
        label_gebruikt: Text for used portion
        label_extra_or_terug: Text for stripe portion
        pot_width: FIXED width representing the pot (400px)
        height: Bar height (40px)
    
    Returns:
        SVG markup as string
    """
    
    border_radius = height / 2
    extension_width = 50  # Fixed extension for overflow
    
    # Prevent division by zero
    if voorschot <= 0:
        voorschot = 1
    
    if is_overfilled:
        # OVERFLOW: Pot fills pot_width + small fixed extension
        total_width = pot_width + extension_width
        used_width = pot_width  # Usage fills entire base
        show_extension = True
        show_marker = True
        
        # Labels
        label_used = label_gebruikt if label_gebruikt else f"€{voorschot:.0f}"
        label_overflow_text = label_extra_or_terug if label_extra_or_terug else f"+€{gebruikt_or_totaal - voorschot:.0f}"
    else:
        # UNDERUSE or PERFECT FIT: Usage within pot
        total_width = pot_width
        used_width = (gebruikt_or_totaal / voorschot) * pot_width
        show_extension = False
        show_marker = False
        
        # Labels
        label_used = label_gebruikt if label_gebruikt else f"€{gebruikt_or_totaal:.0f}"
        label_return = label_extra_or_terug if label_extra_or_terug else f"€{voorschot - gebruikt_or_totaal:.0f}"
    
    # Ensure minimum visibility
    if used_width > 0 and used_width < 5:
        used_width = 5
    
    # Build SVG with unique pattern ID
    import random
    pattern_id = f"stripes_{random.randint(1000, 9999)}"
    
    svg_parts = [f'<svg width="{total_width}" height="{height}" viewBox="0 0 {total_width} {height}" xmlns="http://www.w3.org/2000/svg">']
    
    # Defs for stripe pattern
    svg_parts.append(f'''    <defs>
        <pattern id="{pattern_id}" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
            <rect width="4" height="8" fill="white" opacity="0.4"/>
        </pattern>
    </defs>''')
    
    # LAYER 1: Base bar - green background (represents full pot/return)
    svg_parts.append(f'    <rect x="0" y="0" width="{pot_width}" height="{height}" rx="{border_radius}" fill="#81C784" stroke="#E0E0E0" stroke-width="1"/>')
    
    # LAYER 2: Yellow overlay (used portion)
    svg_parts.append(f'    <rect x="0" y="0" width="{used_width}" height="{height}" rx="{border_radius}" fill="#FFE082"/>')
    
    if is_overfilled:
        # LAYER 3: Overflow extension (red striped)
        svg_parts.append(f'    <rect x="{pot_width}" y="0" width="{extension_width}" height="{height}" rx="{border_radius}" fill="#EF9A9A"/>')
        svg_parts.append(f'    <rect x="{pot_width}" y="0" width="{extension_width}" height="{height}" rx="{border_radius}" fill="url(#{pattern_id})"/>')
        
        # Pot boundary marker
        if show_marker:
            svg_parts.append(f'    <line x1="{pot_width}" y1="-5" x2="{pot_width}" y2="{height + 5}" stroke="#D32F2F" stroke-width="2" stroke-dasharray="4,4" opacity="0.6"/>')
        
        # Labels
        if used_width > 40:
            svg_parts.append(f'    <text x="{used_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#2C3E50" font-size="11" font-weight="600" font-family="Barlow, sans-serif">{label_used}</text>')
        if extension_width > 30:
            svg_parts.append(f'    <text x="{pot_width + extension_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#C62828" font-size="11" font-weight="600" font-family="Barlow, sans-serif">{label_overflow_text}</text>')
    else:
        # Labels for underuse/perfect fit
        return_width = pot_width - used_width
        if used_width > 40:
            svg_parts.append(f'    <text x="{used_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#2C3E50" font-size="11" font-weight="600" font-family="Barlow, sans-serif">{label_used}</text>')
        if return_width > 40:
            svg_parts.append(f'    <text x="{used_width + return_width/2}" y="{height/2 + 5}" text-anchor="middle" fill="#2C3E50" font-size="11" font-weight="600" font-family="Barlow, sans-serif">{label_return}</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def generate_start_bar_svg(
    amount: float,
    label: str = "",
    width: int = 280,
    height: int = 30
) -> str:
    """
    Generate solid bar for START column.

    Args:
        amount: The prepaid amount
        label: Text label
        width: FIXED width (matches VERBLIJF bar width)
        height: FIXED height (matches VERBLIJF bar height)

    Returns:
        SVG markup as string
    """

    border_radius = height / 2.0

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="{width}" height="{height}" rx="{border_radius}" fill="#A5D6A7" stroke="#E0E0E0" stroke-width="1"/>
    <text x="{width/2}" y="{height/2 + 4}" text-anchor="middle" fill="#2C3E50" font-size="11" font-weight="600" font-family="Barlow, sans-serif">{label}</text>
</svg>'''

    return svg


def generate_overflow_indicator_svg(
    amount: float,
    width: int = 80,
    height: int = 24
) -> str:
    """
    Generate small red overflow indicator badge.

    This appears next to the main bar when usage exceeds budget,
    showing the overflow amount in a compact red badge.

    Args:
        amount: The overflow amount (positive value)
        width: Badge width (default 80px)
        height: Badge height (default 24px)

    Returns:
        SVG markup as string
    """

    border_radius = height / 2.0

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="{width}" height="{height}" rx="{border_radius}" fill="#EF9A9A" stroke="#C62828" stroke-width="1.5"/>
    <text x="{width/2}" y="{height/2 + 4}" text-anchor="middle" fill="#C62828" font-size="10" font-weight="700" font-family="Barlow, sans-serif">+€{amount:.0f}</text>
</svg>'''

    return svg


def generate_caption(
    pot: float,
    used: float,
    refund: float = 0,
    overflow: float = 0
) -> str:
    """
    Generate human-readable caption for bar visualization.

    Args:
        pot: The voorschot (prepaid amount / pot)
        used: Amount used
        refund: Amount to be refunded (if underuse)
        overflow: Amount over budget (if overuse)

    Returns:
        Human-readable caption string
    """

    # Zero usage
    if used <= 0:
        return "Nog geen verbruik geregistreerd."

    # Perfect fit
    if abs(used - pot) < 0.01:  # Account for float precision
        return "Uw voorschot dekte uw volledige verbruik."

    # Overflow scenario
    if overflow > 0 or used > pot:
        actual_overflow = overflow if overflow > 0 else (used - pot)
        return f"Voorschot: €{pot:.0f} · Verbruik: €{used:.0f} · Extra te betalen: €{actual_overflow:.0f}"

    # Underuse scenario
    if refund > 0:
        return f"Voorschot: €{pot:.0f} · Verbruik: €{used:.0f} · Terug: €{refund:.0f}"

    # Fallback (shouldn't normally reach here)
    return f"Verbruik: €{used:.2f} van €{pot:.2f} voorschot."


if __name__ == "__main__":
    print("=== All bars same width test ===")
    print("\n1. Underuse:")
    print(generate_bar_svg(800, 0, False, "€0", "€800", 400, 40))
    print("\n2. Normal:")
    print(generate_bar_svg(350, 90, False, "€90", "€260", 400, 40))
    print("\n3. Overuse:")
    print(generate_bar_svg(250, 325, True, "€250", "+€75", 400, 40))
