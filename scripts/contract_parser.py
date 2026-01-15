#!/usr/bin/env python3
"""
Contract Parser for RyanRent IHOVK/VHOVK contracts.
Extracts structured data from PDF rental agreements.
"""

import re
import os
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import json

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pdfplumber', '-q'])
    import pdfplumber

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("OCR not available. Install with: pip install pytesseract pdf2image pillow")


@dataclass
class ContractData:
    """Extracted contract data"""
    # Source
    filename: str
    has_text: bool = False
    
    # Property
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    
    # Verhuurder (eigenaar in old contracts)
    verhuurder_naam: Optional[str] = None
    verhuurder_kvk: Optional[str] = None
    verhuurder_adres: Optional[str] = None
    verhuurder_email: Optional[str] = None
    verhuurder_telefoon: Optional[str] = None
    verhuurder_iban: Optional[str] = None
    
    # Huurder (Tradiro in old contracts)
    huurder_naam: Optional[str] = None
    huurder_kvk: Optional[str] = None
    
    # Contract terms
    contract_type: Optional[str] = None  # bepaald/onbepaald
    ingangsdatum: Optional[str] = None
    einddatum: Optional[str] = None
    minimum_duur: Optional[str] = None
    opzegtermijn: Optional[str] = None
    
    # Pricing
    huurprijs_excl_btw: Optional[float] = None
    huurprijs_incl_btw: Optional[float] = None
    borg: Optional[float] = None
    voorschot_gwe: Optional[float] = None
    servicekosten: Optional[float] = None
    
    # Parsing info
    raw_text_preview: Optional[str] = None


