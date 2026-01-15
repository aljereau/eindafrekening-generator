#!/usr/bin/env python3
"""
Batch Contract Parser for RyanRent
Parses all inhuur/verhuur contracts from the Woningen folder structure
and compares extracted data to database values.
"""

import os
import json
import csv
import re
import sqlite3
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path

# OCR dependencies
import pytesseract
from pdf2image import convert_from_path

# LLM
from openai import OpenAI

WONINGEN_PATH = "/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/01_Woningen"
DB_PATH = "database/ryanrent_v2.db"


@dataclass
class ContractExtraction:
    """Comprehensive extraction schema for both inhuur and verhuur contracts"""
    # Source
    filepath: str
    filename: str
    object_id: Optional[str] = None
    contract_type_detected: Optional[str] = None  # inhuur / verhuur
    
    # Woning
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    
    # Verhuurder/Eigenaar (for INHUUR: who RyanRent rents FROM)
    verhuurder_naam: Optional[str] = None
    verhuurder_type: Optional[str] = None
    verhuurder_kvk: Optional[str] = None
    verhuurder_iban: Optional[str] = None
    verhuurder_email: Optional[str] = None
    verhuurder_telefoon: Optional[str] = None
    verhuurder_adres: Optional[str] = None
    verhuurder_postcode: Optional[str] = None
    verhuurder_plaats: Optional[str] = None
    
    # Huurder (for VERHUUR: who RyanRent rents TO)
    huurder_naam: Optional[str] = None
    huurder_type: Optional[str] = None  # particulier / bedrijf
    huurder_kvk: Optional[str] = None
    huurder_contactpersoon: Optional[str] = None
    huurder_email: Optional[str] = None
    huurder_telefoon: Optional[str] = None
    huurder_adres: Optional[str] = None
    
    # Contract terms
    contract_duur: Optional[str] = None  # bepaalde_tijd / onbepaalde_tijd
    start_datum: Optional[str] = None
    eind_datum: Optional[str] = None
    minimale_duur_maanden: Optional[int] = None
    opzegtermijn_maanden: Optional[int] = None
    
    # Pricing
    huurprijs_excl_btw: Optional[float] = None
    huurprijs_incl_btw: Optional[float] = None
    btw_percentage: Optional[float] = None
    borg: Optional[float] = None
    voorschot_gwe: Optional[float] = None
    vve_kosten: Optional[float] = None
    servicekosten: Optional[float] = None
    eindschoonmaak_kosten: Optional[float] = None
    
    # Indexering (rent increase)
    indexering_type: Optional[str] = None  # CPI / CBS / vast_percentage / geen
    indexering_percentage: Optional[float] = None
    indexering_datum: Optional[str] = None  # yearly date when indexation applies
    
    # Betaling
    betalingswijze: Optional[str] = None  # machtiging / overboeking / incasso
    betaaldatum: Optional[int] = None  # dag van de maand
    
    # Services included
    incl_stoffering: Optional[bool] = None
    incl_meubilering: Optional[bool] = None
    incl_internet: Optional[bool] = None
    incl_schoonmaak: Optional[bool] = None
    incl_bedlinnen: Optional[bool] = None
    incl_tuinonderhoud: Optional[bool] = None
    incl_eindschoonmaak: Optional[bool] = None
    
    # GWE responsibility
    gwe_verantwoordelijk: Optional[str] = None  # verhuurder / huurder / ryanrent
    elektra_verantwoordelijk: Optional[str] = None
    gas_verantwoordelijk: Optional[str] = None
    water_verantwoordelijk: Optional[str] = None
    
    # Meta
    extraction_confidence: Optional[float] = None
    llm_tokens_used: Optional[int] = None
    llm_cost_usd: Optional[float] = None


