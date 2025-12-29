
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def extract_text_from_docx(docx_path):
    print(f"--- Analyzing DOCX: {docx_path.name} ---")
    try:
        with zipfile.ZipFile(docx_path) as zf:
            xml_content = zf.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # XML namespace for Word
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            full_text = []
            # Iterate through paragraphs
            for p in tree.findall('.//w:p', namespaces):
                texts = [node.text for node in p.findall('.//w:t', namespaces) if node.text]
                if texts:
                    full_text.append(''.join(texts))
                else:
                    full_text.append('') # Preserve empty lines for structure
            
            return '\n'.join(full_text)
            
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None

if __name__ == "__main__":
    target_file = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/Shared/Sources/HOVK_Kortesingelstraat21-3_Schiedam_BedrijvenBakker_090126.docx")
    
    if target_file.exists():
        text = extract_text_from_docx(target_file)
        print(text)
    else:
        print(f"File not found: {target_file}")
