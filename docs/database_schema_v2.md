# RyanRent Database v2 Schema

## Overzicht
- **11 Tabellen** voor data opslag
- **3 Views** voor berekende/samengevoegde data
- **Locatie**: `database/ryanrent_v2.db`

---

## Data Flow
```
configuratie ─────────────────────────────────┐
                                              ▼
klanten ─── verhuur_contracten ─── bookings ──┬── damages
                    │                         ├── gwe_usage
houses ─────────────┘                         └── schoonmaak

inventaris ──── v_inventaris_prijzen (pulls marge from configuratie)
```

---

## Tabellen

### Basis Data
| Tabel | Rows | Omschrijving |
|-------|------|--------------|
| **klanten** | 375 | Huurders (naam, contact, marge_max) |
| **leveranciers** | 507 | Eigenaren/suppliers |
| **houses** | 473 | Huizen + defaults (borg, voorschot_gwe) |
| **configuratie** | 16 | Business settings (marges, PPPW tarieven) |

### Producten & Diensten
| Tabel | Rows | Omschrijving |
|-------|------|--------------|
| **inventaris** | 64 | Producten (inkoop_prijs, marge_override) |
| **diensten** | 4 | Services (schoonmaak €35/u, TD €45/u, etc.) |

### Transactie Data
| Tabel | Rows | Omschrijving |
|-------|------|--------------|
| **verhuur_contracten** | 0 | Contract: klant + huis + servicekosten |
| **bookings** | 0 | Uitvoering: checkin/out, voorschotten |
| **damages** | 0 | Schade per booking |
| **gwe_usage** | 0 | Meterstanden per booking |
| **schoonmaak** | 0 | Schoonmaakkosten per booking |

---

## Views (Berekende Data)

### v_inventaris_prijzen
Pullt marge uit configuratie, berekent verkoop_prijs
```sql
verkoop_prijs = inkoop_prijs / (1 - marge)
```

### v_booking_complete
Combineert booking met klant, huis, contract. Resolved defaults:
```sql
borg = COALESCE(booking.borg_betaald, contract.borg_override, house.borg_standaard)
```

### v_eindafrekening
Booking complete + totalen:
- `total_damages_incl`
- `total_gwe_incl`
- `total_schoonmaak`

---

## Configuratie Keys
| Key | Value | Omschrijving |
|-----|-------|--------------|
| marge_inventaris_standaard | 0.30 | 30% marge producten |
| marge_tradiro_max | 0.08 | Max 8% Tradiro |
| meubilering_pppw | 15.00 | €15/persoon/week |
| schoonmaak_basis | 250.00 | Basis pakket |
| schoonmaak_intensief | 375.00 | Intensief pakket |