EXTRACTION_PROMPT = """You are extracting data from a Dutch rental contract (huurovereenkomst/inhuurovereenkomst).

Extract ALL of the following fields. Return ONLY valid JSON:

{
  "adres": "property street address",
  "postcode": "Dutch postcode like 3332 GB",
  "plaats": "city name",
  
  "verhuurder_naam": "landlord/owner name (company or person)",
  "verhuurder_type": "particulier or bedrijf",
  "verhuurder_kvk": "8-digit KvK number if company",
  "verhuurder_iban": "bank account IBAN",
  "verhuurder_email": "email address",
  "verhuurder_telefoon": "phone number",
  "verhuurder_adres": "landlord's address",
  "verhuurder_postcode": "landlord's postcode",
  "verhuurder_plaats": "landlord's city",
  
  "huurder_naam": "tenant name (company or person)",
  "huurder_type": "particulier or bedrijf",
  "huurder_kvk": "tenant KvK if company",
  "huurder_contactpersoon": "contact person name at tenant company",
  "huurder_email": "tenant email",
  "huurder_telefoon": "tenant phone",
  "huurder_adres": "tenant address",
  
  "contract_duur": "bepaalde_tijd or onbepaalde_tijd",
  "start_datum": "start date as DD-MM-YYYY",
  "eind_datum": "end date as DD-MM-YYYY or null",
  "minimale_duur_maanden": "minimum duration in months",
  "opzegtermijn_maanden": "notice period in months",
  
  "huurprijs_excl_btw": "monthly rent excluding BTW as number",
  "huurprijs_incl_btw": "monthly rent including BTW as number",
  "btw_percentage": "BTW percentage as decimal (0.09 or 0.21)",
  "borg": "deposit/waarborgsom amount as number",
  "voorschot_gwe": "utility advance payment per month as number",
  "vve_kosten": "VvE/service charges as number",
  "servicekosten": "other service costs as number",
  "eindschoonmaak_kosten": "final cleaning costs as number",
  
  "indexering_type": "CPI or CBS or vast_percentage or geen",
  "indexering_percentage": "fixed increase percentage if applicable",
  "indexering_datum": "date when yearly indexation applies (e.g. '01-01' or '01-07')",
  
  "betalingswijze": "machtiging or overboeking or incasso",
  "betaaldatum": "day of month when rent is due (1-31)",
  
  "incl_stoffering": true/false,
  "incl_meubilering": true/false,
  "incl_internet": true/false,
  "incl_schoonmaak": true/false,
  "incl_bedlinnen": true/false,
  "incl_tuinonderhoud": true/false,
  "incl_eindschoonmaak": true/false,
  
  "gwe_verantwoordelijk": "verhuurder or huurder or ryanrent",
  "elektra_verantwoordelijk": "verhuurder or huurder",
  "gas_verantwoordelijk": "verhuurder or huurder",
  "water_verantwoordelijk": "verhuurder or huurder",
  
  "extraction_confidence": 0.0-1.0
}

IMPORTANT:
- Return null for fields not found
- Amounts should be numbers only
- Dates as DD-MM-YYYY
- For RyanRent contracts: RyanRent is usually verhuurder in verhuurcontracten, huurder in inhuurcontracten

CONTRACT TEXT:
"""


