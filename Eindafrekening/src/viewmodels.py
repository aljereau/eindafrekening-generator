#!/usr/bin/env python3
"""
ViewModels - Transform entity data to OnePager and Detail output formats

Transforms raw entity data into the specific JSON structures needed for:
- OnePager template (simplified one-page view)
- Detail template (comprehensive breakdown with all line items)

Output matches onepager.json and detail.json schemas.
"""

from typing import Dict, Any, List
from datetime import date, datetime
from entities import (
    Client, RentalProperty, Period, Deposit, GWEMeterReading, GWERegel,
    GWETotalen, Cleaning, DamageRegel, DamageTotalen, Settlement,
    GWEMeterstanden
)
from calculator import Calculator
from svg_bars import generate_bar_svg, generate_start_bar_svg, generate_caption, generate_overflow_indicator_svg


def date_to_str(d: date) -> str:
    """Convert date to string format DD-MM-YYYY (Dutch format)"""
    return d.strftime('%d-%m-%Y') if d else ""


def build_onepager_viewmodel(data: Dict[str, Any], settlement: Settlement) -> Dict[str, Any]:
    """
    Build OnePager view model for simplified one-page template
    
    Args:
        data: Raw entity data from excel_reader
        settlement: Calculated settlement entity
        
    Returns:
        Dictionary matching onepager.json schema
    """
    client: Client = data['client']
    obj: RentalProperty = data['object']
    period: Period = data['period']
    gwe_totalen: GWETotalen = data['gwe_totalen']
    gwe_meterstanden: GWEMeterstanden = data['gwe_meterstanden']
    cleaning: Cleaning = data['cleaning']
    damage_totalen: DamageTotalen = data['damage_totalen']
    damage_regels: List[DamageRegel] = data.get('damage_regels', [])
    extra_voorschot = data.get('extra_voorschot')  # Optional extra advance payment
    
    # Get voorschotten from various sources
    gwe_voorschot = data.get('gwe_voorschot', 0.0)  # Should be passed in
    
    # Calculate GWE meer/minder and derived values
    gwe_meer_minder = Calculator.calculate_gwe_meer_minder(gwe_voorschot, gwe_totalen.totaal_incl)
    gwe_is_overfilled = gwe_meer_minder < 0
    gwe_extra = abs(gwe_meer_minder) if gwe_is_overfilled else 0
    gwe_terug = gwe_meer_minder if not gwe_is_overfilled else 0
    
    # Calculate cleaning derived values
    clean_is_overfilled = cleaning.extra_bedrag > 0
    clean_terug = 0 if clean_is_overfilled else (cleaning.voorschot - cleaning.extra_bedrag)
    
    return {
        "client": {
            "name": client.name,
            "contact_person": client.contact_person,
            "email": client.email,
            "phone": client.phone or ""
        },
        "object": {
            "address": obj.address,
            "unit": obj.unit or "",
            "postal_code": obj.postal_code or "",
            "city": obj.city or "",
            "object_id": obj.object_id or ""
        },
        "period": {
            "checkin_date": date_to_str(period.checkin_date),
            "checkout_date": date_to_str(period.checkout_date),
            "days": period.days
        },
        "financial": {
            "borg": {
                "voorschot": settlement.borg.voorschot,
                "gebruikt": settlement.borg.gebruikt,
                "terug": settlement.borg.terug,
                "restschade": settlement.borg.restschade
            },
            "gwe": {
                "voorschot": gwe_voorschot,
                "totaal_incl": gwe_totalen.totaal_incl,
                "meer_minder": gwe_meer_minder,
                "is_overfilled": gwe_is_overfilled,
                "extra": gwe_extra,
                "extra": gwe_extra,
                "terug": gwe_terug,
                "meterstanden": {
                    "stroom": {
                        "begin": gwe_meterstanden.stroom.begin,
                        "eind": gwe_meterstanden.stroom.eind,
                        "verbruik": gwe_meterstanden.stroom.verbruik
                    },
                    "gas": {
                        "begin": gwe_meterstanden.gas.begin,
                        "eind": gwe_meterstanden.gas.eind,
                        "verbruik": gwe_meterstanden.gas.verbruik
                    },
                    "water": {
                        "begin": gwe_meterstanden.water.begin,
                        "eind": gwe_meterstanden.water.eind,
                        "verbruik": gwe_meterstanden.water.verbruik
                    } if gwe_meterstanden.water else None
                }
            },
            "cleaning": {
                "pakket_type": cleaning.pakket_type,
                "pakket_naam": cleaning.pakket_naam,
                "inbegrepen_uren": cleaning.inbegrepen_uren,
                "totaal_uren": cleaning.totaal_uren,
                "voorschot": cleaning.voorschot,
                "extra_uren": cleaning.extra_uren,
                "extra_bedrag": cleaning.extra_bedrag,
                "is_overfilled": clean_is_overfilled,
                "terug": clean_terug
            },
            "damage": {
                "totaal_incl": damage_totalen.totaal_incl
            },
            "extra_voorschot": {
                "voorschot": extra_voorschot.voorschot if extra_voorschot else 0.0,
                "gebruikt": extra_voorschot.gebruikt if extra_voorschot else 0.0,
                "terug": extra_voorschot.terug if extra_voorschot else 0.0,
                "restschade": extra_voorschot.restschade if extra_voorschot else 0.0,
                "omschrijving": extra_voorschot.omschrijving if extra_voorschot else "",
                "has_voorschot": extra_voorschot is not None
            } if extra_voorschot else None,
            "totals": {
                "totaal_eindafrekening": settlement.totaal_eindafrekening,
                "totaal_eindafrekening_is_positive": settlement.totaal_eindafrekening >= 0
            }
        },
        "damage_details": [
            {"omschrijving": regel.beschrijving, "bedrag": regel.bedrag_excl}
            for regel in damage_regels
        ],
        "generated_date": datetime.now().strftime('%d-%m-%Y %H:%M'),
        "logo_b64": data.get('logo_b64', None)
    }


