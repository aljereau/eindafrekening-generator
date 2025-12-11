# Complex Test Questions for RyanRent Bot

These questions are designed to test the bot's ability to handle multi-step logic, complex filtering, SQL generation, and financial analysis.

## 🔍 Complex Filtering & Availability
1. **"How many houses have a checkout in the coming 3 months which I could rent for between €3000 and €4000?"**
   * *Tests: Date range logic, Price range filtering, JOIN between houses and bookings.*
2. **"List all houses that are currently empty (no active booking) but have a 'kale huur' (base rent) lower than €1500."**
   * *Tests: Vacancy logic (NOT EXISTS or filtering on current date vs booking range), Price optimization.*
3. **"Which properties with more than 3 bedrooms will become available in December?"**
   * *Tests: Attribute filtering (bedrooms) combined with future date availability.*

## 💰 Financial Analysis & Margins
4. **"Show me the top 5 houses with the lowest profit margin (difference between current rent and minimum price)."**
   * *Tests: Calculation logic (`v_house_costs` view usage), Sorting, Limiting results.*
5. **"What is the total projected revenue from 'kale huur' for all active contracts in the next 30 days?"**
   * *Tests: Aggregation (SUM), Date filtering.*
6. **"Are there any houses where the 'servicekosten' are higher than 15% of the 'kale huur'?"**
   * *Tests: Relative value comparison / Arithmetic in SQL.*

## 🛠️ Operational & Scheduling
7. **"Which houses have a checkout scheduled in the next 14 days but NO pre-inspection (voorinspectie) planned yet?"**
   * *Tests: Exclusion logic (LEFT JOIN ... WHERE NULL), Planning awareness.*
8. **"List all the owners (eigenaars) who have more than 2 houses ending their contracts this year."**
   * *Tests: Grouping (GROUP BY having count > 2), Relationship traversal.*
9. **"Show me a schedule of all 'Eindinspecties' for next week, ordered by date, including the address and client name."**
   * *Tests: Joining multiple tables (Inspecties -> Huizen, Inspecties -> Klanten), Ordering.*

## 🧠 Multi-Step / Logic
10. **"I want to find a replacement tenant for the 'Keizersgracht' property. Who was the previous tenant before the current one, and what did they pay?"**
    * *Tests: History traversal, specific item lookup, past data retrieval.*
11. **"Identify any potential bottlenecks for next month: specifically days where we have more than 3 checkouts or inspections scheduled."**
    * *Tests: Aggregation by date, Threshold filtering, Operational capacity planning.*
