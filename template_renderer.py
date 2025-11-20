#!/usr/bin/env python3
"""
Template Renderer - Jinja2 rendering for OnePager and Detail templates

Renders HTML output from viewmodels using Jinja2 templates.
Supports dual template architecture (onepager + detail).
"""

from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any
import os


class TemplateRenderer:
    """Renders HTML from viewmodels using Jinja2 templates"""
    
    def __init__(self, template_dir: str = "."):
        """
        Initialize renderer with template directory
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['euro'] = self._filter_euro
        self.env.filters['percentage'] = self._filter_percentage
        self.env.filters['abs'] = abs
    
    def _filter_euro(self, value: float) -> str:
        """Format number as Euro currency"""
        return f"€{value:,.2f}".replace(',', '.')
    
    def _filter_percentage(self, value: float, decimals: int = 1) -> str:
        """Format number as percentage"""
        return f"{value:.{decimals}f}%"
    
    def render_onepager(self, viewmodel: Dict[str, Any], 
                       template_name: str = "template_onepager.html") -> str:
        """
        Render OnePager HTML from viewmodel
        
        Args:
            viewmodel: OnePager viewmodel dictionary
            template_name: Template filename
            
        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(**viewmodel)
    
    def render_detail(self, viewmodel: Dict[str, Any],
                     template_name: str = "template_detail.html") -> str:
        """
        Render Detail HTML from viewmodel
        
        Args:
            viewmodel: Detail viewmodel dictionary
            template_name: Template filename
            
        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(**viewmodel)
    
    def render_both(self, onepager_vm: Dict[str, Any], detail_vm: Dict[str, Any]) -> tuple[str, str]:
        """
        Render both OnePager and Detail templates
        
        Args:
            onepager_vm: OnePager viewmodel
            detail_vm: Detail viewmodel
            
        Returns:
            Tuple of (onepager_html, detail_html)
        """
        onepager_html = self.render_onepager(onepager_vm)
        detail_html = self.render_detail(detail_vm)
        return onepager_html, detail_html


def save_html(html: str, filepath: str):
    """
    Save HTML string to file
    
    Args:
        html: HTML content
        filepath: Output file path
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"💾 Saved HTML: {filepath}")


def render_and_save(onepager_vm: Dict[str, Any], detail_vm: Dict[str, Any],
                   output_dir: str = "output", basename: str = "eindafrekening",
                   template_dir: str = ".") -> tuple[str, str]:
    """
    Render both templates and save HTML files
    
    Args:
        onepager_vm: OnePager viewmodel
        detail_vm: Detail viewmodel
        output_dir: Output directory for HTML files
        basename: Base filename (e.g., "eindafrekening_jansen")
        template_dir: Directory containing templates
        
    Returns:
        Tuple of (onepager_path, detail_path)
    """
    renderer = TemplateRenderer(template_dir=template_dir)
    
    # Render both
    onepager_html, detail_html = renderer.render_both(onepager_vm, detail_vm)
    
    # Build output paths
    onepager_path = os.path.join(output_dir, f"{basename}_onepager.html")
    detail_path = os.path.join(output_dir, f"{basename}_detail.html")
    
    # Save files
    save_html(onepager_html, onepager_path)
    save_html(detail_html, detail_path)
    
    return onepager_path, detail_path


if __name__ == "__main__":
    """Test template renderer with mock data"""
    print("🎨 Testing Template Renderer")
    print("=" * 60)
    
    # Mock viewmodels
    mock_onepager = {
        "client": {
            "name": "Fam. Jansen",
            "contact_person": "Jan Jansen",
            "email": "jan@example.com",
            "phone": "06-12345678"
        },
        "object": {
            "address": "Strandweg 42",
            "unit": "A3",
            "postal_code": "1234AB",
            "city": "Zandvoort",
            "object_id": "OBJ-001"
        },
        "period": {
            "checkin_date": "2024-08-01",
            "checkout_date": "2024-08-13",
            "days": 12
        },
        "financial": {
            "borg": {
                "voorschot": 800,
                "gebruikt": 600,
                "terug": 200,
                "bars": {
                    "gebruikt_pct": 75.0,
                    "terug_pct": 25.0,
                    "extra_pct": 0.0,
                    "is_overfilled": False
                }
            },
            "gwe": {
                "voorschot": 350,
                "totaal_incl": 308.55,
                "meer_minder": 41.45,
                "bars": {
                    "gebruikt_pct": 88.2,
                    "terug_pct": 11.8,
                    "extra_pct": 0.0,
                    "is_overfilled": False
                }
            },
            "cleaning": {
                "pakket_type": "5_uur",
                "inbegrepen_uren": 5,
                "voorschot": 250,
                "extra_uren": 2.5,
                "extra_bedrag": 125,
                "bars": {
                    "gebruikt_pct": 100.0,
                    "terug_pct": 0.0,
                    "extra_pct": 50.0,
                    "is_overfilled": True
                }
            },
            "damage": {
                "totaal_incl": 72.6
            },
            "totals": {
                "totaal_eindafrekening": 144.05
            }
        }
    }
    
    mock_detail = {
        "client": {
            "name": "Fam. Jansen",
            "object_address": "Strandweg 42, A3, 1234AB Zandvoort",
            "period": {
                "checkin_date": "2024-08-01",
                "checkout_date": "2024-08-13"
            }
        },
        "gwe": {
            "meterstanden": {
                "stroom": {"begin": 10000, "eind": 10500, "verbruik": 500},
                "gas": {"begin": 5000, "eind": 5100, "verbruik": 100}
            },
            "kostenregels": [
                {"omschrijving": "Elektra verbruik", "verbruik_of_dagen": 500, "tarief_excl": 0.28, "kosten_excl": 140},
                {"omschrijving": "Gas verbruik", "verbruik_of_dagen": 100, "tarief_excl": 1.15, "kosten_excl": 115}
            ],
            "totalen": {"totaal_excl": 255, "btw": 53.55, "totaal_incl": 308.55}
        },
        "cleaning": {
            "pakket_type": "5_uur",
            "inbegrepen_uren": 5,
            "totaal_uren": 7.5,
            "extra_uren": 2.5,
            "uurtarief": 50,
            "extra_bedrag": 125,
            "voorschot": 250
        },
        "damage": {
            "regels": [
                {"beschrijving": "Reparatie deur", "aantal": 1, "tarief_excl": 30, "bedrag_excl": 30},
                {"beschrijving": "Vervangen lamp", "aantal": 2, "tarief_excl": 15, "bedrag_excl": 30}
            ],
            "totalen": {"totaal_excl": 60, "btw": 12.6, "totaal_incl": 72.6}
        },
        "borg": {
            "voorschot": 800,
            "gebruikt": 600,
            "terug": 200,
            "restschade": 0
        }
    }
    
    print("\n✅ Mock viewmodels created")
    
    # Test rendering (will fail if templates don't exist yet)
    try:
        onepager_path, detail_path = render_and_save(
            mock_onepager,
            mock_detail,
            basename="test_eindafrekening"
        )
        print(f"\n✅ Templates rendered successfully:")
        print(f"   OnePager: {onepager_path}")
        print(f"   Detail: {detail_path}")
    except Exception as e:
        print(f"\n⚠️  Could not render templates (they may not exist yet): {e}")
        print("   This is expected if templates haven't been created.")
    
    print("\n✅ Template Renderer test completed!")