def build_detail_viewmodel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build Detail view model for comprehensive detail template
    
    Args:
        data: Raw entity data from excel_reader
        
    Returns:
        Dictionary matching detail.json schema
    """
    client: Client = data['client']
    obj: RentalProperty = data['object']
    period: Period = data['period']
    gwe_meterstanden: GWEMeterstanden = data['gwe_meterstanden']
    gwe_regels: List[GWERegel] = data['gwe_regels']
    gwe_totalen: GWETotalen = data['gwe_totalen']
    cleaning: Cleaning = data['cleaning']
    damage_regels: List[DamageRegel] = data['damage_regels']
    damage_totalen: DamageTotalen = data['damage_totalen']
    deposit: Deposit = data['deposit']
    
    # Build full object address for detail view
    object_address = obj.address
    if obj.unit:
        object_address += f", {obj.unit}"
    if obj.postal_code and obj.city:
        object_address += f", {obj.postal_code} {obj.city}"
    
    return {
        "client": {
            "name": client.name,
            "object_address": object_address,
            "period": {
                "checkin_date": date_to_str(period.checkin_date),
                "checkout_date": date_to_str(period.checkout_date)
            }
        },
        "gwe": {
            "meterstanden": {
                "stroom": {
                    "begin": gwe_meterstanden.stroom.begin,
                    "eind": gwe_meterstanden.stroom.eind,
                    "verbruik": gwe_meterstanden.stroom.verbruik
                },
                "gas": {
                    "begin": gwe_meterstanden.gas.begin,
                    "eind": gwe_meterstanden.gas.eind,
                    "verbruik": gwe_meterstanden.gas.verbruik
                },
                "water": {
                    "begin": gwe_meterstanden.water.begin,
                    "eind": gwe_meterstanden.water.eind,
                    "verbruik": gwe_meterstanden.water.verbruik
                } if gwe_meterstanden.water else None
            },
            "kostenregels": [
                {
                    "omschrijving": regel.omschrijving,
                    "verbruik_of_dagen": regel.verbruik_of_dagen,
                    "tarief_excl": regel.tarief_excl,
                    "kosten_excl": regel.kosten_excl
                }
                for regel in gwe_regels
            ],
            "totalen": {
                "totaal_excl": gwe_totalen.totaal_excl,
                "btw": gwe_totalen.btw,
                "totaal_incl": gwe_totalen.totaal_incl
            }
        },
        "cleaning": {
            "pakket_type": cleaning.pakket_type,
            "pakket_naam": cleaning.pakket_naam,
            "inbegrepen_uren": cleaning.inbegrepen_uren,
            "totaal_uren": cleaning.totaal_uren,
            "extra_uren": cleaning.extra_uren,
            "uurtarief": cleaning.uurtarief,
            "extra_bedrag": cleaning.extra_bedrag,
            "voorschot": cleaning.voorschot
        },
        "damage": {
            "regels": [
                {
                    "beschrijving": regel.beschrijving,
                    "aantal": regel.aantal,
                    "tarief_excl": regel.tarief_excl,
                    "bedrag_excl": regel.bedrag_excl
                }
                for regel in damage_regels
            ],
            "totalen": {
                "totaal_excl": damage_totalen.totaal_excl,
                "btw": damage_totalen.btw,
                "totaal_incl": damage_totalen.totaal_incl
            }
        },
        "borg": {
            "voorschot": deposit.voorschot,
            "gebruikt": deposit.gebruikt,
            "terug": deposit.terug,
            "restschade": deposit.restschade
        },
        "extra_voorschot": {
            "voorschot": data.get('extra_voorschot').voorschot if data.get('extra_voorschot') else 0.0,
            "gebruikt": data.get('extra_voorschot').gebruikt if data.get('extra_voorschot') else 0.0,
            "terug": data.get('extra_voorschot').terug if data.get('extra_voorschot') else 0.0,
            "restschade": data.get('extra_voorschot').restschade if data.get('extra_voorschot') else 0.0,
            "omschrijving": data.get('extra_voorschot').omschrijving if data.get('extra_voorschot') else "",
            "has_voorschot": data.get('extra_voorschot') is not None
        } if data.get('extra_voorschot') else None
    }


def add_bar_chart_data(onepager_vm: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add bar chart percentage data and SVG markup for visual rendering
    
    Adds calculated percentages and SVG bars for:
    - Borg bars (used/return)
    - GWE bars (used/extra)
    - Cleaning bars
    
    Args:
        onepager_vm: OnePager viewmodel dictionary
        
    Returns:
        Enhanced viewmodel with bar chart data and SVG markup
    """
    financial = onepager_vm['financial']
    
    # BORG - Bar percentages and SVG
    borg = financial['borg']
    borg_bars = Calculator.calculate_bar_percentages(
        gebruikt=borg['gebruikt'],
        voorschot=borg['voorschot']
    )
    financial['borg']['bars'] = borg_bars
    financial['borg']['is_overfilled'] = False  # Borg never overfills (restschade handled separately)

    # Generate START bar SVG (solid prepaid amount)
    borg_start_svg = generate_start_bar_svg(
        amount=borg['voorschot'],
        label=f"€{borg['voorschot']:.0f}",
        width=280,
        height=30
    )
    financial['borg']['svg_start_bar'] = borg_start_svg

    # Generate Borg bar SVG (matches GWE style)
    # Usage bar is always 280px, showing only the capped usage (no overflow extension)
    # Overflow is a separate SVG in the extra-section
    is_overfilled = borg['restschade'] > 0
    
    # Usage bar - always 280px, never shows overflow extension
    borg_svg = generate_bar_svg(
        voorschot=borg['voorschot'],
        gebruikt_or_totaal=min(borg['voorschot'], borg['gebruikt']),
        is_overfilled=False,  # Always False so the bar stays 280px
        label_gebruikt=f"€{min(borg['voorschot'], borg['gebruikt']):.0f}",
        label_extra_or_terug=f"€{borg['terug']:.0f}",
        pot_width=280,
        height=30,
        show_limit_line=is_overfilled,  # Show red dashed line if overfilled
        rounded_right=not is_overfilled  # Sharp right edge if overfilled, to match overflow bar
    )
    financial['borg']['svg_bar'] = borg_svg
    financial['borg']['is_overfilled'] = is_overfilled

    # Generate separate overflow SVG if needed (goes in extra-section)
    if is_overfilled:
        overflow_svg = generate_overflow_indicator_svg(
            amount=borg['restschade'],
            height=30,
            rounded_left=False  # Sharp left edge to match GWE style
        )
        financial['borg']['overflow_svg'] = overflow_svg

    # Generate human-readable caption
    # Format matches GWE but with "Extra schade" instead of "Extra te betalen"
    if is_overfilled:
        borg_caption = f"Voorschot: €{borg['voorschot']:.0f} · Verbruik: €{borg['gebruikt']:.0f} · Extra schade: €{borg['restschade']:.0f}"
    else:
        borg_caption = f"Voorschot: €{borg['voorschot']:.0f} · Verbruik: €{borg['gebruikt']:.0f} · Terug: €{borg['terug']:.0f}"
    
    financial['borg']['caption'] = borg_caption
    
    # GWE - Bar percentages and SVG
    gwe = financial['gwe']
    gwe_gebruikt = gwe['totaal_incl']
    gwe_bars = Calculator.calculate_bar_percentages(
        gebruikt=gwe_gebruikt,
        voorschot=gwe['voorschot']
    )
    financial['gwe']['bars'] = gwe_bars

    # Generate START bar SVG
    gwe_start_svg = generate_start_bar_svg(
        amount=gwe['voorschot'],
        label=f"€{gwe['voorschot']:.0f}",
        width=280,
        height=30
    )
    financial['gwe']['svg_start_bar'] = gwe_start_svg

    # Generate VERBLIJF bar SVG (always matches START width)
    if gwe['is_overfilled']:
        # Overuse scenario - bar fills pot, overflow shows separately
        gwe_svg = generate_bar_svg(
            voorschot=gwe['voorschot'],
            gebruikt_or_totaal=gwe['voorschot'],  # Show full bar
            is_overfilled=False,  # Bar itself doesn't overflow
            label_gebruikt=f"€{gwe['voorschot']:.0f}",
            label_extra_or_terug="",
            pot_width=280,
            height=30,
            show_limit_line=True,
            rounded_right=False
        )
        # Generate overflow indicator
        gwe_overflow_svg = generate_overflow_indicator_svg(
            amount=gwe['extra'],
            width=80,
            height=30,
            rounded_left=False
        )
        financial['gwe']['overflow_svg'] = gwe_overflow_svg
    else:
        # Underuse scenario
        gwe_svg = generate_bar_svg(
            voorschot=gwe['voorschot'],
            gebruikt_or_totaal=gwe['totaal_incl'],
            is_overfilled=False,
            label_gebruikt=f"€{gwe['totaal_incl']:.0f}",
            label_extra_or_terug=f"€{gwe['terug']:.0f}",
            pot_width=280,
            height=30
        )
        financial['gwe']['overflow_svg'] = ""  # No overflow
    financial['gwe']['svg_bar'] = gwe_svg

    # Generate human-readable caption
    if gwe['is_overfilled']:
        gwe_caption = generate_caption(
            pot=gwe['voorschot'],
            used=gwe['totaal_incl'],
            refund=0,
            overflow=gwe['extra']
        )
    else:
        gwe_caption = generate_caption(
            pot=gwe['voorschot'],
            used=gwe['totaal_incl'],
            refund=gwe['terug'],
            overflow=0
        )
    financial['gwe']['caption'] = gwe_caption
    
    # CLEANING - Bar percentages and SVG
    # NOTE: Cleaning packages are ALWAYS fully used (never refunded)
    # The bar always shows the full package amount (yellow)
    # Extra hours appear as overflow indicator
    cleaning = financial['cleaning']

    # Cleaning is always 100% used (the package is consumed)
    financial['cleaning']['bars'] = {
        'gebruikt_pct': 100.0,
        'terug_pct': 0.0,
        'extra_pct': 0.0 if (cleaning['extra_bedrag'] == 0 or cleaning['voorschot'] == 0) else (cleaning['extra_bedrag'] / cleaning['voorschot']) * 100,
        'is_overfilled': cleaning['extra_bedrag'] > 0
    }

    # Generate START bar SVG
    if cleaning['pakket_naam'] == "Achteraf Betaald":
        cleaning_start_svg = generate_start_bar_svg(
            amount=0,
            label="Geen voorschot",
            width=280,
            height=30
        )
    else:
        cleaning_start_svg = generate_start_bar_svg(
            amount=cleaning['voorschot'],
            label=f"€{cleaning['voorschot']:.0f}",
            width=280,
            height=30
        )
    financial['cleaning']['svg_start_bar'] = cleaning_start_svg

    # Generate VERBLIJF bar SVG
    if cleaning['pakket_naam'] == "Achteraf Betaald":
        # Post-paid: Show total cost as usage (yellow), no overflow
        cleaning_svg = generate_bar_svg(
            voorschot=cleaning['extra_bedrag'], # Use total cost as "pot" size for visualization
            gebruikt_or_totaal=cleaning['extra_bedrag'],
            is_overfilled=False,
            label_gebruikt=f"€{cleaning['extra_bedrag']:.0f}",
            label_extra_or_terug="",
            pot_width=280,
            height=30,
            show_limit_line=False,
            rounded_right=True
        )
        financial['cleaning']['svg_bar'] = cleaning_svg
        financial['cleaning']['overflow_svg'] = "" # No overflow
        cleaning_caption = f"Schoonmaak kosten: €{cleaning['extra_bedrag']:.0f}"
    else:
        # Pre-paid: Always shows full package as used (yellow)
        cleaning_svg = generate_bar_svg(
            voorschot=cleaning['voorschot'],
            gebruikt_or_totaal=cleaning['voorschot'],  # Always full package
            is_overfilled=False,  # Bar itself doesn't overflow (shows full yellow)
            label_gebruikt=f"€{cleaning['voorschot']:.0f}",
            label_extra_or_terug="",  # No return label for cleaning
            pot_width=280,
            height=30,
            show_limit_line=True if cleaning['extra_bedrag'] > 0 else False,
            rounded_right=False if cleaning['extra_bedrag'] > 0 else True
        )
        financial['cleaning']['svg_bar'] = cleaning_svg

        # Generate overflow indicator if extra hours were needed
        if cleaning['extra_bedrag'] > 0:
            cleaning_overflow_svg = generate_overflow_indicator_svg(
                amount=cleaning['extra_bedrag'],
                width=80,
                height=30,
                rounded_left=False
            )
            financial['cleaning']['overflow_svg'] = cleaning_overflow_svg
            # Caption showing extra hours cost
            cleaning_caption = f"Pakket: €{cleaning['voorschot']:.0f} · Extra uren: €{cleaning['extra_bedrag']:.0f}"
        else:
            financial['cleaning']['overflow_svg'] = ""  # No overflow
            # Caption showing package was sufficient
            cleaning_caption = f"Pakket: €{cleaning['voorschot']:.0f} · Geen extra uren"

    financial['cleaning']['caption'] = cleaning_caption
    
    # EXTRA VOORSCHOT - Bar percentages and SVG (if exists)
    if financial.get('extra_voorschot') and financial['extra_voorschot']:
        extra_v = financial['extra_voorschot']
        extra_v_bars = Calculator.calculate_bar_percentages(
            gebruikt=extra_v['gebruikt'],
            voorschot=extra_v['voorschot']
        )
        financial['extra_voorschot']['bars'] = extra_v_bars
        
        # Generate START bar SVG
        extra_v_start_svg = generate_start_bar_svg(
            amount=extra_v['voorschot'],
            label=f"€{extra_v['voorschot']:.0f}",
            width=280,
            height=30
        )
        financial['extra_voorschot']['svg_start_bar'] = extra_v_start_svg
        
        # Generate VERBLIJF bar SVG
        if extra_v_bars['is_overfilled']:
            # Overfilled - show 100% used + overflow
            extra_v_svg = generate_bar_svg(
                voorschot=extra_v['voorschot'],
                gebruikt_or_totaal=extra_v['voorschot'],  # Cap at 100%
                is_overfilled=True,
                label_gebruikt=f"€{extra_v['voorschot']:.0f}",
                label_extra_or_terug="",
                pot_width=280,
                height=30,
                show_limit_line=True,
                rounded_right=False  # Sharp edge for overflow
            )
            # Generate overflow indicator
            extra_v_overflow_svg = generate_overflow_indicator_svg(
                amount=extra_v['restschade'],
                width=80,
                height=30,
                rounded_left=False
            )
            financial['extra_voorschot']['overflow_svg'] = extra_v_overflow_svg
        else:
            # Underfilled - show used + return
            extra_v_svg = generate_bar_svg(
                voorschot=extra_v['voorschot'],
                gebruikt_or_totaal=extra_v['gebruikt'],
                is_overfilled=False,
                label_gebruikt=f"€{extra_v['gebruikt']:.0f}",
                label_extra_or_terug=f"€{extra_v['terug']:.0f}",
                pot_width=280,
                height=30
            )
            financial['extra_voorschot']['overflow_svg'] = ""  # No overflow
        financial['extra_voorschot']['svg_bar'] = extra_v_svg
        
        # Generate caption
        if extra_v_bars['is_overfilled']:
            extra_v_caption = generate_caption(
                pot=extra_v['voorschot'],
                used=extra_v['gebruikt'],
                refund=0,
                overflow=extra_v['restschade']
            )
        else:
            extra_v_caption = generate_caption(
                pot=extra_v['voorschot'],
                used=extra_v['gebruikt'],
                refund=extra_v['terug'],
                overflow=0
            )
        financial['extra_voorschot']['caption'] = extra_v_caption
    
    return onepager_vm


