#!/usr/bin/env python3
"""
Calculator - Business Logic for Settlement Calculations

Handles all calculations for:
- Deposit (borg) - used vs. prepaid, refund calculations
- GWE - consumption, meter differences, overage calculations
- Cleaning - extra hours beyond package
- Damage - totals with VAT
- Final settlement - net amount to refund or charge
"""

from typing import Dict, Any, List
from entities import (
    Deposit, ExtraVoorschot, GWEMeterReading, GWERegel, GWETotalen, Cleaning,
    DamageRegel, DamageTotalen, Settlement, GWEMeterstanden
)


class Calculator:
    """Handles all business logic calculations for settlements"""
    
    # Constants
    BTW_PERCENTAGE = 0.21  # 21% VAT
    
    # ==================== DEPOSIT CALCULATIONS ====================
    
    @staticmethod
    def calculate_deposit(voorschot: float, damage_total_incl: float) -> Deposit:
        """
        Calculate deposit (borg) amounts
        
        Args:
            voorschot: Prepaid deposit amount
            damage_total_incl: Total damage cost (incl. VAT)
            
        Returns:
            Deposit entity with calculated values
        """
        gebruikt = min(voorschot, damage_total_incl)  # Amount used from deposit
        terug = max(0, voorschot - damage_total_incl)  # Amount to refund
        restschade = max(0, damage_total_incl - voorschot)  # Remaining damage beyond deposit
        
        return Deposit(
            voorschot=voorschot,
            gebruikt=gebruikt,
            terug=terug,
            restschade=restschade
        )
    
    # ==================== GWE CALCULATIONS ====================
    
    @staticmethod
    def calculate_meter_reading(begin: float, eind: float) -> GWEMeterReading:
        """
        Calculate meter consumption (verbruik)
        
        Args:
            begin: Starting meter reading
            eind: Ending meter reading
            
        Returns:
            GWEMeterReading with calculated consumption
        """
        verbruik = max(0, eind - begin)
        
        return GWEMeterReading(
            begin=begin,
            eind=eind,
            verbruik=verbruik
        )
    
    @staticmethod
    def calculate_gwe_regel_kosten(verbruik_of_dagen: float, tarief_excl: float) -> float:
        """
        Calculate cost for a single GWE line item
        
        Args:
            verbruik_of_dagen: Consumption amount or number of days
            tarief_excl: Rate excluding VAT
            
        Returns:
            Total cost excluding VAT
        """
        return verbruik_of_dagen * tarief_excl
    
    @staticmethod
    def calculate_gwe_totalen(regels: List[GWERegel]) -> GWETotalen:
        """
        Calculate GWE totals from cost lines
        
        Args:
            regels: List of GWE cost line items
            
        Returns:
            GWETotalen with calculated totals and VAT
        """
        totaal_excl = sum(regel.kosten_excl for regel in regels)
        
        # Calculate VAT per line
        btw = sum(regel.kosten_excl * regel.btw_percentage for regel in regels)
        
        totaal_incl = totaal_excl + btw
        
        return GWETotalen(
            totaal_excl=totaal_excl,
            btw=btw,
            totaal_incl=totaal_incl
        )
    
    @staticmethod
    def calculate_gwe_meer_minder(voorschot: float, totaal_incl: float) -> float:
        """
        Calculate GWE difference (positive = refund, negative = extra charge)
        
        Args:
            voorschot: Prepaid GWE amount
            totaal_incl: Actual GWE consumption (incl. VAT)
            
        Returns:
            Difference amount (voorschot - totaal_incl)
        """
        return voorschot - totaal_incl
    
    # ==================== CLEANING CALCULATIONS ====================
    
    @staticmethod
    def calculate_inbegrepen_uren(pakket_type: str) -> float:
        """
        Get included hours for cleaning package
        
        Args:
            pakket_type: Package type ('5_uur' or '7_uur')
            
        Returns:
            Number of included hours
        """
        if pakket_type == '7_uur':
            return 7.0
        elif pakket_type == 'achteraf':
            return 0.0
        return 5.0  # Default to 5_uur
    
    @staticmethod
    def calculate_cleaning(pakket_type: str, pakket_naam: str, totaal_uren: float, 
                          uurtarief: float, voorschot: float) -> Cleaning:
        """
        Calculate cleaning costs including extra hours
        
        Args:
            pakket_type: Package type ('geen', '5_uur' or '7_uur')
            totaal_uren: Total hours worked
            uurtarief: Hourly rate
            voorschot: Prepaid cleaning amount
            
        Returns:
            Cleaning entity with calculated extra hours and cost
        """
        # Handle "geen" package - no cleaning package purchased
        if pakket_type == 'geen':
            return Cleaning(
                pakket_type='geen',  # type: ignore
                pakket_naam=pakket_naam,
                inbegrepen_uren=0.0,
                totaal_uren=0.0,
                extra_uren=0.0,
                uurtarief=0.0,
                extra_bedrag=0.0,
                voorschot=0.0
            )
        
        inbegrepen_uren = Calculator.calculate_inbegrepen_uren(pakket_type)
        extra_uren = max(0, totaal_uren - inbegrepen_uren)
        extra_bedrag = extra_uren * uurtarief
        
        return Cleaning(
            pakket_type=pakket_type,  # type: ignore
            pakket_naam=pakket_naam,
            inbegrepen_uren=inbegrepen_uren,
            totaal_uren=totaal_uren,
            extra_uren=extra_uren,
            uurtarief=uurtarief,
            extra_bedrag=extra_bedrag,
            voorschot=voorschot
        )
    
    # ==================== DAMAGE CALCULATIONS ====================
    
    @staticmethod
    def calculate_damage_regel_bedrag(aantal: float, tarief_excl: float) -> float:
        """
        Calculate amount for a single damage line item
        
        Args:
            aantal: Quantity
            tarief_excl: Rate excluding VAT
            
        Returns:
            Total amount excluding VAT
        """
        return aantal * tarief_excl
    
    @staticmethod
    def calculate_damage_totalen(regels: List[DamageRegel]) -> DamageTotalen:
        """
        Calculate damage totals from line items
        
        Args:
            regels: List of damage line items
            
        Returns:
            DamageTotalen with calculated totals and VAT
        """
        totaal_excl = sum(regel.bedrag_excl for regel in regels)
        
        # Calculate VAT per line
        btw = sum(regel.bedrag_excl * regel.btw_percentage for regel in regels)
        
        totaal_incl = totaal_excl + btw
        
        return DamageTotalen(
            totaal_excl=totaal_excl,
            btw=btw,
            totaal_incl=totaal_incl
        )
    
    # ==================== SETTLEMENT CALCULATIONS ====================
    
    @staticmethod
    def calculate_settlement(borg: Deposit, gwe_voorschot: float, gwe_totalen: GWETotalen,
                            cleaning: Cleaning, damage_totalen: DamageTotalen,
                            extra_voorschot: ExtraVoorschot = None) -> Settlement:
        """
        Calculate final settlement
        
        Args:
            borg: Deposit entity
            gwe_voorschot: Prepaid GWE amount
            gwe_totalen: GWE totals
            cleaning: Cleaning entity
            damage_totalen: Damage totals
            extra_voorschot: Optional extra advance payment
            
        Returns:
            Settlement entity with final totals
        """
        # Net settlement calculation:
        # Positive = refund to customer
        # Negative = customer must pay
        
        totaal_eindafrekening = 0.0
        
        # Deposit refund (positive)
        # NOTE: Restschade (overflow) is NOT charged to the tenant in this report.
        # It is displayed visually but excluded from the settlement total.
        totaal_eindafrekening += borg.terug
        # totaal_eindafrekening -= borg.restschade  <-- REMOVED per user feedback
        
        # GWE: voorschot minus actual consumption
        gwe_meer_minder = gwe_voorschot - gwe_totalen.totaal_incl
        totaal_eindafrekening += gwe_meer_minder
        
        # Cleaning extra cost (negative) - only if package was purchased
        if cleaning.pakket_type != 'geen':
            totaal_eindafrekening -= cleaning.extra_bedrag
        
        # Extra voorschot refund (positive) - if exists
        # NOTE: Like borg, restschade is NOT charged in the settlement
        if extra_voorschot:
            totaal_eindafrekening += extra_voorschot.terug
        
        return Settlement(
            borg=borg,
            gwe_totalen=gwe_totalen,
            cleaning=cleaning,
            damage_totalen=damage_totalen,
            totaal_eindafrekening=totaal_eindafrekening
        )
    
    # ==================== PERCENTAGE CALCULATIONS (for bar charts) ====================
    
    @staticmethod
    def calculate_usage_percentage(gebruikt: float, voorschot: float) -> float:
        """
        Calculate usage percentage for bar charts
        
        Args:
            gebruikt: Amount used
            voorschot: Prepaid amount
            
        Returns:
            Percentage (0-100, capped at 100 for underfilled)
        """
        if voorschot == 0:
            return 0.0
        return min(100.0, (gebruikt / voorschot) * 100)
    
    @staticmethod
    def calculate_overage_percentage(extra: float, voorschot: float) -> float:
        """
        Calculate overage percentage for bar charts (extends beyond 100%)
        
        Args:
            extra: Extra amount beyond prepaid
            voorschot: Prepaid amount (baseline = 100%)
            
        Returns:
            Percentage relative to baseline
        """
        if voorschot == 0:
            return 0.0
        return (extra / voorschot) * 100
    
    @staticmethod
    def calculate_bar_percentages(gebruikt: float, voorschot: float) -> Dict[str, float]:
        """
        Calculate all bar chart percentages
        
        Args:
            gebruikt: Amount used
            voorschot: Prepaid amount
            
        Returns:
            Dictionary with 'gebruikt_pct', 'terug_pct', 'extra_pct', 'is_overfilled'
        """
        if voorschot == 0:
            return {
                'gebruikt_pct': 0.0,
                'terug_pct': 0.0,
                'extra_pct': 0.0,
                'is_overfilled': False
            }
        
        if gebruikt <= voorschot:
            # Underfilled - show used + return
            gebruikt_pct = (gebruikt / voorschot) * 100
            terug_pct = 100.0 - gebruikt_pct
            return {
                'gebruikt_pct': gebruikt_pct,
                'terug_pct': terug_pct,
                'extra_pct': 0.0,
                'is_overfilled': False
            }
        else:
            # Overfilled - show 100% used + extra beyond
            extra = gebruikt - voorschot
            extra_pct = (extra / voorschot) * 100
            return {
                'gebruikt_pct': 100.0,
                'terug_pct': 0.0,
                'extra_pct': extra_pct,
                'is_overfilled': True
            }


