---
description: Manage inspections by exporting upcoming inspections to Excel or importing planned inspections from Excel.
---
1. If the user wants to **export** or **generate** a planning list:
   ```bash
   python3 workflows/manage_inspections.py export
   ```

2. If the user wants to **import** or **process** a filled Excel file:
   - Ask for the filename if not provided.
   - Run the import command (dry run first):
     ```bash
     python3 workflows/manage_inspections.py import [filename]
     ```
   - If the dry run looks good and user approves, run with commit:
     ```bash
     python3 workflows/manage_inspections.py import [filename] --commit
     ```
