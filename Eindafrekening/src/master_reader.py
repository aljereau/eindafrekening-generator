#!/usr/bin/env python3
"""
Master Reader
Reads row-based Master Excel sheet and converts it to structured booking data.
"""

import openpyxl
from collections import defaultdict
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import sys
import os

# Add Shared and src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(os.path.join(root_dir, 'Shared'))

# Import entities from existing excel_reader (reuse definitions)
from entities import (
    Client, RentalProperty, Period, Deposit, ExtraVoorschot, GWEMeterReading, GWERegel, 
    GWETotalen, Cleaning, DamageRegel, DamageTotalen, GWEMeterstanden
)
# We need Database to fetch missing details (like Postcode/City)
from database import Database

class MasterReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.db = Database()
        
    def read_all(self) -> List[Dict[str, Any]]:
        """Read master sheet and return list of booking data dicts"""
        print(f"📖 Reading Master Input: {self.filepath}")
        wb = openpyxl.load_workbook(self.filepath, data_only=True)
        ws = wb.active # Assume first sheet
        
        # Group rows by Address (or Booking Identifier if available)
        # Using Address + Checkin Date as unique key would be safer, 
        # but for now let's assume rows are grouped by Address or just process sequentially.
        # Actually, grouping by address allows scattered rows.
        
        grouped_data = defaultdict(list)
        
        # Iterating rows, skipping header
        for row in ws.iter_rows(min_row=2, values_only=True):
            adres = row[0]
            if not adres: continue
            grouped_data[adres].append(row)
            
        results = []
        
        for adres, rows in grouped_data.items():
            try:
                booking_data = self._process_booking_rows(adres, rows)
                if booking_data:
                    results.append(booking_data)
            except Exception as e:
                print(f"❌ Error processing booking for {adres}: {e}")
                # Continue with next booking
                
        return results

    def _process_booking_rows(self, adres: str, rows: List[tuple]) -> Optional[Dict[str, Any]]:
        """Process all rows for a single booking/address"""
        
        # Initialize containers
        client = None
        period = None
        deposit = None
        gwe_standen = None
        cleaning = None
        damage_regels = []
        gwe_regels = [] # Added initialization
        extra_voorschot = None
        gwe_settings = {'beheer_type': 'Via RyanRent'} # Default
        
        # Helper to parse amount strings
        def parse_float(val):
            if not val: return 0.0
            if isinstance(val, (int, float)): return float(val)
            try:
                return float(str(val).replace('€', '').replace(',', '.').strip())
            except:
                return 0.0

        # Helper to parse dates
        def parse_date(val):
            if not val: return date.today()
            if isinstance(val, datetime): return val.date()
            if isinstance(val, date): return val
            return date.today() # Fallback

        has_basis = False

        for row in rows:
            # Ensure row has enough columns (pad if needed)
            if len(row) < 26:
                row = row + (None,) * (26 - len(row))
                
            row_type = str(row[1]).strip() if row[1] else ""
            
            if row_type == "Basis":
                has_basis = True
                
            if row_type == "Basis":
                has_basis = True
                
                # Column mapping based on updated template
                # 0:Adres, 1:Type, 2:Klant, 3:ObjID
                # 4:Checkin, 5:Checkout, 6:Borg
                # 7:GWEBeh, 8:Meter, 9:Lev, 10:Contr, 11:ExVr, 12:ExDesc
                
                klant_naam = row[2]
                checkin = parse_date(row[4])
                checkout = parse_date(row[5])
                borg_voorschot = parse_float(row[6])
                
                gwe_beheer_val = str(row[7]).strip() if row[7] else "Via RyanRent"
                gwe_settings['beheer_type'] = gwe_beheer_val
                
                # Extra Voorschot
                ex_voor_bedrag = parse_float(row[11])
                ex_voor_desc = str(row[12]) if row[12] else "Extra Voorschot"
                
                if ex_voor_bedrag > 0:
                    extra_voorschot = ExtraVoorschot(
                        voorschot=ex_voor_bedrag,
                        gebruikt=0.0,
                        terug=ex_voor_bedrag,
                        restschade=0.0,
                        omschrijving=ex_voor_desc
                    )
                
                # Client
                client = Client(name=klant_naam, contact_person="", email="", phone=None)
                
                # Period
                days = (checkout - checkin).days
                period = Period(checkin_date=checkin, checkout_date=checkout, days=days)
                
                # Deposit
                deposit = Deposit(voorschot=borg_voorschot, gebruikt=0.0, terug=0.0, restschade=0.0)

            elif row_type == "GWE":
                # Readings (Cols N-S -> Indices 13-18)
                elek_start = parse_float(row[13])
                elek_eind = parse_float(row[14])
                gas_start = parse_float(row[15])
                gas_eind = parse_float(row[16])
                water_start = parse_float(row[17])
                water_eind = parse_float(row[18])
                
                stroom = GWEMeterReading(begin=elek_start, eind=elek_eind, verbruik=elek_eind-elek_start)
                gas = GWEMeterReading(begin=gas_start, eind=gas_eind, verbruik=gas_eind-gas_start)
                water = GWEMeterReading(begin=water_start, eind=water_eind, verbruik=water_eind-water_start)
                
                gwe_standen = GWEMeterstanden(stroom=stroom, gas=gas, water=water)
                
            elif row_type == "Schoonmaak":
                # Cleaning (Cols T-Z -> Indices 19-25)
                # 19:Pakket, 20:Uren, 21:Tarief, 22:TotEx, 23:BTW%, 24:BTW€, 25:TotInc
                pakket = str(row[19]).strip()
                uren = parse_float(row[20])
                tarief = parse_float(row[21])
                btw_pct = parse_float(row[23]) # Index 23 now
                
                if not btw_pct: btw_pct = 0.21
                if btw_pct > 1: btw_pct = btw_pct / 100 
                
                # Map packet name
                pakket_code = '5_uur'
                if 'basis' in pakket.lower(): pakket_code = '5_uur'
                elif 'intensief' in pakket.lower(): pakket_code = '7_uur'
                elif 'geen' in pakket.lower(): pakket_code = 'geen'
                elif 'achteraf' in pakket.lower(): pakket_code = 'achteraf'
                
                # Calculate costs
                total_cost = uren * tarief * (1 + btw_pct)
                
                cleaning = Cleaning(
                    pakket_type=pakket_code,
                    pakket_naam=pakket,
                    inbegrepen_uren=0, 
                    totaal_uren=uren,
                    extra_uren=0,
                    uurtarief=tarief,
                    extra_bedrag=0,
                    voorschot=0, 
                    totaal_kosten_incl=total_cost,
                    btw_percentage=btw_pct,
                    btw_bedrag=total_cost - (total_cost/(1+btw_pct))
                )

            elif row_type == "GWE_Item":
                # Cols AA-AI (Indices 26-34)
                # 26:Type, 27:Eenheid, 28:Desc, 29:Aant, 30:Prijs, 31:TotEx, 32:BTW%, 33:BTW€, 34:TotInc
                k_type = str(row[26]).strip() if row[26] else "Overig"
                eenheid = str(row[27]).strip() if row[27] else ""
                desc = row[28]
                aantal = parse_float(row[29])
                prijs = parse_float(row[30])
                btw = parse_float(row[32])
                
                if btw > 1: btw = btw / 100
                if not btw: btw = 0.21
                
                bedrag_excl = aantal * prijs
                
                # Append to gwe_regels list
                gwe_regels.append(GWERegel(
                    type=k_type,
                    omschrijving=desc,
                    eenheid=eenheid,
                    verbruik_of_dagen=aantal,
                    tarief_excl=prijs,
                    kosten_excl=bedrag_excl,
                    btw_percentage=btw
                ))

            elif row_type in ["Schade", "Extra"]:
                # Cols AA-AI (Indices 26-34) - SAME columns as GWE_Item!
                # 26:Type (Ignore), 27:Eenheid (Ignore?), 28:Desc, 29:Aant, 30:Prijs, 32:BTW%
                desc = row[28]
                qty = parse_float(row[29])
                amt = parse_float(row[30]) 
                btw = parse_float(row[32]) 
                
                if btw > 1: btw = btw / 100
                if not btw: btw = 0.21 
                
                tarief = amt 
                total_excl = qty * tarief
                
                damage_regels.append(DamageRegel(
                    beschrijving=desc,
                    aantal=qty,
                    tarief_excl=tarief,
                    bedrag_excl=total_excl,
                    btw_percentage=btw
                ))

        if not has_basis:
            print(f"⚠️  Skipping {adres}: No 'Basis' row found.")
            return None

        # Fetch Property Details from DB
        prop_details = self._fetch_property_details(adres)
        rental_property = RentalProperty(
            address=adres,
            unit=None,
            postal_code=prop_details.get('postcode'),
            city=prop_details.get('plaats'),
            object_id=prop_details.get('object_id')
        )
        
        # Defaults if missing
        if not gwe_standen:
            z = GWEMeterReading(0,0,0)
            gwe_standen = GWEMeterstanden(z,z,z)
            
        if not cleaning:
            cleaning = Cleaning('geen', 'Geen pakket', 0,0,0,0,0,0,0,0,0)

        # Totals mapping
        gwe_totalen = GWETotalen(0,0,0, gwe_settings['beheer_type'])
        damage_totalen = DamageTotalen(0,0,0)
        
        return {
            'client': client,
            'object': rental_property,
            'period': period,
            'deposit': deposit,
            'gwe_meterstanden': gwe_standen,
            'gwe_regels': gwe_regels, 
            'gwe_totalen': gwe_totalen,
            'cleaning': cleaning,
            'damage_regels': damage_regels,
            'damage_totalen': damage_totalen,
            'extra_voorschot': extra_voorschot
        }

    def _fetch_property_details(self, adres: str) -> Dict[str, Any]:
        """Fetch details from DB"""
        try:
             # We need to get a fresh connection - context manager usage is better but ad-hoc here
             conn = self.db.get_connection()
             cursor = conn.execute("SELECT object_id, postcode, plaats FROM huizen WHERE adres=?", (adres,))
             row = cursor.fetchone()
             conn.close()
             if row:
                 return {'object_id': row[0], 'postcode': row[1], 'plaats': row[2]}
        except Exception as e:
            print(f"⚠️ DB Error fetching property {adres}: {e}")
            
        return {}

if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "../input_master.xlsx"
    reader = MasterReader(file)
    data = reader.read_all()
    for d in data:
        print(f"Found: {d['object'].address} - {d['client'].name}")
