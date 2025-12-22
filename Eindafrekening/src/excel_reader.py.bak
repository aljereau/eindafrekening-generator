#!/usr/bin/env python3
"""
Excel Reader - Reads data from Excel template using named ranges

Reads the 4-sheet Excel template (Algemeen, GWE_Detail, Schoonmaak, Schade)
using named ranges defined in developer-mapping.json and returns structured data.
"""

import openpyxl
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from entities import (
    Client, RentalProperty, Period, Deposit, ExtraVoorschot, GWEMeterReading, GWERegel, 
    GWETotalen, Cleaning, DamageRegel, DamageTotalen, GWEMeterstanden
)


class ExcelReader:
    """Reads Excel data using named ranges and returns entity objects"""
    
    def __init__(self, filepath: str):
        """Initialize reader with Excel file path"""
        self.filepath = filepath
        self.wb = None
        
    def __enter__(self):
        """Context manager entry - open workbook"""
        self.wb = openpyxl.load_workbook(self.filepath, data_only=True)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close workbook"""
        if self.wb:
            self.wb.close()
    
    def get_named_value(self, name: str) -> Any:
        """
        Get value from named range
        
        Args:
            name: Named range name (e.g., 'Klantnaam')
            
        Returns:
            Cell value or None if not found
        """
        if not self.wb:
            raise RuntimeError("Workbook not opened. Use context manager.")
            
        try:
            # Get defined name
            if name not in self.wb.defined_names:
                print(f"⚠️  Warning: Named range '{name}' not found")
                return None
                
            defn = self.wb.defined_names[name]
            
            # Parse the reference (format: "SheetName!$A$1")
            destinations = list(defn.destinations)
            if not destinations:
                return None
                
            sheet_name, cell_ref = destinations[0]
            ws = self.wb[sheet_name]
            
            # Remove $ signs from cell reference
            cell_ref = cell_ref.replace('$', '')
            
            return ws[cell_ref].value
            
        except Exception as e:
            print(f"⚠️  Warning: Error reading named range '{name}': {e}")
            return None
    
    def get_string(self, name: str, default: str = "") -> str:
        """Get string value from named range"""
        val = self.get_named_value(name)
        if val is None:
            return default
        return str(val).strip()
    
    def get_float(self, name: str, default: float = 0.0) -> float:
        """Get float value from named range"""
        val = self.get_named_value(name)
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            print(f"⚠️  Warning: Could not convert '{val}' to float for '{name}', using {default}")
            return default
    
    def get_int(self, name: str, default: int = 0) -> int:
        """Get integer value from named range"""
        val = self.get_named_value(name)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            print(f"⚠️  Warning: Could not convert '{val}' to int for '{name}', using {default}")
            return default
    
    def get_date(self, name: str, default: Optional[date] = None) -> Optional[date]:
        """Get date value from named range"""
        val = self.get_named_value(name)
        if val is None:
            return default
            
        # Handle datetime objects from Excel
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
            
        # Try parsing string
        if isinstance(val, str):
            try:
                return datetime.strptime(val, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.strptime(val, '%d-%m-%Y').date()
                except ValueError:
                    print(f"⚠️  Warning: Could not parse date '{val}' for '{name}'")
                    return default
        
        return default
    
    def read_table_range(self, sheet_name: str, start_row: int, start_col: int = 1, 
                        num_cols: int = 4, max_rows: int = 200) -> List[List[Any]]:
        """
        Read a dynamic table from Excel (stops at first empty row)
        
        Args:
            sheet_name: Sheet name
            start_row: Starting row number (1-indexed)
            start_col: Starting column (1-indexed)
            num_cols: Number of columns to read
            max_rows: Maximum rows to scan
            
        Returns:
            List of row lists
        """
        if not self.wb:
            raise RuntimeError("Workbook not opened. Use context manager.")
            
        if sheet_name not in self.wb.sheetnames:
            print(f"⚠️  Warning: Sheet '{sheet_name}' not found")
            return []
            
        ws = self.wb[sheet_name]
        rows = []
        
        for row_idx in range(start_row, start_row + max_rows):
            # Read all columns in this row
            row_values = []
            is_empty = True
            
            for col_idx in range(start_col, start_col + num_cols):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                row_values.append(cell_value)
                
                # Check if any cell has data
                if cell_value is not None and str(cell_value).strip():
                    is_empty = False
            
            # Stop at first completely empty row
            if is_empty:
                break
                
            rows.append(row_values)
        
        return rows
    
    # ==================== ENTITY READERS ====================
    
    def read_client(self) -> Client:
        """Read client information from Algemeen sheet"""
        return Client(
            name=self.get_string('Klantnaam'),
            contact_person=self.get_string('Contactpersoon'),
            email=self.get_string('Email'),
            phone=self.get_string('Telefoonnummer') or None
        )
    
    def read_object(self) -> RentalProperty:
        """Read object (property) information from Algemeen sheet"""
        return RentalProperty(
            address=self.get_string('Object_adres'),
            unit=self.get_string('Unit_nr') or None,
            postal_code=self.get_string('Postcode') or None,
            city=self.get_string('Plaats') or None,
            object_id=self.get_string('Object_ID') or None
        )
    
    def read_period(self) -> Period:
        """Read rental period from Algemeen sheet"""
        checkin = self.get_date('Incheck_datum')
        checkout = self.get_date('Uitcheck_datum')
        days = self.get_int('Aantal_dagen')
        
        # Calculate days if not provided
        if days == 0 and checkin and checkout:
            days = (checkout - checkin).days
        
        return Period(
            checkin_date=checkin or date.today(),
            checkout_date=checkout or date.today(),
            days=days
        )
    
    def read_deposit(self) -> Deposit:
        """Read deposit (borg) information"""
        voorschot = self.get_float('Voorschot_borg')
        gebruikt = self.get_float('Borg_gebruikt')
        terug = self.get_float('Borg_terug')
        restschade = self.get_float('Restschade')
        
        return Deposit(
            voorschot=voorschot,
            gebruikt=gebruikt,
            terug=terug,
            restschade=restschade
        )
    
    def read_gwe_meterstanden(self) -> GWEMeterstanden:
        """Read GWE meter readings from GWE_Detail sheet"""
        stroom = GWEMeterReading(
            begin=self.get_float('KWh_begin'),
            eind=self.get_float('KWh_eind'),
            verbruik=self.get_float('KWh_verbruik')
        )
        
        gas = GWEMeterReading(
            begin=self.get_float('Gas_begin'),
            eind=self.get_float('Gas_eind'),
            verbruik=self.get_float('Gas_verbruik')
        )

        # Read Water (optional, might be 0 if not present)
        water_begin = self.get_float('Water_begin', default=0.0)
        water_eind = self.get_float('Water_eind', default=0.0)
        water_verbruik = self.get_float('Water_verbruik', default=0.0)
        
        water = None
        # Only create water reading if there's actual data (non-zero or explicitly entered)
        # We check if verbruik > 0 or if begin/eind are different
        if water_verbruik > 0 or water_eind > 0:
             water = GWEMeterReading(
                begin=water_begin,
                eind=water_eind,
                verbruik=water_verbruik
            )
        
        return GWEMeterstanden(stroom=stroom, gas=gas, water=water)
    
    def read_gwe_regels(self) -> List[GWERegel]:
        """Read GWE cost lines from GWE_Detail sheet table"""
        # Read dynamic table starting at row 17 (after section headers and table header row)
        # Now reading 8 columns: Type, Omschrijving, Eenheid, Verbruik, Tarief, Kosten, BTW %, BTW €
        rows = self.read_table_range('GWE_Detail', start_row=17, start_col=1, num_cols=8)
        
        regels = []
        for row in rows:
            type_val = str(row[0]).strip() if row[0] else "Overig"
            omschrijving = str(row[1]).strip() if row[1] else ""
            eenheid = str(row[2]).strip() if row[2] else ""
            verbruik = row[3] if row[3] is not None else 0
            tarief = row[4] if row[4] is not None else 0
            kosten = row[5] if row[5] is not None else 0
            btw_pct = row[6] if len(row) > 6 and row[6] is not None else 0.21 # Default to 21%
            
            # Skip empty rows and header rows
            if not omschrijving or omschrijving.lower() in ['omschrijving', 'beschrijving']:
                continue
            
            # Skip instruction rows
            if omschrijving.startswith('💡') or 'vul hier' in omschrijving.lower():
                continue

            # Skip Total rows (which might be read if there are no empty lines between data and totals)
            if 'totaal' in type_val.lower() or 'totaal' in omschrijving.lower():
                continue
            
            try:
                # Handle percentage input
                if isinstance(btw_pct, str):
                    btw_pct = float(btw_pct.replace('%', '').strip()) / 100 if '%' in btw_pct else float(btw_pct)
                elif btw_pct > 1:
                    btw_pct = btw_pct / 100

                regels.append(GWERegel(
                    omschrijving=omschrijving,
                    verbruik_of_dagen=float(verbruik),
                    tarief_excl=float(tarief),
                    kosten_excl=float(kosten),
                    btw_percentage=float(btw_pct),
                    type=type_val,
                    eenheid=eenheid
                ))
            except (ValueError, TypeError) as e:
                print(f"⚠️  Warning: Could not parse GWE regel '{omschrijving}': {e}")
                continue
        
        return regels
    
    def read_gwe_totalen(self) -> GWETotalen:
        """Read GWE totals from GWE_Detail sheet"""
        return GWETotalen(
            totaal_excl=self.get_float('GWE_totaal_excl'),
            btw=self.get_float('GWE_BTW'),
            totaal_incl=self.get_float('GWE_totaal_incl'),
            beheer_type=self.get_string('GWE_Beheer', default='Via RyanRent')
        )
    
    def read_cleaning(self) -> Cleaning:
        """Read cleaning information from Schoonmaak sheet"""
        pakket_raw = self.get_string('Schoonmaak_pakket', default='Basis Schoonmaak')
        pakket_naam = pakket_raw
        
        # Map to internal type
        if 'geen' in pakket_raw.lower() or not pakket_raw.strip():
            pakket = 'geen'
            pakket_naam = 'Geen pakket'
        elif 'intensief' in pakket_raw.lower():
            pakket = '7_uur'
        elif 'basis' in pakket_raw.lower():
            pakket = '5_uur'
        elif 'achteraf' in pakket_raw.lower():
            pakket = 'achteraf'
        elif pakket_raw in ['5_uur', '7_uur', 'achteraf']:
             pakket = pakket_raw
        else:
            print(f"⚠️  Warning: Unknown pakket type '{pakket_raw}', defaulting to '5_uur'")
            pakket = '5_uur'
        
        # Calculate VAT
        # Read totals from Excel as it is the source of truth
        totaal_incl = self.get_float('Schoonmaak_totaal_kosten', default=0.0)
        btw_pct = self.get_float('BTW_percentage_schoonmaak', default=0.21)

        voorschot = self.get_float('Schoonmaak_voorschot', default=0.0)
        
            # If voorschot is 0 but we have a package, calculate default value
        # This handles cases where user selects a package but leaves voorschot empty
        if voorschot == 0 and pakket not in ['geen', 'achteraf', 'op maat']:
            # Try to get standard hours for package
            inbegrepen = self.get_float('Schoonmaak_uren_inbegrepen', 0.0)
            tarief = self.get_float('Uurtarief_schoonmaak', 50.0)
            
            # Fallback for standard packages if Excel formula failed (inbegrepen=0)
            if inbegrepen == 0:
                if "basis" in pakket_naam.lower():
                    inbegrepen = 5.0 # Standard Basis hours
                elif "intensief" in pakket_naam.lower():
                    inbegrepen = 7.0 # Standard Intensief hours
            
            if inbegrepen > 0:
                # Calculate implied voorschot: hours * rate * (1+VAT)
                voorschot = inbegrepen * tarief * (1 + btw_pct)
                print(f"ℹ️  Calculated implied voorschot for {pakket_naam}: €{voorschot:.2f}")

        # Calculate VAT amount from total incl
        # Total Incl = Total Excl * (1 + VAT%)
        # Total Excl = Total Incl / (1 + VAT%)
        # VAT Amount = Total Incl - Total Excl
        totaal_excl = totaal_incl / (1 + btw_pct)
        btw_bedrag = totaal_incl - totaal_excl

        return Cleaning(
            pakket_type=pakket,  # type: ignore
            pakket_naam=pakket_naam,
            inbegrepen_uren=self.get_float('Inbegrepen_uren'),
            totaal_uren=self.get_float('Totaal_uren_gew'),
            extra_uren=self.get_float('Extra_uren'),
            uurtarief=self.get_float('Uurtarief_schoonmaak'),
            extra_bedrag=self.get_float('Extra_schoonmaak_bedrag'),
            voorschot=voorschot, # Use the calculated voorschot
            totaal_kosten_incl=totaal_incl,
            btw_percentage=btw_pct,
            btw_bedrag=btw_bedrag
        )
    
    def read_damage_regels(self) -> List[DamageRegel]:
        """Read damage line items from Schade sheet table"""
        # Read dynamic table starting at row 5
        # Now reading 6 columns: Beschrijving, Aantal, Tarief, Bedrag, BTW %, BTW €
        rows = self.read_table_range('Schade', start_row=5, start_col=1, num_cols=6)
        
        regels = []
        for row in rows:
            beschrijving = str(row[0]).strip() if row[0] else ""
            aantal = row[1] if row[1] is not None else 0
            tarief = row[2] if row[2] is not None else 0
            bedrag = row[3] if row[3] is not None else 0
            btw_pct = row[4] if len(row) > 4 and row[4] is not None else 0.21 # Default to 21%
            
            # Skip empty rows and header rows (check for "beschrijving" text in description)
            if not beschrijving or beschrijving.lower() in ['beschrijving', 'omschrijving']:
                continue
            
            try:
                # Handle percentage input
                if isinstance(btw_pct, str):
                    btw_pct = float(btw_pct.replace('%', '').strip()) / 100 if '%' in btw_pct else float(btw_pct)
                elif btw_pct > 1:
                    btw_pct = btw_pct / 100

                regels.append(DamageRegel(
                    beschrijving=beschrijving,
                    aantal=float(aantal),
                    tarief_excl=float(tarief),
                    bedrag_excl=float(bedrag),
                    btw_percentage=float(btw_pct)
                ))
            except (ValueError, TypeError) as e:
                print(f"⚠️  Warning: Could not parse damage regel '{beschrijving}': {e}")
                continue
        
        return regels
    
    def read_damage_totalen(self) -> DamageTotalen:
        """Read damage totals from Schade sheet"""
        return DamageTotalen(
            totaal_excl=self.get_float('Schade_totaal_excl'),
            btw=self.get_float('Schade_BTW'),
            totaal_incl=self.get_float('Schade_totaal_incl')
        )
    
    def read_extra_voorschot(self) -> Optional[ExtraVoorschot]:
        """Read extra voorschot information (furniture, garden, keys, etc.)"""
        bedrag = self.get_float('Extra_voorschot_bedrag', default=0.0)
        
        # If no extra voorschot, return None
        if bedrag <= 0:
            return None
        
        return ExtraVoorschot(
            voorschot=bedrag,
            omschrijving=self.get_string('Extra_voorschot_omschrijving', default='Extra voorschot'),
            gebruikt=self.get_float('Extra_voorschot_gebruikt', default=0.0),
            terug=self.get_float('Extra_voorschot_terug', default=bedrag),
            restschade=self.get_float('Extra_voorschot_restschade', default=0.0)
        )
    
    def read_all(self) -> Dict[str, Any]:
        """
        Read all data from Excel and return as dictionary of entities
        
        Returns:
            Dictionary with all entity objects
        """
        return {
            'client': self.read_client(),
            'object': self.read_object(),
            'period': self.read_period(),
            'deposit': self.read_deposit(),
            'gwe_meterstanden': self.read_gwe_meterstanden(),
            'gwe_regels': self.read_gwe_regels(),
            'gwe_totalen': self.read_gwe_totalen(),
            'cleaning': self.read_cleaning(),
            'damage_regels': self.read_damage_regels(),
            'damage_totalen': self.read_damage_totalen(),
            'extra_voorschot': self.read_extra_voorschot()
        }


def read_excel(filepath: str) -> Dict[str, Any]:
    """
    Convenience function to read Excel data
    
    Args:
        filepath: Path to Excel file
        
    Returns:
        Dictionary with all entity objects
    """
    # Detect file type
    wb = openpyxl.load_workbook(filepath, read_only=True)
    sheet_names = wb.sheetnames
    wb.close()
    
    if 'Input' in sheet_names:
        print(f"ℹ️  Detecting Master Template format ('Input' sheet found)")
        from master_reader import MasterReader
        reader = MasterReader(filepath)
        all_bookings = reader.read_all()
        
        if not all_bookings:
            raise ValueError("No valid bookings found in Master Template")
            
        print(f"   Found {len(all_bookings)} bookings.")
        return all_bookings # Return list of bookings
        
    else:
        # Legacy Format
        with ExcelReader(filepath) as reader:
            return reader.read_all()


if __name__ == "__main__":
    """Test the excel reader"""
    import sys
    
    test_file = sys.argv[1] if len(sys.argv) > 1 else "input_template.xlsx"
    
    print(f"📖 Testing Excel Reader with: {test_file}")
    print("=" * 60)
    
    try:
        data = read_excel(test_file)
        
        print(f"\n✅ Successfully read Excel data:")
        print(f"   Client: {data['client'].name}")
        print(f"   Object: {data['object'].address}")
        print(f"   Period: {data['period'].checkin_date} → {data['period'].checkout_date} ({data['period'].days} days)")
        print(f"   Deposit: €{data['deposit'].voorschot} (€{data['deposit'].gebruikt} used, €{data['deposit'].terug} back)")
        print(f"   GWE Regels: {len(data['gwe_regels'])} lines")
        print(f"   GWE Total: €{data['gwe_totalen'].totaal_incl}")
        print(f"   Cleaning: {data['cleaning'].pakket_type}, {data['cleaning'].totaal_uren} hours")
        print(f"   Damage Regels: {len(data['damage_regels'])} items")
        print(f"   Damage Total: €{data['damage_totalen'].totaal_incl}")
        
    except FileNotFoundError:
        print(f"\n❌ Error: File '{test_file}' not found")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