class ContractParser:
    """Parser for rental contract PDFs"""
    
    # Regex patterns
    PATTERNS = {
        # Formal contract patterns
        'bedrijfsnaam': r'Bedrijfsnaam\s*:\s*(.+?)(?:\n|$)',
        'kvk': r'(?:Kvk-nummer|KvK|KVK|KvKnr|KvKor)\s*[:\s]\s*(\d{8})',
        'adres_kantoor': r'Kantooradres\s*:\s*(.+?)(?:\n|$)',
        'postcode_plaats': r'Postcode en plaats\s*:\s*(\d{4}\s*[A-Z]{2})\s*(?:te\s+)?(.+?)(?:\n|$)',
        'telefoon': r'(?:Telefoonnummer|Tel)\s*:\s*([0-9\s\-]+)',
        'email': r'(?:E-mail|e-mail)\s*:\s*([^\n\s]+)',
        'iban': r'(?:IBAN|IBAN NR\.?)\s*[:\s]\s*([A-Z]{2}\d{2}[A-Z0-9\s]+)',
        
        # Letter/informal patterns - company name at top
        'company_header': r'^([A-Z][A-Za-z\s&\.\-]+(?:BV|B\.V\.|NV|N\.V\.|Holding|Services|Rentals))\s*(?:KvK|$)',
        'personal_name': r'^(?:Dhr\.|Mevr\.|De heer|Mevrouw)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        
        # Address patterns
        'gehuurde_adres': r'plaatselijk bekend\s+(.+?),\s*(\d{4}\s*[A-Z]{2})\s*(?:te\s+)?([^\.\n]+)',
        'adres_als': r'als\s+(?:appartement aan de\s+)?([^,\n]+)',
        
        # Pricing - multiple patterns for flexibility
        'huurprijs': r'(?:huurprijs|huur|nieuwe huurprijs)\s*(?:per maand)?\s*(?:is\s+)?(?:daardoor\s+)?[€:]?\s*([\d\.,]+)(?:\s*euro)?',
        'huurprijs_eur': r'€\s*([\d\.,]+)',
        'borg': r'(?:borg|waarborgsom|waarborg)\s*[€:]?\s*([\d\.,]+)',
        
        # Contract terms
        'onbepaalde_tijd': r'onbepaalde tijd',
        'bepaalde_tijd': r'bepaalde tijd',
        'minimum_duur': r'minimum(?:\s+duur)?\s+tot\s+en\s+met\s+(\d{2}-\d{2}-\d{4})',
        'ingangsdatum': r'(?:ingang(?:s)?datum|per|vanaf)\s+(\d{1,2}[-/\s](?:\d{1,2}|januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)[-/\s]\d{4})',
    }
    
    def __init__(self):
        pass
    
    def extract_text(self, pdf_path: str, use_ocr: bool = True) -> tuple[str, bool]:
        """Extract text from PDF, returns (text, has_text). Uses OCR fallback for scanned PDFs."""
        try:
            # First try pdfplumber (fast, for digital PDFs)
            with pdfplumber.open(pdf_path) as pdf:
                texts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
                
                full_text = '\n'.join(texts)
                has_text = len(full_text.strip()) > 100
                
                if has_text:
                    return full_text, True
            
            # If no text and OCR available, use OCR
            if use_ocr and HAS_OCR:
                print(f"      Using OCR...")
                return self.extract_text_ocr(pdf_path)
            
            return "", False
        except Exception as e:
            print(f"Error extracting {pdf_path}: {e}")
            return "", False
    
    def extract_text_ocr(self, pdf_path: str) -> tuple[str, bool]:
        """Extract text from scanned PDF using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=5)
            
            texts = []
            for i, image in enumerate(images):
                # Run OCR on each page
                text = pytesseract.image_to_string(image, lang='nld+eng')
                if text.strip():
                    texts.append(text)
            
            full_text = '\n'.join(texts)
            has_text = len(full_text.strip()) > 100
            return full_text, has_text
        except Exception as e:
            print(f"OCR error: {e}")
            return "", False
    
    def parse_money(self, value: str) -> Optional[float]:
        """Parse money string to float"""
        if not value:
            return None
        # Remove € and spaces, handle Dutch format
        value = re.sub(r'[€\s]', '', value)
        value = value.replace('.', '').replace(',', '.')
        try:
            return float(value)
        except:
            return None
    
    def find_pattern(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """Find pattern in text, return group"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(group).strip()
        return None
    
    def parse_contract(self, pdf_path: str) -> ContractData:
        """Parse a contract PDF and extract data"""
        filename = os.path.basename(pdf_path)
        text, has_text = self.extract_text(pdf_path)
        
        data = ContractData(
            filename=filename,
            has_text=has_text,
            raw_text_preview=text[:500] if text else None
        )
        
        if not has_text:
            return data
        
        # Split text to find verhuurder (first) and huurder (second) sections
        # Usually format is: verhuurder info... "hierna te noemen 'verhuurder'" ... huurder info...
        
        verhuurder_section = ""
        huurder_section = ""
        
        parts = re.split(r"hierna te noemen ['\"]?(?:verhuurder|huurder)['\"]?", text, flags=re.IGNORECASE)
        if len(parts) >= 2:
            verhuurder_section = parts[0]
            huurder_section = parts[1] if len(parts) > 1 else ""
        else:
            verhuurder_section = text[:2000]
            huurder_section = text[1000:3000]
        
        # Extract verhuurder (eigenaar) info
        # Try formal patterns first
        data.verhuurder_naam = self.find_pattern(verhuurder_section, self.PATTERNS['bedrijfsnaam'])
        
        # Fallback: try company header pattern (for letters)
        if not data.verhuurder_naam:
            data.verhuurder_naam = self.find_pattern(text[:500], self.PATTERNS['company_header'])
        
        # Fallback: try personal name pattern
        if not data.verhuurder_naam:
            data.verhuurder_naam = self.find_pattern(text[:500], self.PATTERNS['personal_name'])
        
        data.verhuurder_kvk = self.find_pattern(text[:1000], self.PATTERNS['kvk'])  # Search in first 1000 chars
        data.verhuurder_adres = self.find_pattern(verhuurder_section, self.PATTERNS['adres_kantoor'])
        data.verhuurder_email = self.find_pattern(text[:1000], self.PATTERNS['email'])
        data.verhuurder_telefoon = self.find_pattern(text[:1000], self.PATTERNS['telefoon'])
        
        # IBAN - search full text, try to get first one (likely verhuurder)
        iban_matches = re.findall(self.PATTERNS['iban'], text, re.IGNORECASE)
        if iban_matches:
            # Filter out Tradiro/RyanRent IBANs
            for iban in iban_matches:
                iban_clean = iban.strip()
                if 'tradiro' not in text[max(0, text.find(iban_clean)-50):text.find(iban_clean)+50].lower():
                    data.verhuurder_iban = iban_clean
                    break
            if not data.verhuurder_iban and iban_matches:
                data.verhuurder_iban = iban_matches[0].strip()
        
        # Extract huurder info
        data.huurder_naam = self.find_pattern(huurder_section, self.PATTERNS['bedrijfsnaam'])
        data.huurder_kvk = self.find_pattern(huurder_section, self.PATTERNS['kvk'])
        
        # Extract property address
        match = re.search(self.PATTERNS['gehuurde_adres'], text, re.IGNORECASE)
        if match:
            data.adres = match.group(1).strip()
            data.postcode = match.group(2).strip()
            data.plaats = match.group(3).strip()
        
        # Fallback: try "als" pattern
        if not data.adres:
            adres_als = self.find_pattern(text, self.PATTERNS['adres_als'])
            if adres_als:
                data.adres = adres_als
        
        # Contract type
        if re.search(self.PATTERNS['onbepaalde_tijd'], text, re.IGNORECASE):
            data.contract_type = 'onbepaalde_tijd'
        elif re.search(self.PATTERNS['bepaalde_tijd'], text, re.IGNORECASE):
            data.contract_type = 'bepaalde_tijd'
        
        # Dates
        data.minimum_duur = self.find_pattern(text, self.PATTERNS['minimum_duur'])
        data.ingangsdatum = self.find_pattern(text, self.PATTERNS['ingangsdatum'])
        
        # Pricing - search in full text
        huurprijs_match = self.find_pattern(text, self.PATTERNS['huurprijs'])
        if huurprijs_match:
            data.huurprijs_excl_btw = self.parse_money(huurprijs_match)
        
        borg_match = self.find_pattern(text, self.PATTERNS['borg'])
        if borg_match:
            data.borg = self.parse_money(borg_match)
        
        return data
    
    def parse_folder(self, folder_path: str, output_csv: str = None) -> List[ContractData]:
        """Parse all PDFs in a folder"""
        results = []
        
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files")
        
        for i, filename in enumerate(pdf_files):
            pdf_path = os.path.join(folder_path, filename)
            print(f"[{i+1}/{len(pdf_files)}] Parsing {filename}...")
            
            try:
                data = self.parse_contract(pdf_path)
                results.append(data)
                
                if data.has_text:
                    print(f"   ✓ Verhuurder: {data.verhuurder_naam or 'N/A'}")
                    print(f"   ✓ Adres: {data.adres or 'N/A'}")
                else:
                    print(f"   ✗ No extractable text (scanned PDF)")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        if output_csv:
            self._save_csv(results, output_csv)
        
        return results
    
    def _save_csv(self, results: List[ContractData], output_path: str):
        """Save results to CSV"""
        import csv
        
        if not results:
            return
        
        fieldnames = list(asdict(results[0]).keys())
        fieldnames.remove('raw_text_preview')  # Don't include in CSV
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for data in results:
                row = asdict(data)
                del row['raw_text_preview']
                writer.writerow(row)
        
        print(f"\n✅ Saved results to {output_path}")


if __name__ == '__main__':
    import sys
    
    parser = ContractParser()
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            output = sys.argv[2] if len(sys.argv) > 2 else 'contract_parsed.csv'
            parser.parse_folder(path, output)
        else:
            data = parser.parse_contract(path)
            print(json.dumps(asdict(data), indent=2, default=str))
    else:
        print("Usage: python contract_parser.py <pdf_path_or_folder> [output.csv]")
