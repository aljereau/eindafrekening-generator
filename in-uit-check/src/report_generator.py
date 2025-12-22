from datetime import date, datetime, timedelta
from jinja2 import Template
from typing import List, Dict
import os

class PlanningReportGenerator:
    """Generate HTML reports for planning overview"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        
    def generate_report(self, transitions: List[Dict], output_path: str) -> str:
        """
        Generate HTML report from transitions data
        
        Args:
            transitions: List of transition dicts from PlanningAPI
            output_path: Where to save the HTML file
            
        Returns:
            Path to generated HTML file
        """
        
        # Load template
        with open(self.template_path, 'r') as f:
            template = Template(f.read())
        
        # Calculate summary stats
        critical_count = sum(1 for t in transitions if t['priority'] == 'CRITICAL')
        high_count = sum(1 for t in transitions if t['priority'] == 'HIGH')
        normal_count = sum(1 for t in transitions if t['priority'] == 'NORMAL')
        
        # Add warnings to each transition
        for t in transitions:
            t['warnings'] = self._generate_warnings(t)
            
            # Format dates nicely if they exist
            # Assuming 'volgende_huurder' contains the date in parens as formatted in API
            t['incheck_date'] = None
            if 'volgende_huurder' in t and '(' in t['volgende_huurder']:
                 try:
                     t['incheck_date'] = t['volgende_huurder'].split('(')[1].replace(')', '')
                 except:
                     pass
        
        # Render
        html = template.render(
            report_date=datetime.now().strftime('%d-%m-%Y'),
            critical_count=critical_count,
            high_count=high_count,
            normal_count=normal_count,
            transitions=transitions
        )
        
        # Save
        with open(output_path, 'w') as f:
            f.write(html)
        
        return output_path
    
    def _generate_warnings(self, transition: Dict) -> List[str]:
        """Generate warnings for a transition"""
        warnings = []
        today = date.today()
        
        try:
            checkout_date = datetime.strptime(transition['date'], '%Y-%m-%d').date()
            days_until_checkout = (checkout_date - today).days
            
            # Check for tight gap
            if transition.get('dagen_tussen') is not None and transition['dagen_tussen'] < 3:
                warnings.append(f"⚠️ Zeer korte overgang ({transition['dagen_tussen']} dagen) - check schoonmaak!")
                
            # Check for settlement status
            if days_until_checkout < 0 and transition['details']['afrekening_status'] != 'voltooid':
                 warnings.append("⚠️ Afrekening nog niet voltooid!")
                 
            # Check for missing pre-inspection
            pre_status = transition['voorinspectie'].get('status', 'nodig')
            if pre_status == 'nodig':
                if days_until_checkout <= 7:
                    warnings.append(f"🚨 Voorinspectie moet binnen {days_until_checkout} dagen gepland worden!")
                elif days_until_checkout <= 14:
                    warnings.append("⚠️ Plan voorinspectie binnenkort")
            
            # Check for missing VIS
            vis_status = transition['vis'].get('status', 'nodig')
            has_next_tenant = "Geen nieuwe huurder" not in transition['volgende_huurder']
            
            if has_next_tenant and vis_status == 'nodig':
                warnings.append("⚠️ VIS moet nog gepland worden voor nieuwe huurder")
                 
        except Exception as e:
            print(f"Warning generation error: {e}")
            
        return warnings
