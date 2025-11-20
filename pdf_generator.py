#!/usr/bin/env python3
"""
PDF Generator - WeasyPrint wrapper with graceful HTML fallback

Converts HTML to PDF using WeasyPrint. If PDF generation fails (common on macOS
due to missing system libraries), falls back to HTML-only output.

HTML-first strategy: Always save HTML, attempt PDF as bonus.
"""

import os
from typing import Optional


class PDFGenerator:
    """Handles PDF generation from HTML with graceful fallback"""
    
    def __init__(self, base_url: str = "."):
        """
        Initialize PDF generator
        
        Args:
            base_url: Base URL for resolving relative paths in HTML
        """
        self.base_url = base_url
        self._weasyprint_available = None
    
    def _check_weasyprint(self) -> bool:
        """
        Check if WeasyPrint is available and working
        
        Returns:
            True if WeasyPrint can be imported, False otherwise
        """
        if self._weasyprint_available is not None:
            return self._weasyprint_available
        
        try:
            from weasyprint import HTML
            self._weasyprint_available = True
            return True
        except (ImportError, OSError) as e:
            print(f"⚠️  WeasyPrint not available: {e}")
            print("   PDFs cannot be generated. HTML files will be saved instead.")
            print("   You can manually print HTML to PDF from your browser.")
            self._weasyprint_available = False
            return False
    
    def html_to_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Convert HTML string to PDF
        
        Args:
            html_content: HTML content as string
            output_path: Output PDF file path
            
        Returns:
            True if PDF was created successfully, False otherwise
        """
        if not self._check_weasyprint():
            return False
        
        try:
            from weasyprint import HTML
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Generate PDF
            HTML(string=html_content, base_url=self.base_url).write_pdf(output_path)
            
            print(f"📄 Generated PDF: {output_path}")
            return True
            
        except Exception as e:
            print(f"⚠️  PDF generation failed: {e}")
            print(f"   HTML can be manually printed to PDF from browser.")
            return False
    
    def html_file_to_pdf(self, html_path: str, pdf_path: Optional[str] = None) -> Optional[str]:
        """
        Convert HTML file to PDF
        
        Args:
            html_path: Path to HTML file
            pdf_path: Output PDF path (defaults to html_path with .pdf extension)
            
        Returns:
            Path to generated PDF if successful, None otherwise
        """
        if pdf_path is None:
            pdf_path = html_path.rsplit('.', 1)[0] + '.pdf'
        
        # Read HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Convert to PDF
        success = self.html_to_pdf(html_content, pdf_path)
        
        return pdf_path if success else None


def generate_pdf_from_html(html_content: str, output_path: str, 
                           base_url: str = ".") -> tuple[str, bool]:
    """
    Generate PDF from HTML content with fallback to HTML
    
    Args:
        html_content: HTML content string
        output_path: Desired output path (will be .pdf or .html)
        base_url: Base URL for resolving relative paths
        
    Returns:
        Tuple of (actual_output_path, is_pdf)
        - actual_output_path: Path to generated file (PDF or HTML)
        - is_pdf: True if PDF was generated, False if HTML fallback
    """
    generator = PDFGenerator(base_url=base_url)
    
    # Always save HTML first (as backup/fallback)
    html_path = output_path.replace('.pdf', '.html') if output_path.endswith('.pdf') else output_path + '.html'
    
    os.makedirs(os.path.dirname(html_path) or '.', exist_ok=True)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"💾 Saved HTML: {html_path}")
    
    # Attempt PDF generation
    if output_path.endswith('.pdf'):
        success = generator.html_to_pdf(html_content, output_path)
        if success:
            return output_path, True
    
    # Fallback to HTML
    print(f"   💡 Tip: Open {html_path} in browser and use Print → Save as PDF")
    return html_path, False


def generate_pdfs_from_html_files(onepager_html_path: str, detail_html_path: str) -> tuple[str, str]:
    """
    Generate PDFs from existing HTML files
    
    Args:
        onepager_html_path: Path to OnePager HTML
        detail_html_path: Path to Detail HTML
        
    Returns:
        Tuple of (onepager_output_path, detail_output_path)
        Each path is either .pdf (success) or .html (fallback)
    """
    generator = PDFGenerator()
    
    # Generate OnePager PDF
    onepager_pdf_path = onepager_html_path.replace('.html', '.pdf')
    onepager_result = generator.html_file_to_pdf(onepager_html_path, onepager_pdf_path)
    onepager_output = onepager_result if onepager_result else onepager_html_path
    
    # Generate Detail PDF
    detail_pdf_path = detail_html_path.replace('.html', '.pdf')
    detail_result = generator.html_file_to_pdf(detail_html_path, detail_pdf_path)
    detail_output = detail_result if detail_result else detail_html_path
    
    return onepager_output, detail_output


def render_and_generate_pdfs(onepager_html: str, detail_html: str,
                             output_dir: str = "output", 
                             basename: str = "eindafrekening",
                             base_url: str = ".") -> dict:
    """
    Render HTML and generate PDFs with complete fallback handling
    
    Args:
        onepager_html: OnePager HTML content
        detail_html: Detail HTML content
        output_dir: Output directory
        basename: Base filename
        base_url: Base URL for WeasyPrint
        
    Returns:
        Dictionary with paths and status:
        {
            'onepager': {'html': path, 'pdf': path or None, 'is_pdf': bool},
            'detail': {'html': path, 'pdf': path or None, 'is_pdf': bool}
        }
    """
    generator = PDFGenerator(base_url=base_url)
    
    # Build paths
    onepager_html_path = os.path.join(output_dir, f"{basename}_onepager.html")
    detail_html_path = os.path.join(output_dir, f"{basename}_detail.html")
    onepager_pdf_path = os.path.join(output_dir, f"{basename}_onepager.pdf")
    detail_pdf_path = os.path.join(output_dir, f"{basename}_detail.pdf")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save HTMLs
    with open(onepager_html_path, 'w', encoding='utf-8') as f:
        f.write(onepager_html)
    print(f"💾 Saved HTML: {onepager_html_path}")
    
    with open(detail_html_path, 'w', encoding='utf-8') as f:
        f.write(detail_html)
    print(f"💾 Saved HTML: {detail_html_path}")
    
    # Attempt PDF generation
    onepager_pdf_success = generator.html_to_pdf(onepager_html, onepager_pdf_path)
    detail_pdf_success = generator.html_to_pdf(detail_html, detail_pdf_path)
    
    # Build result
    result = {
        'onepager': {
            'html': onepager_html_path,
            'pdf': onepager_pdf_path if onepager_pdf_success else None,
            'is_pdf': onepager_pdf_success
        },
        'detail': {
            'html': detail_html_path,
            'pdf': detail_pdf_path if detail_pdf_success else None,
            'is_pdf': detail_pdf_success
        }
    }
    
    if not (onepager_pdf_success or detail_pdf_success):
        print(f"\n💡 Tip: Open HTML files in browser and use Print → Save as PDF")
    
    return result


if __name__ == "__main__":
    """Test PDF generator"""
    print("📄 Testing PDF Generator")
    print("=" * 60)
    
    # Create simple test HTML
    test_html = """
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <title>Test PDF</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
            }
            h1 { color: #1F4E78; }
            .box {
                border: 2px solid #5B9BD5;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <h1>🏠 RyanRent Test Document</h1>
        <div class="box">
            <h2>PDF Generator Test</h2>
            <p>This is a test document to verify PDF generation.</p>
            <p><strong>Status:</strong> If you see this as PDF, WeasyPrint is working! ✅</p>
        </div>
        <div class="box">
            <h3>Features:</h3>
            <ul>
                <li>HTML to PDF conversion</li>
                <li>Graceful fallback to HTML</li>
                <li>Browser print support</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    # Test PDF generation
    print("\n1. Testing HTML to PDF conversion:")
    output_path = "output/test_pdf_generator.pdf"
    
    actual_path, is_pdf = generate_pdf_from_html(test_html, output_path)
    
    if is_pdf:
        print(f"\n✅ PDF generated successfully: {actual_path}")
    else:
        print(f"\n⚠️  PDF generation unavailable, HTML saved: {actual_path}")
    
    print("\n✅ PDF Generator test completed!")
    print(f"\n📂 Output location: {os.path.abspath(actual_path)}")

