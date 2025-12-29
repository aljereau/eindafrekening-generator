
from pypdf import PdfReader
from pathlib import Path
import sys

def analyze_pdf(file_path):
    print(f"--- Analyzing: {file_path.name} ---")
    try:
        reader = PdfReader(file_path)
        number_of_pages = len(reader.pages)
        print(f"Total Pages: {number_of_pages}\n")
        
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            print(f"--- Page {i+1} ---")
            print(text)
            print("\n")
            full_text += text + "\n"
            
        return full_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

if __name__ == "__main__":
    target_file = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/HVOK_Compierekade15AlphenadRijn_PPLDirekt_070325.pdf")
    
    if target_file.exists():
        analyze_pdf(target_file)
    else:
        print(f"File not found: {target_file}")
