Here you go — a **complete, polished, zero-missing-pieces `.md` guide** written specifically for your AI Builder.
It explains:

* the purpose of the one-pager
* the logic behind the structure
* what needs to be added
* what must be changed
* what is required for correct wording
* where each piece of data belongs
* the difference between verblijfsperiode & rapporteringsperiode
* exactly how the template should be updated
* the UX principles
* the mapping logic
* the expected output

This is a **production-grade guide**.

---

# 📘 **RyanRent – One-Pager Redesign & Implementation Guide**

### *Technical + UX Specification for AI Builder / Developers*

---

## ## 1. **Purpose of This Document**

This document gives the AI Builder everything needed to:

* understand the **goal** of the new eindoverzicht one-pager
* understand the **context** of how RyanRent handles eindafrekeningen
* fully upgrade the **template, structure, captions, logic, and text**
* implement the new JSON-driven text and data mapping
* fix missing information (periods, meterstand summaries, etc.)
* ensure all scenarios (refund, extra, perfect fit, under use, over use) work visually
* understand what needs to change in the existing template and output

This guide is meant to be **complete**, so the builder can implement the new system without needing back-and-forth clarifications.

---

# ## 2. **What the One-Pager Is**

The RyanRent “Eindoverzicht Verblijf” is a **client-facing summary** that shows:

* what the tenant **paid upfront** (voorschotten)
* what was **actually used** during their stay
* the **net result** (refund or extra payment)
* simple **visual bars** showing usage vs pot
* a short, human summary per component
* a clear **top-level result** (nothing, refund, or pay extra)

It is **not** the technical breakdown.
It is a **clear and friendly summary**.

The full technical details are shown in the **detail PDF**, not here.

---

# ## 3. **Why It Needs an Upgrade**

The current version is missing:

* clear explanation text
* meterstand summaries
* rapporteringsperiode for G/W/E
* correct placement of date ranges
* improved copywriting
* better captioning
* better hierarchy
* correct wording for schoonmaak
* disambiguation between stay period & supplier period
* consistency in layout
* a top-level net result
* micro-captions to reduce client confusion
* improved wording logic for all scenarios

This document fixes those gaps and describes the updates needed.

---

# ## 4. **Two Different Periods (Critical)**

The builder must understand that two **different date ranges** appear in the output.

### ### 4.1. Verblijfsperiode (Stay period)

**This belongs at the TOP of the document.**

Example:

```
01-08-2024 t/m 15-08-2024 (14 dagen)
```

It identifies the actual stay being settled.

### ### 4.2. Rapporteringsperiode (Reporting period)

**This belongs ONLY inside the G/W/E specification section**, never in the header.

Example:

```
Rapporteringsperiode G/W/E:
01-01-2024 t/m 01-01-2025
```

Reason:
G/W/E may follow yearly supplier cycles that do not match the stay period.

This distinction is crucial for clarity.

---

# ## 5. **Updated One-Pager Structure (MANDATORY)**

The one-pager must follow this exact order:

---

## **1. Header**

* Title
* Object address
* Unit
* Opdrachtgever
* Verblijfsperiode
* Intro text explaining purpose of document

---

## **2. Net Result Section**

A clear summary of the financial result.

Examples:

**Neutral:**

> Netto resultaat: €0
> U betaalt niets bij en ontvangt niets terug.

**Refund:**

> Netto resultaat: +€200
> U ontvangt dit bedrag retour.

**Extra:**

> Netto resultaat: -€125
> U betaalt dit bedrag bij.

This must be placed **directly below the header**.

---

## **3. Start – Betaalde Voorschotten**

Shows what the user paid at the beginning.

Includes:

* Borg
* Schoonmaak pakket
* G/W/E voorschot
* Captions explaining what each item represents

---

## **4. Verblijf – Gebruik**

Shows what was used during the stay.

Includes:

* Bars showing pot vs usage
* Text templates (perfect fit / refund / extra)
* Schoonmaak: included hours & extra hours
* G/W/E: usage & meterstand summary

---

## **5. Resultaat – Eindafrekening**

A table showing:
| Onderdeel | Voorschot | Gebruikt | Verschil |

Includes:

* Row: Borg
* Row: G/W/E
* Row: Schoonmaak
* Total line with correct labeling

---

## **6. Specificaties (Samenvatting)**

Short summaries for:

* Borg
* G/W/E (with meterstand summary + rapporteringsperiode)
* Schoonmaak

Full details appear in the **detail PDF**, not here.

---

## **7. Footer**

* Verified by: Anna (or whoever generated the report)
* Generated on
* Contact details

---

# ## 6. **Key UX Principles (Builder Must Follow)**

### **6.1. Pot must be a fixed baseline**

The pot (voorschot) bar must:

* always be the same length
* show usage inside that pot
* show refund inside remaining pot
* show overflow outside the pot

### **6.2. Captions reduce confusion**

Every section must contain short, human-friendly clarifications:

* what is this value?
* why is this here?
* how was this calculated?

### **6.3. Tone must be calm, neutral, and helpful**

Avoid:

* technical jargon
* cold language
* confusing Dutch financial terminology

Use friendly, simple explanations.

---

# ## 7. **What MUST Be Added (Critical)**

The builder must add:

* meterstand summary
* rapporteringsperiode inside G/W/E section
* intro text
* net result block
* micro-captions for borg, schoonmaak, G/W/E
* correct schoonmaak explanation
* clear indications of refund or payment
* correct scenario logic (perfect fit, refund, extra)
* wording improvements as provided in the text JSON previously

---

# ## 8. **JSON Mapping Requirements**

The builder will use a JSON-based text dictionary, containing:

* headers
* captions
* templates for all scenarios
* table labels
* footer lines

The JSON I provided earlier (**“onepager_text”**) must be used as the text source.

Templates use placeholders like:

* `{{currency}}`
* `{{pot}}`
* `{{used}}`
* `{{refund}}`
* `{{extra}}`
* `{{power_start}}`
* `{{power_end}}`
* `{{gas_start}}`
* `{{gas_end}}`
* etc.

The builder must implement logic to choose correct templates based on scenario.

---

# ## 9. **Technical Implementation Summary**

### **9.1. The builder must:**

* update the HTML template
* insert new sections and captions
* integrate JSON text mappings
* use placeholders for all dynamic values
* ensure correct logic branching for scenarios
* add placement for meterstanden
* add placement for rapporteringsperiode
* ensure the pot-bar uses correct flex/ratio logic
* ensure headings follow order defined above

### **9.2. No wording should be hardcoded in HTML**

All sentences must come from the JSON dictionary.

---

# ## 10. **Expected Output Quality**

The final output must:

* be clean
* be client-friendly
* read naturally
* follow the correct hierarchy
* avoid confusion
* accurately represent usage and results
* pass internal & client audits
* answer questions before they arise

This is not just a PDF — it is an important trust-building component.

---

# ## 11. **Ready for Next Steps**

Once the builder implements:

* the updated HTML structure
* the JSON mapping
* the improved copy
* the bar logic
* the period placement

The new one-pager will be ready for production.

If needed, I can also generate:

* the **full HTML template**,
* the **full JSON for detail PDF**,
* or the **bar component HTML/CSS**.

Just tell me.
