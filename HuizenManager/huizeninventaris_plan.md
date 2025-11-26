# Huizeninventaris (House Inventory) System Plan

## 1. Goal
Create a robust, historical database for the "Huizeninventaris" that serves as the single source of truth for the fleet.
**Key Objectives:**
- Track current fleet status (Active/Inactive).
- Maintain historical data (rent prices, owners) so old reports remain accurate.
- Separate "Physical House Data" from "Operational/Financial Data".
- Provide tools to Add, Update, and View houses.

## 2. Analysis of Current Data
Based on the provided input and recent schema updates, the current data includes a mix of:
- **Physical Attributes**: Address, Type, Surface Area, Bedrooms, Object ID.
- **Operational Info**: Key #, In Fleet?, Status.
- **Financial/Owner Info**: Owner Name, Phone, Kale Inhuurprijs, Voorschot GWE, Internet Costs, etc.

**Problem**: Storing financial data (like `base_rent_price`) directly on the `properties` table means we lose history when the price changes. If we update the price today, a report generated for last year might be incorrect if it pulls the "current" price.

## 3. Proposed Data Architecture

We will split the data into two main concepts (tables):

### A. `properties` (The Physical House)
*Static attributes that rarely change.*
- `id` (PK)
- `object_id` (e.g., "0001")
- `address` (Street + Number)
- `postal_code`
- `city`
- `property_type` (Type woning)
- `surface_area` (Oppervlakte)
- `bedrooms` (Aantal Slaapkamers)
- `capacity` (Personen bezetting)

### B. `owners` (New)
*Landlords who own the properties.*
- `id` (PK)
- `name` (Eigenaar)
- `email`
- `phone` (Telefoonnummer)
- `iban`

### C. `inhuur_contracts` (Financial & Owner History)
*Time-bound agreements where RyanRent rents FROM the owner.*
- `id` (PK)
- `property_id` (FK to properties)
- `owner_id` (FK to owners)
- `start_date`
- `end_date` (NULL = Current)
- `contract_file` (Path to PDF)
- **Financials (Costs for RyanRent):**
    - `base_rent` (Kale Inhuurprijs)
    - `service_costs` (Servicekosten)
    - `gwe_advance` (Voorschot GWE)
    - `internet_costs` (Inhuur Internet)
    - `inventory_costs` (Inhuur Inventaris)
    - `waste_costs` (Inhuur Afval)
    - `cleaning_costs` (Inhuur Schoonmaak - if applicable)
    - `total_rent` (Total monthly cost)

### D. `fleet_status_log` (Optional but recommended)
*Tracks when a house enters or leaves the fleet.*
- `property_id`
- `status` (Active/Inactive/Maintenance)
- `date_changed`
- `reason`

## 4. Implementation Steps

### Phase 1: Database Refactoring
1.  Create `owner_contracts` table.
2.  Migrate existing financial columns from `properties` to `owner_contracts` (creating an initial "current" contract for each house).
3.  Remove financial columns from `properties` to clean it up.

### Phase 2: Application Logic (The "Sub App")
Create a Python module `checkin_manager` (or `huizen_manager`) to handle:
1.  **Add House**: Wizard to input physical details + initial owner contract.
2.  **Update House**:
    - If physical info changes (e.g., renovation): Update `properties`.
    - If financial info changes (e.g., rent increase): Close current `owner_contract` (set end_date) and create a new one.
3.  **Get House at Date**: Function to retrieve house details + the specific contract active at a given date (crucial for historical reports).

### Phase 3: Data Import/Cleanup
1.  Script to import the "Single Row" Excel data into this new structure.
2.  Validation to ensure no duplicate Object IDs.

## 5. Questions for User
- Does "Inhuur" (Hiring in) refer to what RyanRent pays the owner? (Assumed Yes).
- Do we need to track *who* the tenant is in this system, or is that handled by the `contracts` table (Client <-> Property)? (Assumed `contracts` table handles Tenants).
