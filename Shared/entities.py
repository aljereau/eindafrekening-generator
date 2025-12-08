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
class RentalProperty:
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
class ExtraVoorschot:
    """Extra advance payment (furniture, garden, keys, etc.)"""
    voorschot: float      # Advance amount
    omschrijving: str     # Description (e.g., "meubilair", "tuinonderhoud")
    gebruikt: float       # Amount used
    terug: float          # Amount to return
    restschade: float     # Damage exceeding deposit (if any)


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
    btw_percentage: float = 0.21 # VAT percentage (default 21%)
    type: str = "Overig"        # Type (Gas, Water, Elektra, Overig)
    eenheid: str = ""           # Unit (kWh, m3, Dagen, etc.)


@dataclass
class GWETotalen:
    """GWE totals with VAT calculation"""
    totaal_excl: float  # Total excl. VAT
    btw: float          # VAT amount (calculated from lines)
    totaal_incl: float  # Total incl. VAT
    beheer_type: str = "Via RyanRent" # "Via RyanRent" or "Eigen Beheer"


@dataclass
class Cleaning:
    """Cleaning cost information"""
    pakket_type: Literal["geen", "5_uur", "7_uur"]  # Package type ("geen" = no package)
    pakket_naam: str                                # Display name (e.g. "Basis Schoonmaak", "Geen pakket")
    inbegrepen_uren: float                          # Hours included in package
    totaal_uren: float                              # Total hours worked
    extra_uren: float                               # Extra hours beyond package
    uurtarief: float                                # Hourly rate
    extra_bedrag: float                             # Extra cost for extra hours
    voorschot: float                                # Prepaid cleaning amount
    totaal_kosten_incl: float = 0.0                 # Total cleaning costs incl VAT
    btw_percentage: float = 0.21                    # VAT percentage (default 21%)
    btw_bedrag: float = 0.0                         # VAT amount


@dataclass
class DamageRegel:
    """Single damage line item"""
    beschrijving: str     # Description
    aantal: float         # Quantity
    tarief_excl: float    # Rate excl. VAT
    bedrag_excl: float    # Amount excl. VAT
    btw_percentage: float = 0.21 # VAT percentage (default 21%)


@dataclass
class DamageTotalen:
    """Damage totals with VAT calculation"""
    totaal_excl: float  # Total excl. VAT
    btw: float          # VAT amount (calculated from lines)
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
    water: Optional[GWEMeterReading] = None # Water meter (optional)


@dataclass
class OnePagerViewModel:
    """View model for OnePager template - single-page summary"""
    client: Client
    object: RentalProperty
    period: Period
    settlement: Settlement


@dataclass
class DetailViewModel:
    """View model for Detail template - comprehensive breakdown"""
    client: Client
    object: RentalProperty
    period: Period
    gwe_meterstanden: GWEMeterstanden
    gwe_regels: List[GWERegel]
    gwe_totalen: GWETotalen
    cleaning: Cleaning
    damage_regels: List[DamageRegel]
    damage_totalen: DamageTotalen
    borg: Deposit


@dataclass
class Huis:
    """Physical House Entity (huizen table)"""
    id: Optional[int]
    object_id: str
    adres: str
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    woning_type: Optional[str] = None
    oppervlakte: Optional[float] = None
    aantal_sk: Optional[int] = None # Aantal slaapkamers
    aantal_pers: Optional[int] = None # Capaciteit
    status: str = "active"


@dataclass
class Leverancier:
    """Supplier / Property Owner (Leverancier)"""
    id: Optional[int]
    naam: str
    email: Optional[str] = None
    telefoonnummer: Optional[str] = None
    iban: Optional[str] = None


@dataclass
class InhuurContract:
    """Contract between RyanRent and Supplier/Owner (Inhuur)"""
    id: Optional[int]
    property_id: int
    leverancier_id: Optional[int]
    start_date: date
    end_date: Optional[date] = None
    
    # Financials (In Dutch)
    kale_huur: float = 0.0
    servicekosten: float = 0.0
    voorschot_gwe: float = 0.0
    internet_kosten: float = 0.0
    inventaris_kosten: float = 0.0
    afval_kosten: float = 0.0
    schoonmaak_kosten: float = 0.0
    totale_huur: float = 0.0
    borg: float = 0.0
    
    contract_bestand: Optional[str] = None
    notities: Optional[str] = None

