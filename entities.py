#!/usr/bin/env python3
"""
Entities - Data Models for RyanRent Eindafrekening Generator

All dataclasses representing the domain model for settlement generation.
Matches the structure defined in Mappings/entities.json.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Literal


@dataclass
class Client:
    """Client information"""
    name: str
    contact_person: str
    email: str
    phone: Optional[str] = None


@dataclass
class Object:
    """Rental property information"""
    address: str
    unit: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    object_id: Optional[str] = None


@dataclass
class Period:
    """Rental period information"""
    checkin_date: date
    checkout_date: date
    days: int


@dataclass
class Deposit:
    """Deposit (borg) information"""
    voorschot: float  # Prepaid deposit
    gebruikt: float   # Amount used
    terug: float      # Amount to return
    restschade: float # Remaining damage costs


@dataclass
class GWEMeterReading:
    """Utility meter reading (electricity or gas)"""
    begin: float      # Starting meter reading
    eind: float       # Ending meter reading
    verbruik: float   # Consumption (eind - begin)


@dataclass
class GWERegel:
    """Single GWE cost line item"""
    omschrijving: str           # Description
    verbruik_of_dagen: float    # Consumption or days
    tarief_excl: float          # Rate excl. VAT
    kosten_excl: float          # Cost excl. VAT


@dataclass
class GWETotalen:
    """GWE totals with VAT calculation"""
    totaal_excl: float  # Total excl. VAT
    btw: float          # VAT amount (21%)
    totaal_incl: float  # Total incl. VAT


@dataclass
class Cleaning:
    """Cleaning cost information"""
    pakket_type: Literal["5_uur", "7_uur"]  # Package type
    pakket_naam: str                        # Display name (e.g. "Basis Schoonmaak")
    inbegrepen_uren: float                  # Hours included in package
    totaal_uren: float                      # Total hours worked
    extra_uren: float                       # Extra hours beyond package
    uurtarief: float                        # Hourly rate
    extra_bedrag: float                     # Extra cost for extra hours
    voorschot: float                        # Prepaid cleaning amount


@dataclass
class DamageRegel:
    """Single damage line item"""
    beschrijving: str     # Description
    aantal: float         # Quantity
    tarief_excl: float    # Rate excl. VAT
    bedrag_excl: float    # Amount excl. VAT


@dataclass
class DamageTotalen:
    """Damage totals with VAT calculation"""
    totaal_excl: float  # Total excl. VAT
    btw: float          # VAT amount (21%)
    totaal_incl: float  # Total incl. VAT


@dataclass
class Settlement:
    """Complete settlement information"""
    borg: Deposit
    gwe_totalen: GWETotalen
    cleaning: Cleaning
    damage_totalen: DamageTotalen
    totaal_eindafrekening: float  # Final settlement total (positive = refund, negative = charge)


@dataclass
class GWEMeterstanden:
    """Container for all meter readings"""
    stroom: GWEMeterReading  # Electricity meter
    gas: GWEMeterReading     # Gas meter


@dataclass
class OnePagerViewModel:
    """View model for OnePager template - single-page summary"""
    client: Client
    object: Object
    period: Period
    settlement: Settlement


@dataclass
class DetailViewModel:
    """View model for Detail template - comprehensive breakdown"""
    client: Client
    object: Object
    period: Period
    gwe_meterstanden: GWEMeterstanden
    gwe_regels: List[GWERegel]
    gwe_totalen: GWETotalen
    cleaning: Cleaning
    damage_regels: List[DamageRegel]
    damage_totalen: DamageTotalen
    borg: Deposit
