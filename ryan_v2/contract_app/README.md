# Contract Application Module

This module handles the extraction, parsing, and template management for RyanRent rental contracts.

## Folder Structure

*   **`src/`**: Core application logic.
    *   `parse_contract.py`: Logic to extract data (dates, amounts) from contract text.
*   **`templates/`**:
    *   `contract_template.md`: The master Markdown template for generating new contracts.
*   **`scripts/`**: Analysis tools.
    *   `analyze_pdf.py`: Extract raw text from PDF contracts.
    *   `analyze_docx.py`: Extract raw text from DOCX files.
*   **`data/`**: Raw text dumps used for testing and validation.

## Usage

**To run the parser:**
```bash
python3 src/parse_contract.py ../data/contract_text.txt
```

**To use the template:**
Copy `templates/contract_template.md` and replace the `[PLACEHOLDERS]` with actual client data.
