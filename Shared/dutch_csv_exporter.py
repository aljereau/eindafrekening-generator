#!/usr/bin/env python3
"""
Dutch CSV Exporter
Converts numeric values from US format (220.5) to Dutch format (220,50)
Auto-detects numeric columns and leaves text columns untouched.

Usage:
    python dutch_csv_exporter.py input.csv output.csv
    python dutch_csv_exporter.py input.csv  # Overwrites with _nl suffix
    
Or import and use:
    from dutch_csv_exporter import export_dutch_csv
    export_dutch_csv("input.csv", "output.csv")
"""

import csv
import sys
import re
from pathlib import Path
from typing import Union


def is_numeric(value: str) -> bool:
    """Check if a string value is numeric (int or float with dot notation)"""
    if not value or value.strip() == "":
        return False
    
    # Remove common currency symbols and whitespace
    cleaned = value.strip().replace("€", "").replace("$", "").strip()
    
    # Check if it looks like a number (optionally negative, with optional decimal)
    # Pattern: optional minus, digits, optional .digits
    pattern = r'^-?\d+\.?\d*$'
    return bool(re.match(pattern, cleaned))


def to_dutch_number(value: str) -> str:
    """Convert US number format to Dutch format"""
    if not value or value.strip() == "":
        return value
    
    # Preserve currency symbols
    prefix = ""
    suffix = ""
    cleaned = value.strip()
    
    if cleaned.startswith("€"):
        prefix = "€"
        cleaned = cleaned[1:].strip()
    elif cleaned.startswith("$"):
        prefix = "$"
        cleaned = cleaned[1:].strip()
    
    if not is_numeric(cleaned):
        return value
    
    # Convert dot to comma
    # Also add thousands separator if needed (1234567.89 -> 1.234.567,89)
    try:
        num = float(cleaned)
        # Format with 2 decimal places for currency-like values
        if "." in cleaned:
            # Has decimal, preserve precision
            decimal_places = len(cleaned.split(".")[-1])
            formatted = f"{num:,.{decimal_places}f}"
        else:
            # Integer, no decimals
            formatted = f"{num:,.0f}"
        
        # Swap separators: 1,234.56 -> 1.234,56
        # Step 1: comma -> temp
        # Step 2: dot -> comma  
        # Step 3: temp -> dot
        dutch = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        return f"{prefix}{dutch}{suffix}"
    except ValueError:
        return value


def detect_numeric_columns(rows: list, headers: list = None, sample_size: int = 10) -> set:
    """
    Detect which columns are numeric by sampling rows.
    A column is numeric if >80% of non-empty values are numbers.
    
    Excludes columns that look like IDs/codes based on header names.
    """
    if not rows:
        return set()
    
    num_cols = len(rows[0])
    numeric_counts = [0] * num_cols
    total_counts = [0] * num_cols
    
    # Columns to exclude based on header name patterns (IDs, codes, etc.)
    excluded_cols = set()
    if headers:
        exclude_patterns = ['_id', 'id', 'object_id', 'house_id', 'klant_id', 'relatie_id', 
                           'contract_id', 'boeking_id', 'nr', 'nummer', 'code', 'postcode']
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            # Exact match or ends with pattern
            if header_lower in exclude_patterns or any(header_lower.endswith(p) for p in ['_id', '_nr', '_code']):
                excluded_cols.add(i)
    
    # Sample rows
    sample_rows = rows[:sample_size]
    
    for row in sample_rows:
        for i, val in enumerate(row):
            if i in excluded_cols:
                continue
            if val and val.strip():
                total_counts[i] += 1
                cleaned = val.strip().replace("€", "").replace("$", "").strip()
                # Also exclude values with leading zeros (like "0388") - these are codes
                if cleaned.startswith("0") and len(cleaned) > 1 and cleaned.isdigit():
                    continue  # Skip - this is a code like 0388
                if is_numeric(cleaned):
                    numeric_counts[i] += 1
    
    # A column is numeric if >80% of values are numbers
    numeric_cols = set()
    for i in range(num_cols):
        if i in excluded_cols:
            continue
        if total_counts[i] > 0 and (numeric_counts[i] / total_counts[i]) >= 0.8:
            numeric_cols.add(i)
    
    return numeric_cols


def export_dutch_csv(
    input_path: Union[str, Path],
    output_path: Union[str, Path] = None,
    delimiter: str = ";",  # Dutch Excel default
    force_numeric_cols: list = None
) -> str:
    """
    Convert a CSV file to Dutch number format.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV (default: input_nl.csv)
        delimiter: Output delimiter (default: ; for Dutch Excel)
        force_numeric_cols: List of column indices to force as numeric
    
    Returns:
        Path to output file
    """
    input_path = Path(input_path)
    
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_nl{input_path.suffix}"
    else:
        output_path = Path(output_path)
    
    # Read input CSV (auto-detect delimiter)
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        # Try to detect delimiter
        sample = f.read(2048)
        f.seek(0)
        
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
            reader = csv.reader(f, dialect)
        except csv.Error:
            reader = csv.reader(f, delimiter=',')
        
        rows = list(reader)
    
    if not rows:
        print(f"⚠️  Empty file: {input_path}")
        return str(output_path)
    
    # Separate header and data
    header = rows[0]
    data = rows[1:]
    
    # Detect numeric columns (pass headers for ID pattern detection)
    numeric_cols = detect_numeric_columns(data, headers=header)
    
    if force_numeric_cols:
        numeric_cols.update(force_numeric_cols)
    
    print(f"📊 Detected {len(numeric_cols)} numeric columns: {sorted(numeric_cols)}")
    
    # Convert data rows
    converted_data = []
    for row in data:
        new_row = []
        for i, val in enumerate(row):
            if i in numeric_cols:
                new_row.append(to_dutch_number(val))
            else:
                new_row.append(val)
        converted_data.append(new_row)
    
    # Write output with Dutch delimiter
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(converted_data)
    
    print(f"✅ Exported to: {output_path}")
    print(f"   Delimiter: '{delimiter}'")
    print(f"   Rows: {len(converted_data)}")
    
    return str(output_path)


def export_query_to_dutch_csv(
    db_path: str,
    query: str,
    output_path: str,
    delimiter: str = ";"
) -> str:
    """
    Run a SQL query and export results to Dutch-formatted CSV.
    
    Args:
        db_path: Path to SQLite database
        query: SQL query to run
        output_path: Path to output CSV
        delimiter: CSV delimiter (default: ; for Dutch Excel)
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(query)
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to strings
    str_rows = [[str(v) if v is not None else "" for v in row] for row in rows]
    
    # Detect numeric columns
    numeric_cols = detect_numeric_columns(str_rows)
    
    print(f"📊 Query returned {len(rows)} rows, {len(columns)} columns")
    print(f"   Numeric columns: {[columns[i] for i in sorted(numeric_cols)]}")
    
    # Convert
    converted_rows = []
    for row in str_rows:
        new_row = []
        for i, val in enumerate(row):
            if i in numeric_cols:
                new_row.append(to_dutch_number(val))
            else:
                new_row.append(val)
        converted_rows.append(new_row)
    
    # Write
    output_path = Path(output_path)
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(columns)
        writer.writerows(converted_rows)
    
    print(f"✅ Exported to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print("  python dutch_csv_exporter.py export.csv")
        print("  python dutch_csv_exporter.py export.csv output_dutch.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_dutch_csv(input_file, output_file)
