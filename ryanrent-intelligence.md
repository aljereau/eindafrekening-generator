# RyanRent Intelligence Layer

**A Guide for Implementation**

## 🎯 Purpose

The goal of this intelligence layer is to place an **AI-powered operational assistant** on top of the RyanRent database.
This assistant can:

1. **Answer operational questions**
   (e.g. “Welke huizen lopen binnen 30 dagen af?”, “Welke boekingen missen een checkout?”)

2. **Perform actions**
   (e.g. nieuwe woning aanmaken, nieuw contract, check-in registreren)

3. **Generate documents**
   (e.g. eindafrekening PDF, uitcheckrapportage)

This turns our existing data + processes into a **single interactive interface** managed via a chatbot or automated agent.

---

## 🧠 Why This Layer?

RyanRent werkt met veel soorten data: huizen, klanten, contracten, boekingen, kostenparameters, eindafrekeningen, borgen, checkins en checkouts.

Deze data is krachtig, maar alleen als je:

* Snel vragen kunt stellen
* Direct acties kunt uitvoeren
* Automatisch documenten kunt genereren
* Overal dezelfde waarheid gebruikt

De intelligence layer koppelt dit samen in één systeem waar de gebruiker:

* informatie kan opvragen,
* processen kan starten, en
* complete rapporten kan genereren

via natuurlijke taal.

---

# 🏗 Architecture Overview

De architectuur bestaat uit drie lagen:

## 1. **Database Layer** (existing)

We gebruiken de huidige tabellen:

* **Properties:** `huizen`, `huizen_status_log`
* **Owners:** `eigenaren`, `inhuur_contracten`
* **Clients:** `klanten`
* **Rental Contracts:** `verhuur_contracten`
* **Bookings:** `boekingen`
* **Pricing Parameters:** `parameters`, `contract_regels`
* **Final Settlements:** `eindafrekeningen`
* **Additional Planned Tables:**

  * `borg_transacties`
  * `checkins`
  * `checkouts`
  * `personen`
  * `verblijven`

De database bevat alle operationele waarheid.

---

## 2. **Backend + API Layer**

This layer wraps the database into **safe, explicit functions**, such as:

* Queries
* Mutations
* Document generators

This ensures:

* no raw SQL in the chatbot
* validation
* business rules enforced
* predictable and maintainable behaviour

Backend exposes these functions as *“tools”* for the AI.

---

## 3. **Intelligence Layer (Chatbot)**

The chatbot receives a list of backend tools.
It can:

* call functions with arguments
* read output
* chain operations
* summarise results in natural language

Example workflow:

User: *“Genereer een eindafrekening voor boeking 1283.”*
Chatbot: calls `generate_eindafrekening_for_booking(booking_id=1283)`.

---

# 🔧 Tool Specification

Below is the list of recommended backend functions to build in the API.
These reflect common operational tasks at RyanRent.

## 📥 Read Tools (Queries)

### **1. `get_houses_near_contract_end`**

Return houses with rental-out contracts ending soon.

**Use cases:**

* Planning
* Finding new tenants
* Preventing leegstand

---

### **2. `get_bookings_without_checkout`**

Find bookings whose expected checkout date has passed but no checkout was registered.

**Use cases:**

* Missing uitcheckrapportages
* Follow-up tasks

---

### **3. `get_open_deposits_by_client`**

Returns deposit balance per client.

**Use cases:**

* Borgadministratie
* Eindafrekening checks

---

### **4. `get_status_overview`**

High-level operational summary.

Example outputs:

* aantal huizen
* bezetting
* contracten die bijna aflopen
* openstaande borgen
* boekingen zonder checkout

---

## ✍️ Write Tools (Mutations)

### **5. `create_house`**

Add a new house to the system.

### **6. `create_client`**

Add a new client, including margin rules.

### **7. `create_rental_contract`**

Register a new contract between RyanRent and a client.

### **8. `create_booking`**

Define the stay period for a client in a property.

### **9. `register_checkin`**

Record check-in events.

### **10. `register_checkout`**

Record checkout events, including damages and cleaning.

### **11. `register_deposit_transaction`**

Handle borg payments, refunds, and withholdings.

---

## 📄 Generator Tools (PDFs and Reports)

### **12. `generate_eindafrekening_for_booking`**

Create a complete eindafrekening:

* Insert row in `eindafrekeningen`
* Generate PDF
* Return file path + metadata

Future:

* uitcheckrapport generator
* monthly overview generator

---

# 🧭 Example Flow (End-to-end)

A typical workflow the AI should automate:

1. User:
   “Welke contracten lopen af binnen 30 dagen?”

2. Chatbot:
   Calls `get_houses_near_contract_end(days=30)`

3. User:
   “Plan een nieuwe boeking voor klant X in huis Y van 12–10 tot 04–12.”

4. Chatbot:
   Calls `create_booking({ ... })`

5. User:
   “Genereer eindafrekening voor boeking 1283.”

6. Chatbot:
   Calls `generate_eindafrekening_for_booking(booking_id=1283)`
   Returns PDF path.

This creates a fully natural and interactive operations assistant.

---

# 🚀 Development Plan (Recommended Order)

1. Implement **read tools**

   * Easiest
   * Gives immediate operational insight

2. Implement **write tools**

   * Add new houses, clients, contracts, bookings

3. Wrap existing PDF logic into **generate tools**

4. Integrate tools into chatbot

   * Use OpenAI function calling or tool API
   * Return structured JSON

5. Create a frontend

   * Optional
   * Chat + buttons for common tasks

---

# 📌 What This Achieves

Once this is done, RyanRent gets:

### ✔ A single interface for the entire operation

No more Excel hunting, no email chaos.

### ✔ Instant answers

Housing status, margins, upcoming checkouts, borgen → all on command.

### ✔ Fully automated document generation

Eindafrekeningen, rapporten, overzichtstabellen → on demand.

### ✔ Accuracy + consistency

All documents and decisions rely on the same database truth.

### ✔ A scalable foundation

---

# 📊 Architecture Diagram   
```mermaid

flowchart LR
    subgraph UserSide[User Side]
        U[User\n(Backoffice / Operations)]
        UI[Chat UI\n(Web / CLI / Tool)]
    end

    subgraph Intelligence[Intelligence Layer]
        LLM[Chatbot / LLM\n(with Tools)]
    end

    subgraph Backend[Backend / API Layer]
        API[API / Service Layer\n(Business Logic)]
        TOOLS[Tool Functions\n(Read / Write / Generate)]
    end

    subgraph DB[Database Layer]
        DBCore[(Core DB\nSQLite/Postgres)]

        subgraph CoreTables[Core Tables]
            H[huizen]
            EIG[eigenaren]
            INH[inhuur_contracten]
            KL[klanten]
            VK[verhuur_contracten]
            BK[boekingen]
            PAR[parameters]
            CR[contract_regels]
            EIN[eindafrekeningen]
        end

        subgraph ExtraTables[Operational Tables (planned)]
            BOR[borg_transacties]
            CI[checkins]
            CO[checkouts]
            PERS[personen]
            VERB[verblijven]
        end
    end

    subgraph Generators[Generators / Documents]
        GEN_EIN[PDF Generator\nEindafrekening]
        GEN_REP[Other Reports\n(Uitcheck, Overzichten)]
    end

    U --> UI
    UI --> LLM
    LLM <---> API
    API --> TOOLS
    TOOLS --> DBCore

    TOOLS --> GEN_EIN
    TOOLS --> GEN_REP
    GEN_EIN --> EIN
    GEN_EIN --> DBCore
    GEN_REP --> DBCore
    ```
    