# ==================== VALIDATION FUNCTIONS ====================

def validate_excel_calculations(data: Dict[str, Any]) -> List[str]:
    """
    Validate Excel-calculated values against Python business logic.
    Returns list of warnings if mismatches found.
    
    This function checks if the Excel formulas produced the same results
    as the Python calculations. Useful for catching formula errors or
    manual overrides that don't match expected logic.
    
    Args:
        data: Dictionary with entity data from excel_reader
        
    Returns:
        List of warning messages (empty if all validations pass)
    """
    warnings = []
    calc = Calculator()
    
    # Check GWE meter readings (stroom/electricity)
    if 'gwe_meterstanden' in data:
        meters = data['gwe_meterstanden']
        
        # KWh verbruik
        expected_kwh = meters.stroom.eind - meters.stroom.begin
        if abs(expected_kwh - meters.stroom.verbruik) > 0.01:
            warnings.append(
                f"KWh verbruik komt niet overeen: "
                f"Verwacht {expected_kwh:.2f}, maar Excel heeft {meters.stroom.verbruik:.2f}"
            )
        
        # Gas verbruik
        expected_gas = meters.gas.eind - meters.gas.begin
        if abs(expected_gas - meters.gas.verbruik) > 0.01:
            warnings.append(
                f"Gas verbruik komt niet overeen: "
                f"Verwacht {expected_gas:.2f}, maar Excel heeft {meters.gas.verbruik:.2f}"
            )
            
        # Water verbruik (if present)
        if meters.water:
            expected_water = meters.water.eind - meters.water.begin
            if abs(expected_water - meters.water.verbruik) > 0.01:
                warnings.append(
                    f"Water verbruik komt niet overeen: "
                    f"Verwacht {expected_water:.2f}, maar Excel heeft {meters.water.verbruik:.2f}"
                )
    
    # Check GWE regel kosten (individual line items)
    if 'gwe_regels' in data:
        for i, regel in enumerate(data['gwe_regels'], 1):
            expected_kosten = regel.verbruik_of_dagen * regel.tarief_excl
            if abs(expected_kosten - regel.kosten_excl) > 0.01:
                warnings.append(
                    f"GWE regel {i} '{regel.omschrijving}': "
                    f"Kosten verwacht {expected_kosten:.2f}, maar Excel heeft {regel.kosten_excl:.2f}"
                )
    
    # Check GWE totals
    if 'gwe_regels' in data and 'gwe_totalen' in data:
        expected_gwe_excl = sum(r.kosten_excl for r in data['gwe_regels'])
        if abs(expected_gwe_excl - data['gwe_totalen'].totaal_excl) > 0.01:
            warnings.append(
                f"GWE totaal excl komt niet overeen: "
                f"Verwacht {expected_gwe_excl:.2f}, maar Excel heeft {data['gwe_totalen'].totaal_excl:.2f}"
            )
        
        expected_gwe_btw = sum(r.kosten_excl * r.btw_percentage for r in data['gwe_regels'])
        if abs(expected_gwe_btw - data['gwe_totalen'].btw) > 0.01:
            warnings.append(
                f"GWE BTW komt niet overeen: "
                f"Verwacht {expected_gwe_btw:.2f}, maar Excel heeft {data['gwe_totalen'].btw:.2f}"
            )
        
        expected_gwe_incl = expected_gwe_excl + expected_gwe_btw
        if abs(expected_gwe_incl - data['gwe_totalen'].totaal_incl) > 0.01:
            warnings.append(
                f"GWE totaal incl komt niet overeen: "
                f"Verwacht {expected_gwe_incl:.2f}, maar Excel heeft {data['gwe_totalen'].totaal_incl:.2f}"
            )
    
    # Check cleaning calculations
    if 'cleaning' in data:
        cleaning = data['cleaning']
        
        # Extra uren
        expected_inbegrepen = 5.0 if cleaning.pakket_type == '5_uur' else 7.0
        if abs(expected_inbegrepen - cleaning.inbegrepen_uren) > 0.01:
            warnings.append(
                f"Inbegrepen uren komt niet overeen: "
                f"Verwacht {expected_inbegrepen:.2f}, maar Excel heeft {cleaning.inbegrepen_uren:.2f}"
            )
        
        expected_extra_uren = max(0, cleaning.totaal_uren - expected_inbegrepen)
        if abs(expected_extra_uren - cleaning.extra_uren) > 0.01:
            warnings.append(
                f"Extra uren komt niet overeen: "
                f"Verwacht {expected_extra_uren:.2f}, maar Excel heeft {cleaning.extra_uren:.2f}"
            )
        
        expected_extra_bedrag = expected_extra_uren * cleaning.uurtarief
        if abs(expected_extra_bedrag - cleaning.extra_bedrag) > 0.01:
            warnings.append(
                f"Extra schoonmaak bedrag komt niet overeen: "
                f"Verwacht €{expected_extra_bedrag:.2f}, maar Excel heeft €{cleaning.extra_bedrag:.2f}"
            )
    
    # Check damage regel bedragen (individual line items)
    if 'damage_regels' in data:
        for i, regel in enumerate(data['damage_regels'], 1):
            expected_bedrag = regel.aantal * regel.tarief_excl
            if abs(expected_bedrag - regel.bedrag_excl) > 0.01:
                warnings.append(
                    f"Schade regel {i} '{regel.beschrijving}': "
                    f"Bedrag verwacht €{expected_bedrag:.2f}, maar Excel heeft €{regel.bedrag_excl:.2f}"
                )
    
    # Check damage totals
    if 'damage_regels' in data and 'damage_totalen' in data:
        expected_damage_excl = sum(r.bedrag_excl for r in data['damage_regels'])
        if abs(expected_damage_excl - data['damage_totalen'].totaal_excl) > 0.01:
            warnings.append(
                f"Schade totaal excl komt niet overeen: "
                f"Verwacht €{expected_damage_excl:.2f}, maar Excel heeft €{data['damage_totalen'].totaal_excl:.2f}"
            )
        
        expected_damage_btw = sum(r.bedrag_excl * r.btw_percentage for r in data['damage_regels'])
        if abs(expected_damage_btw - data['damage_totalen'].btw) > 0.01:
            warnings.append(
                f"Schade BTW komt niet overeen: "
                f"Verwacht €{expected_damage_btw:.2f}, maar Excel heeft €{data['damage_totalen'].btw:.2f}"
            )
        
        expected_damage_incl = expected_damage_excl + expected_damage_btw
        if abs(expected_damage_incl - data['damage_totalen'].totaal_incl) > 0.01:
            warnings.append(
                f"Schade totaal incl komt niet overeen: "
                f"Verwacht €{expected_damage_incl:.2f}, maar Excel heeft €{data['damage_totalen'].totaal_incl:.2f}"
            )
    
    # Check deposit calculations
    if 'deposit' in data and 'damage_totalen' in data:
        dep = data['deposit']
        
        expected_gebruikt = min(dep.voorschot, data['damage_totalen'].totaal_incl)
        if abs(expected_gebruikt - dep.gebruikt) > 0.01:
            warnings.append(
                f"Borg gebruikt komt niet overeen: "
                f"Verwacht €{expected_gebruikt:.2f}, maar Excel heeft €{dep.gebruikt:.2f}"
            )
        
        expected_terug = max(0, dep.voorschot - data['damage_totalen'].totaal_incl)
        if abs(expected_terug - dep.terug) > 0.01:
            warnings.append(
                f"Borg terug komt niet overeen: "
                f"Verwacht €{expected_terug:.2f}, maar Excel heeft €{dep.terug:.2f}"
            )
        
        expected_restschade = max(0, data['damage_totalen'].totaal_incl - dep.voorschot)
        if abs(expected_restschade - dep.restschade) > 0.01:
            warnings.append(
                f"Restschade komt niet overeen: "
                f"Verwacht €{expected_restschade:.2f}, maar Excel heeft €{dep.restschade:.2f}"
            )
    
    return warnings


