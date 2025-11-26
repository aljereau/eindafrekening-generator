import os
import sys
import json
import requests
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.intelligence_api import IntelligenceAPI

class RyanRentBot:
    """
    AI Chatbot for RyanRent Operations.
    Uses Anthropic Claude API (via requests) to understand natural language and call Intelligence API tools.
    """

    def __init__(self, api_key: str, db_path: str = None):
        self.api_key = api_key
        self.api = IntelligenceAPI(db_path)
        self.model = "claude-sonnet-4-5-20250929"
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.history = []
        
        # Define Tools for Claude
        self.tools = [
            {
                "name": "get_status_overview",
                "description": "Get a high-level dashboard of the operation (Total houses, Occupancy, Expiring contracts count, etc). Use this for general status questions.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                }
            },
            {
                "name": "get_houses_near_contract_end",
                "description": "Find houses with INHUUR contracts (agreements with owners) that are expiring soon. Use this when asked about expiring contracts or 'aflopende contracten'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look ahead (default 30)",
                            "default": 30
                        }
                    },
                }
            },
            {
                "name": "get_bookings_without_checkout",
                "description": "Find bookings that have passed their checkout date but have no checkout registered. These are 'ghost bookings' or missing checkouts.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                }
            },
            {
                "name": "get_open_deposits_by_client",
                "description": "Get a list of clients who have open deposits (borg) that haven't been fully refunded or settled.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                }
            },
            {
                "name": "get_active_houses",
                "description": "Get a list of active houses with their Object IDs and addresses. Use this when asked for a full list or overview of all houses.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of houses to return (default 50)",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "run_sql_query",
                "description": "Run a read-only SQL query on the database. Use this to answer questions that other tools cannot handle. Tables: huizen, klanten, leveranciers, inhuur_contracten, verhuur_contracten, boekingen, borg_transacties.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The SQL SELECT query to execute"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_house",
                "description": "Add a new house to the system.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "adres": {"type": "string", "description": "Full address (e.g. 'Street 1, City')"},
                        "plaats": {"type": "string", "description": "City"},
                        "postcode": {"type": "string", "description": "Postal code"},
                        "woning_type": {"type": "string", "description": "Type (Appartement, Eengezinswoning)"},
                        "aantal_sk": {"type": "integer", "description": "Number of bedrooms"},
                        "aantal_pers": {"type": "integer", "description": "Max capacity"}
                    },
                    "required": ["adres", "plaats", "postcode", "woning_type", "aantal_sk", "aantal_pers"]
                }
            },
            {
                "name": "add_supplier",
                "description": "Add a new supplier or owner.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "naam": {"type": "string", "description": "Name of supplier/owner"},
                        "email": {"type": "string", "description": "Email address (optional)"},
                        "telefoon": {"type": "string", "description": "Phone number (optional)"},
                        "iban": {"type": "string", "description": "IBAN (optional)"}
                    },
                    "required": ["naam"]
                }
            },
            {
                "name": "add_client",
                "description": "Add a new client.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "naam": {"type": "string", "description": "Name of client"},
                        "email": {"type": "string", "description": "Email address (optional)"}
                    },
                    "required": ["naam"]
                }
            },
            {
                "name": "add_inhuur_contract",
                "description": "Add a new inhuur contract (owner contract).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "house_id": {"type": "integer", "description": "ID of the house"},
                        "supplier_id": {"type": "integer", "description": "ID of the supplier/owner"},
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "rent_price": {"type": "number", "description": "Monthly rent (kale huur)"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD (optional)"}
                    },
                    "required": ["house_id", "supplier_id", "start_date", "rent_price"]
                }
            },
            {
                "name": "find_house",
                "description": "Find a house by address (partial match). Returns ID and address.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Address part (e.g. 'Nunspeet')"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "find_client",
                "description": "Find a client by name (partial match). Returns ID and name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Name part (e.g. 'Tradiro')"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_booking",
                "description": "Create a new booking for a house. Requires house ID, client ID, and dates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "huis_id": {"type": "integer", "description": "ID of the house"},
                        "klant_id": {"type": "integer", "description": "ID of the client"},
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"}
                    },
                    "required": ["huis_id", "klant_id", "start_date", "end_date"]
                }
            },
            {
                "name": "register_checkin",
                "description": "Register a check-in event for a booking.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "booking_id": {"type": "integer", "description": "ID of the booking"},
                        "date": {"type": "string", "description": "YYYY-MM-DD"},
                        "notes": {"type": "string", "description": "Optional notes"}
                    },
                    "required": ["booking_id", "date"]
                }
            },
            {
                "name": "register_checkout",
                "description": "Register a check-out event for a booking.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "booking_id": {"type": "integer", "description": "ID of the booking"},
                        "date": {"type": "string", "description": "YYYY-MM-DD"},
                        "damage": {"type": "number", "description": "Estimated damage cost"},
                        "cleaning": {"type": "number", "description": "Cleaning cost"}
                    },
                    "required": ["booking_id", "date"]
                }
            },
            {
                "name": "generate_settlement",
                "description": "Generate a PDF settlement (Eindafrekening) for a booking. Requires financial details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string", "description": "Name of the client"},
                        "house_address": {"type": "string", "description": "Address of the house"},
                        "checkin_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "checkout_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "deposit_held": {"type": "number", "description": "Total deposit held (e.g. 500)"},
                        "deposit_returned": {"type": "number", "description": "Amount to return to client"},
                        "cleaning_cost": {"type": "number", "description": "Extra cleaning costs (deducted)"},
                        "damage_cost": {"type": "number", "description": "Damage costs (deducted)"},
                        "gwe_usage": {"type": "number", "description": "Total GWE usage cost (optional)"}
                    },
                    "required": ["client_name", "house_address", "checkin_date", "checkout_date", "deposit_held", "deposit_returned", "cleaning_cost", "damage_cost"]
                }
            }
        ]

    def _call_claude(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": messages,
            "messages": messages,
            "system": """You are the RyanRent Operational Assistant. You speak Dutch. You help manage a fleet of 250+ houses. 

**Core Rules:**
1. **Data Integrity**: When adding a new house, ALWAYS check if the owner/supplier exists first using `find_client` or `run_sql_query`. If not, ask the user for owner details and add the owner FIRST using `add_supplier`.
2. **Memory**: Remember context from previous messages. If a user refers to "that house" or "the contract", use the IDs from the recent conversation history.
3. **Tools**: Use available tools to answer questions. If a specific tool doesn't exist, use `run_sql_query` to fetch data.
4. **Language**: Summarize all results clearly in Dutch."""
        }
        if tools:
            payload["tools"] = tools

        response = requests.post(self.api_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return response.json()

    def chat(self, user_message: str) -> str:
        """
        Process a user message, call tools if needed, and return the response.
        """
        # Append user message to history
        self.history.append({"role": "user", "content": user_message})
        
        # 1. Initial call to Claude
        response_data = self._call_claude(self.history, self.tools)
        
        # Loop to handle multiple tool calls
        while response_data['stop_reason'] == "tool_use":
            content_block = response_data['content']
            
            # Add assistant response to history
            self.history.append({"role": "assistant", "content": content_block})
            
            tool_results = []
            
            # Process ALL tool uses in the content block
            for block in content_block:
                if block['type'] == "tool_use":
                    tool_name = block['name']
                    tool_input = block['input']
                    tool_id = block['id']
                    
                    print(f"🤖 Calling tool: {tool_name}({tool_input})")
                    
                    # Execute the tool
                    result = self._execute_tool(tool_name, tool_input)
                    
                    # Add result to list
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result, default=str)
                    })
            
            # Add ALL tool results in a single user message
            self.history.append({
                "role": "user",
                "content": tool_results
            })
            
            # Call Claude again with the tool results
            response_data = self._call_claude(self.history, self.tools)

        # Final response (text)
        content_block = response_data['content']
        self.history.append({"role": "assistant", "content": content_block})
        
        text_block = next((block for block in content_block if block['type'] == "text"), None)
        return text_block['text'] if text_block else "No response text."

    def _execute_tool(self, name: str, args: Dict) -> Any:
        if name == "get_status_overview":
            return self.api.get_status_overview()
        elif name == "get_houses_near_contract_end":
            days = args.get("days", 30)
            return self.api.get_houses_near_contract_end(days)
        elif name == "get_bookings_without_checkout":
            return self.api.get_bookings_without_checkout()
        elif name == "get_open_deposits_by_client":
            return self.api.get_open_deposits_by_client()
        elif name == "get_active_houses":
            limit = args.get("limit", 50)
            return self.api.get_active_houses(limit)
        elif name == "run_sql_query":
            return self.api.run_sql_query(args['query'])
        elif name == "add_house":
            return self.api.add_house(
                args['adres'], args['plaats'], args['postcode'], 
                args['woning_type'], args['aantal_sk'], args['aantal_pers']
            )
        elif name == "add_supplier":
            return self.api.add_supplier(
                args['naam'], args.get('email'), args.get('telefoon'), args.get('iban')
            )
        elif name == "add_client":
            return self.api.add_client(args['naam'], args.get('email'))
        elif name == "add_inhuur_contract":
            return self.api.add_inhuur_contract(
                args['house_id'], args['supplier_id'], args['start_date'], 
                args['rent_price'], args.get('end_date')
            )
        elif name == "find_house":
            return self.api.find_house(args['query'])
        elif name == "find_client":
            return self.api.find_client(args['query'])
        elif name == "create_booking":
            return self.api.create_booking(
                args['huis_id'], args['klant_id'], args['start_date'], args['end_date']
            )
        elif name == "register_checkin":
            return self.api.register_checkin(
                args['booking_id'], args['date'], args.get('notes', "")
            )
        elif name == "register_checkout":
            return self.api.register_checkout(
                args['booking_id'], args['date'], args.get('damage', 0), args.get('cleaning', 0)
            )
        elif name == "generate_settlement":
            return self.api.generate_settlement(
                client_name=args['client_name'],
                house_address=args['house_address'],
                checkin_date=args['checkin_date'],
                checkout_date=args['checkout_date'],
                deposit_held=args['deposit_held'],
                deposit_returned=args['deposit_returned'],
                cleaning_cost=args['cleaning_cost'],
                damage_cost=args['damage_cost'],
                gwe_usage=args.get('gwe_usage', 0.0)
            )
        else:
            return {"error": f"Unknown tool: {name}"}
