#!/usr/bin/env python3
"""
LLM-based Contract Parser for RyanRent
Extracts structured data from IHOVK/VHOVK PDFs using GPT-4o-mini
"""

import os
import json
import csv
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from datetime import datetime

# OCR dependencies
import pytesseract
from pdf2image import convert_from_path

# LLM
from openai import OpenAI


@dataclass
class ContractExtraction:
    """All fields we want to extract from a contract"""
    # Source file
    filename: str
    
    # Woning (property)
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    
    # Verhuurder/Eigenaar (landlord - for inhuur this is who RyanRent rents FROM)
    verhuurder_naam: Optional[str] = None
    verhuurder_type: Optional[str] = None  # particulier / bedrijf
    verhuurder_kvk: Optional[str] = None
    verhuurder_iban: Optional[str] = None
    verhuurder_email: Optional[str] = None
    verhuurder_telefoon: Optional[str] = None
    verhuurder_adres: Optional[str] = None
    verhuurder_postcode: Optional[str] = None
    verhuurder_plaats: Optional[str] = None
    
    # Huurder (tenant - for verhuur this is who RyanRent rents TO)
    huurder_naam: Optional[str] = None
    huurder_kvk: Optional[str] = None
    
    # Contract terms
    contract_type: Optional[str] = None  # bepaalde_tijd / onbepaalde_tijd
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
    
    # Services included
    incl_stoffering: Optional[bool] = None
    incl_meubilering: Optional[bool] = None
    incl_internet: Optional[bool] = None
    incl_schoonmaak: Optional[bool] = None
    incl_bedlinnen: Optional[bool] = None
    incl_tuinonderhoud: Optional[bool] = None
    gwe_verantwoordelijk: Optional[str] = None  # eigen_beheer / ryanrent / huurder
    
    # Meta
    extraction_confidence: Optional[float] = None
    llm_tokens_used: Optional[int] = None
    llm_cost_usd: Optional[float] = None


EXTRACTION_PROMPT = """You are extracting data from a Dutch rental contract (huurovereenkomst).

Extract the following fields. Return ONLY valid JSON with these exact keys:

{
  "adres": "property street address",
  "postcode": "Dutch postcode like 3332 GB",
  "plaats": "city name",
  
  "verhuurder_naam": "landlord/owner name (company or person) - this is who OWNS the property",
  "verhuurder_type": "particulier or bedrijf",
  "verhuurder_kvk": "8-digit KvK number if company",
  "verhuurder_iban": "bank account IBAN",
  "verhuurder_email": "email address",
  "verhuurder_telefoon": "phone number",
  "verhuurder_adres": "landlord's address",
  "verhuurder_postcode": "landlord's postcode",
  "verhuurder_plaats": "landlord's city",
  
  "huurder_naam": "tenant name (company or person)",
  "huurder_kvk": "tenant KvK if company",
  
  "contract_type": "bepaalde_tijd or onbepaalde_tijd",
  "start_datum": "start date as DD-MM-YYYY",
  "eind_datum": "end date as DD-MM-YYYY or null if onbepaalde_tijd",
  "minimale_duur_maanden": "minimum duration in months as integer",
  "opzegtermijn_maanden": "notice period in months as integer",
  
  "huurprijs_excl_btw": "monthly rent excluding BTW as number",
  "huurprijs_incl_btw": "monthly rent including BTW as number",
  "btw_percentage": "BTW percentage as decimal (0.09 or 0.21)",
  "borg": "deposit/waarborgsom amount as number",
  "voorschot_gwe": "utility advance payment as number",
  "vve_kosten": "VvE/service charges as number",
  "servicekosten": "other service costs as number",
  
  "incl_stoffering": true/false if furniture included,
  "incl_meubilering": true/false if furnishing included,
  "incl_internet": true/false if internet included,
  "incl_schoonmaak": true/false if cleaning included,
  "incl_bedlinnen": true/false if bed linen included,
  "incl_tuinonderhoud": true/false if garden maintenance included,
  "gwe_verantwoordelijk": "who pays utilities: eigen_beheer/ryanrent/huurder",
  
  "extraction_confidence": 0.0-1.0 how confident you are in the extraction
}

IMPORTANT:
- Return null for any field you cannot find in the contract
- For Tradiro contracts: Tradiro is usually the HUURDER (tenant), the other party is VERHUURDER (owner)
- Amounts should be numbers only, no currency symbols
- Dates should be DD-MM-YYYY format

CONTRACT TEXT:
"""


