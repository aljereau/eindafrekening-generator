import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Incheck.src.planning_api import PlanningAPI

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("==========================================")
    print("      📋 INCHECK PLANNING APP 📋          ")
    print("==========================================")

def show_planning_report():
    api = PlanningAPI()
    transitions = api.get_upcoming_transitions(days_lookahead=60)
    
    print("\n📅 Planning & Inspecties (Komende 60 Dagen)")
    print("=" * 100)
    # Header
    print(f"{'Adres':<30} | {'Uitcheck':<20} | {'Inspecties (Huidig)':<15} | {'Gap/Prio':<15} | {'Volgende Huurder':<25}")
    print("-" * 100)
    
    for t in transitions:
        # Priority
        prio_text = t['priority']
        if t['priority'] == "CRITICAL":
            prio_text = "🔴 KRITISCH"
        elif t['priority'] == "HIGH":
            prio_text = "🟡 HOOG"
        elif t['priority'] == "NORMAL":
            prio_text = "🟢 NORMAAL"
            
        gap_text = f"{t['gap_days']} dagen" if t['gap_days'] is not None else "-"
        
        # Icons
        def get_icon(status):
            s = status.get('status', 'needed')
            if s == 'completed': return "✅"
            if s == 'planned': return "📅"
            if s == 'needed': return "⭕"
            return "❓"
            
        curr_insp = f"Pre:{get_icon(t['pre_inspection'])} Uit:{get_icon(t['uitcheck'])}"
        
        # Format rows
        # Address
        addr = t['property'][:28]
        # Checkout
        checkout = f"{t['checkout_date']} ({t['current_client'][:10]}..)"
        
        print(f"{addr:<30} | {checkout:<20} | {curr_insp:<15} | {gap_text} {prio_text} | {t['next_tenant'][:25]}")
        
    print("-" * 100)
    print("Legenda: ⭕ Nodig | 📅 Gepland | ✅ Gedaan")
    input("\nDruk op Enter om door te gaan...")

def main_menu():
    while True:
        clear_screen()
        print_header()
        print("1. 📅 Toon Planning & Inspecties")
        print("2. 🔄 Importeer Excel Data")
        print("q. Afsluiten")
        
        choice = input("\nKies een optie: ").strip().lower()
        
        if choice == '1':
            show_planning_report()
        elif choice == '2':
            print("Importing data...")
            # Run import script
            os.system(f"{sys.executable} Incheck/src/import_excel.py")
            input("\nDruk op Enter om door te gaan...")
        elif choice == 'q':
            print("Tot ziens!")
            break

if __name__ == "__main__":
    main_menu()
