#!/usr/bin/env python3
"""Quick test of LLM extraction on a contract PDF"""

import os
from openai import OpenAI
import pytesseract
from pdf2image import convert_from_path

# Extract OCR text
pdf_path = "Shared/Sources/Coornhertstraat 95.pdf"
print("Extracting OCR...")
images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=5)
text = "\n".join([pytesseract.image_to_string(img, lang='nld+eng') for img in images])

print(f"OCR extracted: {len(text)} chars")

# Use GPT-4o-mini
client = OpenAI()

print("\nCalling GPT-4o-mini...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": f"""Extract the following from this Dutch rental contract. Return JSON only:
- verhuurder_naam (landlord/owner company - NOT Tradiro, they are the tenant)
- verhuurder_kvk (KvK of landlord, 8 digits)  
- huurder_naam (tenant company)
- adres (property street address)
- postcode
- plaats (city)
- huurprijs (monthly rent amount, number only)
- borg (deposit amount, number only)
- ingangsdatum (start date, format DD-MM-YYYY)
- contract_type (bepaalde_tijd or onbepaalde_tijd)

Contract text:
{text[:10000]}"""
    }],
    response_format={"type": "json_object"}
)

print("\n=== LLM EXTRACTION RESULT ===")
print(response.choices[0].message.content)
print(f"\nTokens: {response.usage.total_tokens}")
print(f"Cost: ~${response.usage.total_tokens * 0.00000015 + response.usage.completion_tokens * 0.0000006:.5f}")
