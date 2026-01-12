# RyanRent Database v2 Schema

> **Updated:** 2026-01-12

## Overzicht
- **12 Tabellen** voor data opslag
- **8 Views** voor berekende/samengevoegde data
- **Locatie:** `database/ryanrent_v2.db`

---

## Data Flow
```
relaties ─────┬── verhuur_contracten ─── boekingen ──┬── schades
              │           │                          ├── gwe_regels
              └── inhuur_contracten                  └── schoonmaak
                          │
huizen ─────────────────┬─┘
                        └── gwe_tarieven

inventaris ──── v_inventaris_prijzen (pulls marge from configuratie)
```

---

## Tabellen

### relaties (961 rows)
Single source of truth voor alle relaties (klanten, leveranciers, eigenaren).

| Kolom | Type | Omschrijving |
|-------|------|--------------|
| id | INTEGER PK | |
| naam | TEXT | |
| type | TEXT | particulier, bedrijf |
| contactpersoon | TEXT | |
| email | TEXT | |
| telefoonnummer | TEXT | |
| adres, postcode, plaats, land | TEXT | |
| is_klant | INTEGER | 0/1 flag |
| is_leverancier | INTEGER | 0/1 flag |
| is_eigenaar | INTEGER | 0/1 flag |
| marge_max | REAL | Max marge voor klant |

### huizen (473 rows)
| Kolom | Type | Omschrijving |
|-------|------|--------------|
| id | INTEGER PK | |
| object_id | TEXT UNIQUE | Business identifier (0345) |
| adres, postcode, plaats | TEXT | |
| capaciteit_personen | INTEGER | Max personen |
| aantal_slaapkamers | INTEGER | |
| woning_type | TEXT | Appartement, Vakantiepark |
| borg_standaard | REAL | Default borg |
| voorschot_gwe_standaard | REAL | Default GWE voorschot |
| meterbeheerder | TEXT | Enexis, Stedin |
| gwe_leverancier | TEXT | Vattenfall, Engie |
| kluis_code_1, kluis_code_2 | TEXT | |

### verhuur_contracten (0 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| relatie_id | INTEGER | → relaties |
| house_id | INTEGER | → huizen |
| start_date, end_date | DATE | |
| huur_excl_btw | REAL | |
| voorschot_gwe_excl_btw | REAL | |
| borg_override | REAL | Override default |
| incl_stoffering | INTEGER | 0/1 |
| incl_meubilering | INTEGER | 0/1 |
| schoonmaak_pakket | TEXT | basis/intensief |

### inhuur_contracten (509 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| house_id | INTEGER | → huizen |
| relatie_id | INTEGER | → relaties (eigenaar) |
| inhuur_excl_btw | REAL | |
| vve_kosten | REAL | |
| borg | REAL | |
| start_datum, eind_datum | DATE | |

### boekingen (0 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| contract_id | INTEGER | → verhuur_contracten |
| checkin, checkout | DATE | |
| borg_betaald | REAL | Override |
| elektra_begin, elektra_eind | REAL | Meterstanden |
| gas_begin, gas_eind | REAL | |
| water_begin, water_eind | REAL | |

### gwe_regels (0 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| booking_id | INTEGER | → boekingen |
| type | TEXT | Water, Gas, Elektra |
| omschrijving | TEXT | levering, vastrecht, etc |
| tarief | REAL | |
| eenheid | TEXT | m³, kWh, dag |
| btw_pct | REAL | |

### schades (0 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| booking_id | INTEGER | → boekingen |
| omschrijving | TEXT | |
| aantal, tarief, kosten | REAL | |
| btw_pct | REAL | |

### schoonmaak (0 rows)
| Kolom | Type | FK |
|-------|------|-----|
| id | INTEGER PK | |
| booking_id | INTEGER | → boekingen |
| kosten | REAL | |
| notities | TEXT | |

### configuratie (16 rows)
Business settings (marges, PPPW tarieven).

### diensten (4 rows)
Services (schoonmaak €35/u, technisch €45/u).

### inventaris (64 rows)
Producten met inkoop_prijs, marge_override.

### gwe_tarieven (4 rows)
Standaard water tarieven (PWN).

---

## Views

| View | Omschrijving |
|------|--------------|
| v_boekingen_compleet | Boeking + klant + huis + meterstanden |
| v_eindafrekening | Boeking + totalen (schades, GWE, schoonmaak) |
| v_gwe_regels_compleet | GWE regels met auto-berekende kosten |
| v_inhuur_compleet | Inhuur contract + eigenaar + huis details |
| v_inventaris_prijzen | Producten + berekende verkoop_prijs |
| v_schades_compleet | Schades + klant + huis context |
| v_schoonmaak_compleet | Schoonmaak + klant + huis context |