def build_viewmodels_from_data(data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Build both OnePager and Detail viewmodels from raw entity data
    
    This is the main function to call - it handles all transformations.
    
    Args:
        data: Raw entity data from excel_reader (with calculations applied)
        
    Returns:
        Tuple of (onepager_viewmodel, detail_viewmodel)
    """
    # Need to get gwe_voorschot from somewhere - let's look for it in data
    # or calculate it from named range if available
    gwe_voorschot = data.get('gwe_voorschot', 0.0)
    
    # Calculate settlement
    calc = Calculator()
    settlement = calc.calculate_settlement(
        borg=data['deposit'],
        gwe_voorschot=gwe_voorschot,
        gwe_totalen=data['gwe_totalen'],
        cleaning=data['cleaning'],
        damage_totalen=data['damage_totalen'],
        extra_voorschot=data.get('extra_voorschot')
    )
    
    # Build OnePager viewmodel
    onepager_vm = build_onepager_viewmodel(data, settlement)
    
    # Add bar chart data for visual rendering
    onepager_vm = add_bar_chart_data(onepager_vm)
    
    # Build Detail viewmodel
    detail_vm = build_detail_viewmodel(data)
    
    return onepager_vm, detail_vm


# ==================== JSON SERIALIZATION ====================

def save_viewmodels_to_json(onepager_vm: Dict[str, Any], detail_vm: Dict[str, Any],
                            onepager_path: str = "output/onepager.json",
                            detail_path: str = "output/detail.json"):
    """
    Save viewmodels to JSON files
    
    Args:
        onepager_vm: OnePager viewmodel
        detail_vm: Detail viewmodel
        onepager_path: Output path for onepager JSON
        detail_path: Output path for detail JSON
    """
    import json
    import os
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(onepager_path), exist_ok=True)
    os.makedirs(os.path.dirname(detail_path), exist_ok=True)
    
    # Save onepager
    with open(onepager_path, 'w', encoding='utf-8') as f:
        json.dump(onepager_vm, f, indent=2, ensure_ascii=False)
    
    # Save detail
    with open(detail_path, 'w', encoding='utf-8') as f:
        json.dump(detail_vm, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Saved viewmodels:")
    print(f"   OnePager: {onepager_path}")
    print(f"   Detail: {detail_path}")


if __name__ == "__main__":
    """Test viewmodels with mock data"""
    from datetime import date
    
    print("📊 Testing ViewModels")
    print("=" * 60)
    
    # Create mock data
    mock_data = {
        'client': Client(
            name="Fam. Jansen",
            contact_person="Jan Jansen",
            email="jan@example.com",
            phone="06-12345678"
        ),
        'object': RentalProperty(
            address="Strandweg 42",
            unit="A3",
            postal_code="1234AB",
            city="Zandvoort",
            object_id="OBJ-001"
        ),
        'period': Period(
            checkin_date=date(2024, 8, 1),
            checkout_date=date(2024, 8, 13),
            days=12
        ),
        'deposit': Deposit(
            voorschot=800,
            gebruikt=600,
            terug=200,
            restschade=0
        ),
        'gwe_meterstanden': GWEMeterstanden(
            stroom=GWEMeterReading(begin=10000, eind=10500, verbruik=500),
            gas=GWEMeterReading(begin=5000, eind=5100, verbruik=100)
        ),
        'gwe_regels': [
            GWERegel("Elektra verbruik", 500, 0.28, 140),
            GWERegel("Gas verbruik", 100, 1.15, 115)
        ],
        'gwe_totalen': GWETotalen(totaal_excl=255, btw=53.55, totaal_incl=308.55),
        'gwe_voorschot': 350,
        'cleaning': Cleaning(
            pakket_type="5_uur",
            inbegrepen_uren=5,
            totaal_uren=7.5,
            extra_uren=2.5,
            uurtarief=50,
            extra_bedrag=125,
            voorschot=250
        ),
        'damage_regels': [
            DamageRegel("Reparatie deur", 1, 30, 30),
            DamageRegel("Vervangen lamp", 2, 15, 30)
        ],
        'damage_totalen': DamageTotalen(totaal_excl=60, btw=12.6, totaal_incl=72.6)
    }
    
    # Build viewmodels
    onepager, detail = build_viewmodels_from_data(mock_data)
    
    print("\n✅ OnePager viewmodel:")
    print(f"   Client: {onepager['client']['name']}")
    print(f"   Period: {onepager['period']['days']} days")
    print(f"   Borg terug: €{onepager['financial']['borg']['terug']}")
    print(f"   GWE meer/minder: €{onepager['financial']['gwe']['meer_minder']:.2f}")
    print(f"   Settlement: €{onepager['financial']['totals']['totaal_eindafrekening']:.2f}")
    
    print("\n✅ Detail viewmodel:")
    print(f"   GWE regels: {len(detail['gwe']['kostenregels'])}")
    print(f"   Damage regels: {len(detail['damage']['regels'])}")
    print(f"   Stroom verbruik: {detail['gwe']['meterstanden']['stroom']['verbruik']} kWh")
    
    print("\n✅ Bar chart data (OnePager):")
    print(f"   Borg bars: {onepager['financial']['borg']['bars']}")
    print(f"   GWE bars: {onepager['financial']['gwe']['bars']}")
    
    # Save to JSON
    save_viewmodels_to_json(onepager, detail)
    
    print("\n✅ ViewModels test completed!")