# ==================== CONVENIENCE FUNCTIONS ====================

def recalculate_all(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalculate all computed values from raw Excel data
    
    Useful for ensuring consistency even if Excel formulas are missing
    
    Args:
        data: Dictionary with raw entity data from excel_reader
        
    Returns:
        Same dictionary with recalculated values
    """
    calc = Calculator()
    
    # Recalculate GWE meter readings
    if 'gwe_meterstanden' in data:
        meters = data['gwe_meterstanden']
        meters.stroom = calc.calculate_meter_reading(
            meters.stroom.begin, 
            meters.stroom.eind
        )
        meters.gas = calc.calculate_meter_reading(
            meters.gas.begin,
            meters.gas.eind
        )
        # Recalculate Water if present
        if meters.water:
            meters.water = calc.calculate_meter_reading(
                meters.water.begin,
                meters.water.eind
            )
    
    # Recalculate GWE regel kosten
    if 'gwe_regels' in data:
        for regel in data['gwe_regels']:
            regel.kosten_excl = calc.calculate_gwe_regel_kosten(
                regel.verbruik_of_dagen,
                regel.tarief_excl
            )
    
    # Recalculate GWE totals - only if there are detail lines with actual costs
    # If no detail lines with costs exist, preserve existing totals from Excel
    if 'gwe_regels' in data and len(data['gwe_regels']) > 0:
        # Always recalculate if rules exist, as Excel formulas might not be calculated
        data['gwe_totalen'] = calc.calculate_gwe_totalen(data['gwe_regels'])
    
    # Recalculate damage regel bedragen
    if 'damage_regels' in data:
        for regel in data['damage_regels']:
            regel.bedrag_excl = calc.calculate_damage_regel_bedrag(
                regel.aantal,
                regel.tarief_excl
            )
    
    # Recalculate damage totals - only if there are detail lines with actual amounts
    # If no detail lines with amounts exist, preserve existing totals from Excel
    if 'damage_regels' in data and len(data['damage_regels']) > 0:
        # Always recalculate if rules exist, as Excel formulas might not be calculated
        data['damage_totalen'] = calc.calculate_damage_totalen(data['damage_regels'])
    
    # Recalculate cleaning
    if 'cleaning' in data:
        cleaning = data['cleaning']
        data['cleaning'] = calc.calculate_cleaning(
            cleaning.pakket_type,
            cleaning.pakket_naam,
            cleaning.totaal_uren,
            cleaning.uurtarief,
            cleaning.voorschot
        )
    
    # Recalculate deposit - preserve gebruikt value from Excel
    if 'deposit' in data and 'damage_totalen' in data:
        # NOTE: We preserve the 'gebruikt' value from Excel because deposits can be
        # used for various purposes (damage, cleaning, other costs), not just damage.
        # The Excel 'Borg_gebruikt' field is the source of truth.
        existing_deposit = data['deposit']
        voorschot = existing_deposit.voorschot
        gebruikt = existing_deposit.gebruikt  # Preserve from Excel
        terug = max(0, voorschot - gebruikt)

        # Recalculate terug and restschade based on Excel's gebruikt value (which is total damage)
        # Logic:
        # - Gebruikt (for display/calc) is the TOTAL damage amount (so client sees full cost)
        # - Restschade is the overflow (Total Damage - Voorschot)
        # - Terug is what's left (Voorschot - Total Damage, min 0)
        
        # Use damage_totalen if available, otherwise fallback to Excel value
        total_damage = existing_deposit.gebruikt
        if 'damage_totalen' in data:
             total_damage = max(total_damage, data['damage_totalen'].totaal_incl)
        
        # We store the FULL damage as 'gebruikt' so it appears in the "Kosten" column of the table.
        # For the bar chart (yellow bar), we will cap it in viewmodels.py.
        gebruikt_full = total_damage
        terug = max(0, voorschot - total_damage)
        restschade = max(0, total_damage - voorschot)

        data['deposit'] = Deposit(
            voorschot=voorschot,
            gebruikt=gebruikt_full,
            terug=terug,
            restschade=restschade
        )
    
    return data


if __name__ == "__main__":
    """Test the calculator"""
    print("🧮 Testing Calculator")
    print("=" * 60)
    
    # Test deposit calculation
    print("\n1. Deposit Calculation:")
    deposit = Calculator.calculate_deposit(voorschot=800, damage_total_incl=600)
    print(f"   Voorschot: €{deposit.voorschot}")
    print(f"   Gebruikt: €{deposit.gebruikt}")
    print(f"   Terug: €{deposit.terug}")
    print(f"   Restschade: €{deposit.restschade}")
    
    # Test GWE calculation
    print("\n2. GWE Calculation:")
    regels = [
        GWERegel("Elektra verbruik", 500, 0.28, 140),
        GWERegel("Gas verbruik", 100, 1.15, 115),
        GWERegel("Vaste levering", 12, 0.48, 5.76)
    ]
    gwe_totals = Calculator.calculate_gwe_totalen(regels)
    print(f"   Totaal excl: €{gwe_totals.totaal_excl:.2f}")
    print(f"   BTW: €{gwe_totals.btw:.2f}")
    print(f"   Totaal incl: €{gwe_totals.totaal_incl:.2f}")
    
    # Test cleaning calculation
    print("\n3. Cleaning Calculation:")
    cleaning = Calculator.calculate_cleaning(
        pakket_type="5_uur",
        pakket_naam="Basis Schoonmaak",
        totaal_uren=7.5,
        uurtarief=50,
        voorschot=250
    )
    print(f"   Pakket: {cleaning.pakket_type}")
    print(f"   Inbegrepen: {cleaning.inbegrepen_uren} uur")
    print(f"   Totaal: {cleaning.totaal_uren} uur")
    print(f"   Extra: {cleaning.extra_uren} uur")
    print(f"   Extra bedrag: €{cleaning.extra_bedrag}")
    
    # Test bar percentages
    print("\n4. Bar Percentages:")
    bars = Calculator.calculate_bar_percentages(gebruikt=600, voorschot=800)
    print(f"   Underfilled scenario:")
    print(f"   - Gebruikt: {bars['gebruikt_pct']:.1f}%")
    print(f"   - Terug: {bars['terug_pct']:.1f}%")
    print(f"   - Is overfilled: {bars['is_overfilled']}")
    
    bars2 = Calculator.calculate_bar_percentages(gebruikt=450, voorschot=350)
    print(f"\n   Overfilled scenario:")
    print(f"   - Gebruikt: {bars2['gebruikt_pct']:.1f}%")
    print(f"   - Extra: {bars2['extra_pct']:.1f}%")
    print(f"   - Is overfilled: {bars2['is_overfilled']}")
    
    print("\n✅ Calculator tests completed!")