class LLMContractParser:
    """Parse contracts using LLM for intelligent extraction"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Cheapest good model
        
    def extract_text_ocr(self, pdf_path: str, max_pages: int = 10) -> str:
        """Extract text from PDF using OCR"""
        try:
            images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=max_pages)
            texts = []
            for img in images:
                text = pytesseract.image_to_string(img, lang='nld+eng')
                if text.strip():
                    texts.append(text)
            return "\n".join(texts)
        except Exception as e:
            print(f"OCR error for {pdf_path}: {e}")
            return ""
    
    def extract_with_llm(self, text: str) -> tuple[dict, int, float]:
        """Call LLM to extract structured data from contract text"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": EXTRACTION_PROMPT + text[:12000]  # Limit context
                }],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistency
            )
            
            result = json.loads(response.choices[0].message.content)
            tokens = response.usage.total_tokens
            # Cost: $0.15/1M input + $0.60/1M output for gpt-4o-mini
            cost = (response.usage.prompt_tokens * 0.00000015 + 
                    response.usage.completion_tokens * 0.0000006)
            
            return result, tokens, cost
        except Exception as e:
            print(f"LLM error: {e}")
            return {}, 0, 0
    
    def parse_contract(self, pdf_path: str) -> ContractExtraction:
        """Parse a single contract PDF"""
        filename = os.path.basename(pdf_path)
        print(f"  Extracting OCR from {filename}...")
        
        text = self.extract_text_ocr(pdf_path)
        if not text or len(text) < 100:
            return ContractExtraction(filename=filename)
        
        print(f"  Calling LLM ({len(text)} chars)...")
        data, tokens, cost = self.extract_with_llm(text)
        
        # Map to dataclass
        result = ContractExtraction(
            filename=filename,
            llm_tokens_used=tokens,
            llm_cost_usd=cost
        )
        
        # Copy all matching fields
        for key, value in data.items():
            if hasattr(result, key) and value is not None:
                setattr(result, key, value)
        
        return result
    
    def parse_folder(self, folder_path: str, output_csv: str = None) -> List[ContractExtraction]:
        """Parse all PDFs in a folder"""
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files")
        
        results = []
        total_cost = 0
        total_tokens = 0
        
        for i, filename in enumerate(pdf_files):
            print(f"\n[{i+1}/{len(pdf_files)}] {filename}")
            pdf_path = os.path.join(folder_path, filename)
            
            try:
                result = self.parse_contract(pdf_path)
                results.append(result)
                
                if result.llm_cost_usd:
                    total_cost += result.llm_cost_usd
                    total_tokens += result.llm_tokens_used
                
                # Show key extracted data
                print(f"    ✓ Verhuurder: {result.verhuurder_naam or 'N/A'}")
                print(f"    ✓ Adres: {result.adres or 'N/A'}")
                print(f"    ✓ Huurprijs: {result.huurprijs_excl_btw or 'N/A'}")
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results.append(ContractExtraction(filename=filename))
        
        print(f"\n{'='*50}")
        print(f"TOTAL: {len(results)} contracts processed")
        print(f"TOKENS: {total_tokens:,}")
        print(f"COST: ${total_cost:.4f}")
        
        if output_csv:
            self._save_csv(results, output_csv)
        
        return results
    
    def _save_csv(self, results: List[ContractExtraction], output_path: str):
        """Save results to CSV"""
        if not results:
            return
        
        fieldnames = list(asdict(results[0]).keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for data in results:
                writer.writerow(asdict(data))
        
        print(f"\n✅ Saved to {output_path}")


if __name__ == '__main__':
    import sys
    
    parser = LLMContractParser()
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else 'contracts_extracted.csv'
        
        if os.path.isdir(path):
            parser.parse_folder(path, output)
        else:
            result = parser.parse_contract(path)
            print(json.dumps(asdict(result), indent=2, default=str))
    else:
        print("Usage: python llm_contract_parser.py <pdf_or_folder> [output.csv]")
