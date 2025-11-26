from datetime import date
from typing import List, Dict, Optional, Tuple
import sys
import os

# Ensure we can import from Shared if running as script
try:
    from Shared.database import Database
    from Shared.entities import Huis, InhuurContract
    from HuizenManager.src.manager import HuizenManager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from Shared.database import Database
    from Shared.entities import Huis, InhuurContract
    from HuizenManager.src.manager import HuizenManager

class StrategyAdvisor:
    """
    Advisor to help calculate the best price for a new contract.
    Analyzes costs, margins, and market rates.
    """

    def __init__(self, manager: HuizenManager = None):
        self.manager = manager or HuizenManager()
        self.db = self.manager.db

    def find_house(self, address_query: str) -> List[Huis]:
        """Fuzzy search for a house by address."""
        conn = self.db._get_connection()
        # Simple LIKE query for now
        rows = conn.execute(
            "SELECT * FROM huizen WHERE adres LIKE ? AND status = 'active'", 
            (f"%{address_query}%",)
        ).fetchall()
        conn.close()
        
        return [
            Huis(
                id=r['id'], object_id=r['object_id'], adres=r['adres'], 
                postcode=r['postcode'], plaats=r['plaats'], 
                aantal_pers=r['aantal_pers'], status=r['status']
            ) for r in rows
        ]

    def get_base_costs(self, huis_id: int) -> Dict:
        """
        Get the monthly base cost breakdown (Inhuur) for the house.
        Returns: Dict with 'total' and 'components'
        """
        contract = self.manager.get_active_contract(huis_id)
        if not contract:
            return {"total": 0.0, "components": {}}
            
        # Sum up all costs from the Inhuur contract
        components = {
            "Kale Huur": contract.kale_huur,
            "Servicekosten": contract.servicekosten,
            "Voorschot GWE": contract.voorschot_gwe,
            "Internet": contract.internet_kosten,
            "Inventaris": contract.inventaris_kosten,
            "Afval": contract.afval_kosten,
            "Schoonmaak": contract.schoonmaak_kosten
        }
        
        total = sum(components.values())
        return {"total": total, "components": components}

    def calculate_service_costs(self, services: List[str], capacity: int) -> Dict:
        """
        Calculate monthly cost of added services.
        Returns: Dict with 'total' and 'details' list
        """
        conn = self.db._get_connection()
        total_monthly = 0.0
        details = []
        
        for service_name in services:
            # Fuzzy match parameter name
            row = conn.execute(
                "SELECT * FROM parameters WHERE naam LIKE ?", 
                (f"%{service_name}%",)
            ).fetchone()
            
            if row:
                # Standard calculation
                cost = row['prijs_pp_pw'] * capacity * 4
                total_monthly += cost
                details.append({
                    "name": row['naam'],
                    "calculation": f"€{row['prijs_pp_pw']:.2f} x {capacity} pers x 4 wks",
                    "cost": cost
                })
            else:
                print(f"⚠️ Warning: Service '{service_name}' not found in parameters.")
        
        conn.close()
        return {"total": total_monthly, "details": details}

    def analyze_deal(self, huis_id: int, client_is_tradiro: bool, 
                    services: List[str], proposed_price: float) -> Dict:
        """
        Analyze a proposed deal.
        """
        # 1. Get House Info
        huis = self.manager.get_huis(huis_id)
        if not huis:
            return {"error": "House not found"}
            
        capacity = huis.aantal_pers or 0
        if capacity == 0:
            return {"error": "House has 0 capacity, cannot calculate per-person costs."}

        # 2. Calculate Costs
        base_data = self.get_base_costs(huis_id) # Dict with breakdown
        service_data = self.calculate_service_costs(services, capacity) # Dict with details
        
        base_cost = base_data['total']
        service_cost = service_data['total']
        total_cost = base_cost + service_cost
        
        if base_cost == 0:
            return {"error": "No active 'Inhuur' contract found. Cannot determine base cost."}

        # 3. Determine Margin Rules
        target_margin_pct = 8.0 if client_is_tradiro else 15.0
        
        # 4. Calculate Minimum Required Price
        min_required_price = total_cost / (1 - (target_margin_pct / 100.0))
        
        # 5. Analyze Proposal
        projected_margin_eur = proposed_price - total_cost
        projected_margin_pct = (projected_margin_eur / proposed_price * 100) if proposed_price > 0 else 0
        
        is_good_deal = proposed_price >= min_required_price
        
        return {
            "house_address": huis.adres,
            "capacity": capacity,
            "base_cost_monthly": base_cost,
            "base_cost_breakdown": base_data['components'],
            "service_cost_monthly": service_cost,
            "service_cost_details": service_data['details'],
            "total_cost_monthly": total_cost,
            "target_margin_pct": target_margin_pct,
            "min_required_price": min_required_price,
            "proposed_price": proposed_price,
            "projected_margin_eur": projected_margin_eur,
            "projected_margin_pct": projected_margin_pct,
            "is_good_deal": is_good_deal,
            "difference": proposed_price - min_required_price
        }
