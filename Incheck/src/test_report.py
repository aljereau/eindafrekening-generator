import sys
import os
from datetime import date

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Incheck.src.planning_api import PlanningAPI
from Incheck.src.report_generator import PlanningReportGenerator

def test_report_generation():
    print("🚀 Starting Report Generation Test...")
    
    # 1. Fetch Data
    api = PlanningAPI("database/ryanrent_mock.db")
    transitions = api.get_upcoming_transitions(days_lookahead=60)
    print(f"✅ Fetched {len(transitions)} transitions")
    
    # 2. Setup Generator
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates', 'planning_report.html'))
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', 'test_report.html'))
    
    # Ensure reports dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 3. Generate
    generator = PlanningReportGenerator(template_path)
    path = generator.generate_report(transitions, output_path)
    
    print(f"✅ Report generated at: {path}")

if __name__ == "__main__":
    test_report_generation()