class BatchContractParser:
    """Parse all contracts from Woningen folder structure"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        
    def extract_object_id(self, folder_path: str) -> Optional[str]:
        """Extract object_id from folder name like '0001 Maasdijk 199A'"""
        folder_name = os.path.basename(folder_path)
        match = re.match(r'^(\d{4})', folder_name)
        return match.group(1) if match else None
    
    def detect_contract_type(self, filepath: str) -> str:
        """Detect if contract is inhuur or verhuur based on path"""
        if '2_Inhuur' in filepath:
            return 'inhuur'
        elif '3_Verhuur' in filepath:
            return 'verhuur'
        return 'unknown'
    
    def extract_text_ocr(self, pdf_path: str, max_pages: int = 8) -> str:
        """Extract text from PDF using OCR with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("OCR timeout")
        
        try:
            # Set 60 second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)
            
            images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=max_pages)
            texts = []
            for img in images:
                text = pytesseract.image_to_string(img, lang='nld+eng')
                if text.strip():
                    texts.append(text)
            
            signal.alarm(0)  # Cancel alarm
            return "\n".join(texts)
        except TimeoutError:
            print(f"  ⚠️ OCR timeout - skipping")
            signal.alarm(0)
            return ""
        except Exception as e:
            signal.alarm(0)
            return ""
    
    def extract_with_llm(self, text: str) -> tuple[dict, int, float]:
        """Call LLM to extract structured data"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": EXTRACTION_PROMPT + text[:12000]}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * 0.00000015 + 
                    response.usage.completion_tokens * 0.0000006)
            
            return result, tokens, cost
        except Exception as e:
            print(f"  LLM error: {e}")
            return {}, 0, 0
    
    def parse_single(self, pdf_path: str) -> ContractExtraction:
        """Parse a single contract PDF"""
        filename = os.path.basename(pdf_path)
        
        # Determine property folder (go up to find object_id)
        parts = Path(pdf_path).parts
        object_id = None
        for part in parts:
            match = re.match(r'^(\d{4})\s', part)
            if match:
                object_id = match.group(1)
                break
        
        contract_type = self.detect_contract_type(pdf_path)
        
        text = self.extract_text_ocr(pdf_path)
        if not text or len(text) < 100:
            return ContractExtraction(filepath=pdf_path, filename=filename, 
                                      object_id=object_id, contract_type_detected=contract_type)
        
        data, tokens, cost = self.extract_with_llm(text)
        
        result = ContractExtraction(
            filepath=pdf_path,
            filename=filename,
            object_id=object_id,
            contract_type_detected=contract_type,
            llm_tokens_used=tokens,
            llm_cost_usd=cost
        )
        
        for key, value in data.items():
            if hasattr(result, key) and value is not None:
                setattr(result, key, value)
        
        return result
    
    def find_all_contracts(self) -> tuple[List[str], List[str]]:
        """Find all inhuur and verhuur contract PDFs"""
        inhuur = []
        verhuur = []
        
        for root, dirs, files in os.walk(WONINGEN_PATH):
            for f in files:
                if not f.lower().endswith('.pdf'):
                    continue
                filepath = os.path.join(root, f)
                
                if '/2_Inhuur/2_Inhuurovereenkomsten' in root:
                    inhuur.append(filepath)
                elif '/2_Verhuurovereenkomsten' in root and '/3_Verhuur/' in root:
                    verhuur.append(filepath)
        
        return inhuur, verhuur
    
    def parse_all(self, output_dir: str = "Shared/Sources", limit: int = None) -> dict:
        """Parse all contracts and save results"""
        inhuur_paths, verhuur_paths = self.find_all_contracts()
        
        print(f"Found {len(inhuur_paths)} inhuur contracts")
        print(f"Found {len(verhuur_paths)} verhuur contracts")
        
        if limit:
            inhuur_paths = inhuur_paths[:limit]
            verhuur_paths = verhuur_paths[:limit]
            print(f"Limited to {limit} each for testing")
        
        results = {'inhuur': [], 'verhuur': []}
        total_cost = 0
        total_tokens = 0
        
        # Parse inhuur
        print(f"\n{'='*50}")
        print("PARSING INHUUR CONTRACTS")
        print('='*50)
        
        for i, path in enumerate(inhuur_paths):
            print(f"\n[{i+1}/{len(inhuur_paths)}] {os.path.basename(path)[:50]}")
            result = self.parse_single(path)
            results['inhuur'].append(result)
            
            if result.llm_cost_usd:
                total_cost += result.llm_cost_usd
                total_tokens += result.llm_tokens_used
            
            print(f"  ✓ Eigenaar: {result.verhuurder_naam or 'N/A'}")
            print(f"  ✓ Huurprijs: {result.huurprijs_excl_btw or 'N/A'}")
        
        # Parse verhuur
        print(f"\n{'='*50}")
        print("PARSING VERHUUR CONTRACTS")
        print('='*50)
        
        for i, path in enumerate(verhuur_paths):
            print(f"\n[{i+1}/{len(verhuur_paths)}] {os.path.basename(path)[:50]}")
            result = self.parse_single(path)
            results['verhuur'].append(result)
            
            if result.llm_cost_usd:
                total_cost += result.llm_cost_usd
                total_tokens += result.llm_tokens_used
            
            print(f"  ✓ Huurder: {result.huurder_naam or 'N/A'}")
            print(f"  ✓ Huurprijs: {result.huurprijs_excl_btw or 'N/A'}")
        
        # Summary
        print(f"\n{'='*50}")
        print("SUMMARY")
        print('='*50)
        print(f"Inhuur contracts: {len(results['inhuur'])}")
        print(f"Verhuur contracts: {len(results['verhuur'])}")
        print(f"Total tokens: {total_tokens:,}")
        print(f"Total cost: ${total_cost:.4f}")
        
        # Save CSVs
        self._save_csv(results['inhuur'], f"{output_dir}/all_inhuur_extracted.csv")
        self._save_csv(results['verhuur'], f"{output_dir}/all_verhuur_extracted.csv")
        
        return results
    
    def _save_csv(self, data: List[ContractExtraction], path: str):
        if not data:
            return
        fieldnames = list(asdict(data[0]).keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for item in data:
                writer.writerow(asdict(item))
        print(f"✅ Saved {len(data)} records to {path}")


if __name__ == '__main__':
    import sys
    
    parser = BatchContractParser()
    
    # Optional limit for testing
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    parser.parse_all(limit=limit)
