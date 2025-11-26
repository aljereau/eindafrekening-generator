import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    print(f"--- Extracting text from: {os.path.basename(pdf_path)} ---")
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(text[:2000]) # Print first 2000 chars to get the gist
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

files = [
    "/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/HOVK Hugo de Grootstraat 72A  B.pdf",
    "/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/IHOVK Lange Kruisweg 12.pdf"
]

for f in files:
    extract_text_from_pdf(f)
