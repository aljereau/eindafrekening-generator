import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.strategy_advisor import StrategyAdvisor

def print_header():
    print("\n" + "="*50)
    print("🤖  RYANRENT STRATEGY ADVISOR  🤖")
    print("="*50 + "\n")

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def format_currency(amount):
    return f"€{amount:,.2f}"

def run_bot():
    advisor = StrategyAdvisor()
    print_header()
    
    print("Hi Ronald! I can help you price a deal.")
    print("Let's start with the house.\n")
    
    # 1. Find House
    while True:
        address = get_input("🏠 Which house? (e.g. Nunspeetlaan)")
        matches = advisor.find_house(address)
        
        if not matches:
            print("❌ No active house found with that name. Try again.")
            continue
            
        if len(matches) > 1:
            print(f"Found {len(matches)} houses:")
            for i, h in enumerate(matches):
                print(f"  {i+1}. {h.adres} (Cap: {h.aantal_pers})")
            
            choice = get_input("Select number", "1")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    house = matches[idx]
                    break
            except ValueError:
                pass
            print("Invalid selection.")
        else:
            house = matches[0]
            print(f"✅ Selected: {house.adres} (Cap: {house.aantal_pers})")
            break
            
    # 2. Client Type
    print("\n👤 Client Details")
    client_type = get_input("Is the client Tradiro? (y/n)", "n").lower()
    is_tradiro = client_type.startswith('y')
    
    # 3. Services
    print("\n🛠️  Services")
    print("Enter services separated by comma (e.g. Internet, Afval)")
    services_input = get_input("Services", "Internet, Afval")
    services = [s.strip() for s in services_input.split(',')]
    
    # 4. Proposed Price
    print("\n💰 Proposal")
    while True:
        try:
            price_str = get_input("What price do you want to ask? (Monthly Total)")
            proposed_price = float(price_str.replace(',', '.'))
            break
        except ValueError:
            print("Please enter a valid number.")

    # 5. Analyze
    print("\n" + "-"*30)
    print("🔄 Analyzing Deal...")
    print("-"*-30)
    
    result = advisor.analyze_deal(house.id, is_tradiro, services, proposed_price)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    # 6. Report
    print(f"\n📊 ANALYSIS FOR {result['house_address'].upper()}")
    print(f"   Capacity: {result['capacity']} persons")
    print(f"   Target Margin: {result['target_margin_pct']}% ({'Tradiro' if is_tradiro else 'Standard'})")
    
    print("\n📉 COSTS (Monthly Breakdown)")
    print(f"   1. Base Costs (Inhuur):")
    for name, amount in result['base_cost_breakdown'].items():
        if amount > 0:
            print(f"      - {name:<20}: {format_currency(amount)}")
    print(f"      ---------------------------")
    print(f"      Subtotal Inhuur:      {format_currency(result['base_cost_monthly'])}")
    
    print(f"\n   2. Added Services:")
    if result['service_cost_details']:
        for item in result['service_cost_details']:
            print(f"      - {item['name']:<20}: {format_currency(item['cost'])} ({item['calculation']})")
    else:
        print("      (None)")
    print(f"      ---------------------------")
    print(f"      Subtotal Services:    {format_currency(result['service_cost_monthly'])}")
    
    print(f"\n   ===========================")
    print(f"   TOTAL COST:           {format_currency(result['total_cost_monthly'])}")
    
    print("\n📈 REVENUE TARGETS")
    print(f"   Minimum Price (Break-even): {format_currency(result['total_cost_monthly'])}")
    print(f"   Target Price ({result['target_margin_pct']}% Margin):  {format_currency(result['min_required_price'])}")
    
    print("\n🏷️  YOUR PROPOSAL")
    print(f"   Proposed Price:       {format_currency(result['proposed_price'])}")
    print(f"   Projected Margin:     {format_currency(result['projected_margin_eur'])} ({result['projected_margin_pct']:.1f}%)")
    
    print("\n🤖 ADVICE")
    if result['is_good_deal']:
        print("   ✅ GOOD DEAL! You are above the target margin.")
        print(f"      You are making {format_currency(result['difference'])} EXTRA per month.")
    else:
        print("   ⚠️  PRICE TOO LOW.")
        print(f"      You are {format_currency(abs(result['difference']))} BELOW the target price.")
        print(f"      Try asking at least {format_currency(result['min_required_price'])}.")

    print("\n" + "="*50)

if __name__ == "__main__":
    run_bot()
