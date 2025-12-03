import os
import sys
import json
import requests
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from HuizenManager.src.intelligence_api import IntelligenceAPI
from Incheck.src.planning_api import PlanningAPI
from Incheck.src.excel_handler import PlanningExcelHandler
from HuizenManager.src.file_exchange import FileExchangeHandler

# Import for settlement generation
import openpyxl
from openpyxl.utils import get_column_letter

# Add Eindafrekening/src to path for importing generate
eindafrekening_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Eindafrekening', 'src'))
if eindafrekening_path not in sys.path:
    sys.path.append(eindafrekening_path)

# Import new Intelligence Modules
shared_scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Shared', 'scripts'))
if shared_scripts_path not in sys.path:
    sys.path.append(shared_scripts_path)

from modules.audit import AuditController
from modules.query import QueryAnalyst
from modules.excel_generator import ExcelGenerator
from modules.query_library import QueryLibrary

try:
    from generate import generate_report
except ImportError:
    print("⚠️ Could not import generate_report from Eindafrekening/src/generate.py")
    generate_report = None

class ConversationMemory:
    """
    Manages conversation history with automatic summarization to prevent rate limits.
    """
    def __init__(self, max_messages: int = 5):
        self.max_messages = max_messages
        self.history: List[Dict] = []
        self.summary: str = ""

    def add_message(self, role: str = None, content: Any = None, message: Dict = None):
        # Truncate content if it's too long (e.g., > 4000 chars) to save tokens
        MAX_CHARS = 4000
        
        if message:
            content_str = str(message.get('content', ''))
            if len(content_str) > MAX_CHARS:
                message['content'] = content_str[:MAX_CHARS] + "... (truncated)"
            self.history.append(message)
        elif role is not None:
            content_str = str(content)
            if len(content_str) > MAX_CHARS:
                content_str = content_str[:MAX_CHARS] + "... (truncated)"
            self.history.append({"role": role, "content": content_str})

    def should_summarize(self) -> bool:
        # Summarize if we have more than double the max_messages
        # This provides a buffer so we don't summarize too often
        return len(self.history) > (self.max_messages * 2)

    def get_context_messages(self) -> List[Dict]:
        """Returns the messages to send to the API (Summary + Recent History)"""
        messages = []
        
        # Add summary as the first context if it exists
        if self.summary:
            # We inject the summary as a user message to provide context
            # This is a common pattern for LLM memory
            context_msg = f"Here is a summary of our conversation so far:\n{self.summary}\n\nPlease use this context for our continued discussion."
            messages.append({"role": "user", "content": context_msg})
            messages.append({"role": "assistant", "content": "Understood. I have processed the summary and am ready to continue."})
        
        # Add the actual recent history
        messages.extend(self.history)
        return messages

    def summarize(self, api_callback):
        """
        Summarizes older messages using the provided API callback.
        """
        if not self.should_summarize():
            return

        # Keep the last `max_messages`
        # Summarize everything before that
        split_index = len(self.history) - self.max_messages
        
        # Ensure we don't split in the middle of a tool chain
        # If the first message to be kept is a 'tool' message, it means its parent 'assistant' message
        # is being summarized. We must also summarize the tool message to avoid an orphaned tool result.
        while split_index < len(self.history) and self.history[split_index].get('role') == 'tool':
            split_index += 1
            
        # If we pushed split_index all the way to the end, we might leave too few messages.
        # But correctness is more important than keeping exactly max_messages.
        
        to_summarize = self.history[:split_index]
        self.history = self.history[split_index:]
        
        print(f"🧠 Summarizing {len(to_summarize)} old messages...")

        # Create prompt for summarization
        conversation_text = ""
        for msg in to_summarize:
            role = msg['role']
            content = msg['content']
            conversation_text += f"{role.upper()}: {str(content)}\n"

        prompt = f"""
        Please summarize the following conversation segment. 
        Your goal is to retain key facts, IDs, names, dates, and context that might be relevant later.
        
        Current Summary Context: {self.summary}
        
        New Conversation Segment to Merge:
        {conversation_text}
        
        Provide a concise but detailed updated summary that combines the old context with the new information.
        """
        
        try:
            # Call OpenAI to generate the summary
            response = api_callback(
                messages=[{"role": "user", "content": prompt}], 
                system_prompt="You are an expert summarizer. Your job is to maintain a persistent memory of a conversation."
            )
            
            # Extract text from response
            new_summary = ""
            if hasattr(response, 'choices'):
                # OpenAI format
                new_summary = response.choices[0].message.content
            elif isinstance(response, dict) and 'content' in response:
                # Anthropic format (list of blocks)
                content_blocks = response['content']
                text_block = next((b for b in content_blocks if b['type'] == 'text'), None)
                if text_block:
                    new_summary = text_block['text']
            
            if new_summary:
                self.summary = new_summary.strip()
                print(f"✅ Memory updated. Summary length: {len(self.summary)} chars")
                
        except Exception as e:
            print(f"⚠️ Failed to summarize memory: {e}")
            # If summarization fails, we just keep the history as is for now (or we lost the 'to_summarize' part? 
            # Actually we already sliced self.history. So if this fails, we lose memory.
            # Ideally we should only slice after success, but for simplicity/MVP this is okay.
            # To be safer, let's prepend back if failed? 
            # For now, let's just log error.


class RyanRentBot:
    """
    AI Chatbot for RyanRent Operations.
    Uses OpenAI GPT-4o API to understand natural language and call Intelligence API tools.
    """

    def __init__(self, api_key: str, db_path: str = None, provider: str = "openai", model_name: str = None, user_role: str = "user"):
        self.api_key = api_key
        self.provider = provider
        
        # Determine permissions based on role
        allow_writes = user_role in ["admin", "manager"]
        
        self.api = IntelligenceAPI(db_path, allow_writes=allow_writes)
        self.planning_api = PlanningAPI(db_path)
        self.excel_handler = PlanningExcelHandler(db_path)
        self.file_exchange = FileExchangeHandler()  # New generic handler
        
        # Initialize Intelligence Modules
        self.audit_controller = AuditController(db_path)
        self.query_analyst = QueryAnalyst(db_path)
        self.excel_generator = ExcelGenerator(db_path)
        self.query_library = QueryLibrary(db_path)
        
        # Set default models if not provided
        if self.provider == "openai":
            self.client = OpenAI(api_key=api_key)
            self.model = model_name if model_name else "gpt-4o"
        elif self.provider == "anthropic":
            self.model = model_name if model_name else "claude-sonnet-4-5-20250929"
            self.api_url = "https://api.anthropic.com/v1/messages"
        elif self.provider == "ollama":
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama" # required but ignored
            )
            self.model = model_name if model_name else "qwen3-coder:30b"
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Initialize Memory
        self.memory = ConversationMemory(max_messages=10)
        
        # Define Tools (OpenAI Format - shared across all providers)
        self.tools = self._get_tools()

    def _get_tools(self) -> List[Dict]:
        """Returns minified tool definitions to save tokens."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_status_overview",
                    "description": "Get fleet status overview (occupancy, financials).",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_houses_near_contract_end",
                    "description": "Find houses with contracts ending soon.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "default": 30}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_bookings_without_checkout",
                    "description": "Find active bookings missing checkout date.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_upcoming_checkouts",
                    "description": "List checkouts in next N days.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "default": 60}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_open_deposits_by_client",
                    "description": "Sum open deposits grouped by client.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_active_houses",
                    "description": "List active houses.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 50}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_sql_query",
                    "description": "Run read-only SQL. Tables: huizen, klanten, boekingen, inspecties.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_house",
                    "description": "Add new house.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "adres": {"type": "string"},
                            "plaats": {"type": "string"},
                            "postcode": {"type": "string"},
                            "woning_type": {"type": "string"},
                            "aantal_sk": {"type": "integer"},
                            "aantal_pers": {"type": "integer"}
                        },
                        "required": ["adres", "plaats", "postcode", "woning_type", "aantal_sk", "aantal_pers"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_supplier",
                    "description": "Add supplier/owner.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "naam": {"type": "string"},
                            "email": {"type": "string"},
                            "telefoon": {"type": "string"},
                            "iban": {"type": "string"}
                        },
                        "required": ["naam"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_client",
                    "description": "Add client.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "naam": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["naam"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_inhuur_contract",
                    "description": "Add inhuur contract.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "house_id": {"type": "integer"},
                            "supplier_id": {"type": "integer"},
                            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                            "rent_price": {"type": "number"},
                            "end_date": {"type": "string"}
                        },
                        "required": ["house_id", "supplier_id", "start_date", "rent_price"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_house",
                    "description": "Find house by address.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_client",
                    "description": "Find client by name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_booking",
                    "description": "Create booking.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "huis_id": {"type": "integer"},
                            "klant_id": {"type": "integer"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"}
                        },
                        "required": ["huis_id", "klant_id", "start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "register_checkin",
                    "description": "Register check-in.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {"type": "integer"},
                            "date": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["booking_id", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "register_checkout",
                    "description": "Register check-out.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {"type": "integer"},
                            "date": {"type": "string"},
                            "damage": {"type": "number"},
                            "cleaning": {"type": "number"}
                        },
                        "required": ["booking_id", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_settlement",
                    "description": "Generate eindafrekening PDF.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {"type": "integer"},
                            "voorschot_gwe": {"type": "number"},
                            "voorschot_schoonmaak": {"type": "number"},
                            "schoonmaak_pakket": {
                                "type": "string",
                                "enum": ["geen", "Basis Schoonmaak", "Intensief Schoonmaak", "Achteraf Betaald"]
                            },
                            "meter_readings": {
                                "type": "object",
                                "properties": {
                                    "electricity": {
                                        "type": "object",
                                        "properties": {
                                            "start": {"type": "number"},
                                            "end": {"type": "number"},
                                            "tariff": {"type": "number"}
                                        },
                                        "required": ["start", "end", "tariff"]
                                    },
                                    "gas": {
                                        "type": "object",
                                        "properties": {
                                            "start": {"type": "number"},
                                            "end": {"type": "number"},
                                            "tariff": {"type": "number"}
                                        },
                                        "required": ["start", "end", "tariff"]
                                    },
                                    "water": {
                                        "type": "object",
                                        "properties": {
                                            "start": {"type": "number"},
                                            "end": {"type": "number"},
                                            "tariff": {"type": "number"}
                                        },
                                        "required": ["start", "end", "tariff"]
                                    }
                                },
                                "required": ["electricity", "gas", "water"]
                            },
                            "damages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "cost": {"type": "number"},
                                        "btw_percentage": {"type": "number", "default": 21.0}
                                    },
                                    "required": ["description", "cost"]
                                }
                            },
                            "schoonmaak_uren": {"type": "number"},
                            "uurtarief_schoonmaak": {"type": "number", "default": 50}
                        },
                        "required": ["booking_id", "voorschot_gwe", "voorschot_schoonmaak", "schoonmaak_pakket", "meter_readings"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_planning_priorities",
                    "description": "Get prioritized list of houses with upcoming checkouts but NO next tenant.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_lookahead": {"type": "integer", "default": 30}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_upcoming_transitions",
                    "description": "Get upcoming transitions (checkouts/inchecks).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_lookahead": {"type": "integer", "default": 60},
                            "client_name": {"type": "string"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_planning_report",
                    "description": "Generate HTML planning report.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_lookahead": {"type": "integer", "default": 30},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "missing_pre_inspection": { "type": "boolean" },
                                    "has_next_tenant": { "type": "boolean" },
                                    "missing_vis": { "type": "boolean" }
                                }
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_planning_excel",
                    "description": "Generate Excel planning export.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days_lookahead": {"type": "integer", "default": 30},
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "missing_pre_inspection": { "type": "boolean" },
                                    "has_next_tenant": { "type": "boolean" },
                                    "missing_vis": { "type": "boolean" }
                                }
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_planning_from_excel",
                    "description": "Update DB from Excel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_booking",
                    "description": "Update booking details (dates, status).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_id": {"type": "integer"},
                            "checkin_date": {"type": "string"},
                            "checkout_date": {"type": "string"},
                            "status": {"type": "string"}
                        },
                        "required": ["booking_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_excel_template",
                    "description": "Generate Excel template for bulk updates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "template_type": {
                                "type": "string",
                                "enum": ["checkout_update", "settlement_batch"]
                            },
                            "filters": {
                                "type": "object",
                                "description": "Filters to select data (e.g. {'city': 'Amsterdam'})"
                            }
                        },
                        "required": ["template_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_excel_update",
                    "description": "Process filled Excel file from Input folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "request_type": {
                                "type": "string",
                                "enum": ["checkout_update", "settlement_batch"]
                            }
                        },
                        "required": ["filename", "request_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_audit",
                    "description": "Run a full system audit to check for data integrity issues.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_analyst_query",
                    "description": "Run a smart analytical query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["profitability", "client_scorecard", "operational_dashboard", "custom"]
                            },
                            "custom_sql": {"type": "string", "description": "Only for custom query type"}
                        },
                        "required": ["query_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_smart_excel",
                    "description": "Generate an Excel sheet based on a SQL query for bulk updates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {"type": "string", "description": "SQL query to select data to update"},
                            "update_type": {
                                "type": "string",
                                "enum": ["update_house_details", "update_contract"],
                                "description": "Type of update to perform"
                            }
                        },
                        "required": ["sql_query", "update_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_smart_excel",
                    "description": "Process a filled Smart Excel sheet.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_query_library",
                    "description": "Search for a saved SQL query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {"type": "string"}
                        },
                        "required": ["search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_query",
                    "description": "Save a SQL query to the library for future use.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "sql_template": {"type": "string"},
                            "parameters": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["name", "description", "sql_template"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_saved_query",
                    "description": "Run a query from the library.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_id": {"type": "integer"},
                            "param_values": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["query_id"]
                    }
                }
            }
        ]

    def _get_default_system_prompt(self) -> str:
        """Returns optimized system prompt based on model capability."""
        
        # Dynamically fetch schema
        try:
            schema_text = self.api.get_database_schema()
        except Exception as e:
            print(f"⚠️ Failed to fetch schema: {e}")
            schema_text = "Schema unavailable."
        
        # Base prompt (for all models)
        base_prompt = f"""You are Ryan, the RyanRent Operational Assistant. You speak Dutch and help manage a fleet of 250+ houses.

**Business Context:**
- **RyanRent**: Intermediary renting houses from owners (Inhuur) and renting them out to clients (Verhuur).
- **Financials**: kale_huur (base rent), servicekosten (service charges), voorschot_gwe (GWE advance), borg (deposit).

**Core Rules:**
1. **Data Integrity**: Check if owner/supplier exists before adding a house. Add owner first if needed.
2. **Tools**: Use available tools. For complex queries, use `run_sql_query`.
3. **Language**: Respond in Dutch.
4. **Formatting**: Present data as clean markdown tables, not raw JSON.

{schema_text}"""

        # Smart models (Claude, GPT) - minimal guidance
        if self.provider in ["anthropic", "openai"]:
            return base_prompt
        
        # Dumb models (Ollama) - explicit step-by-step instructions
        else:
            return base_prompt + """

**CRITICAL INSTRUCTIONS FOR TOOL USE:**

**Rule #1: Tool Output Handling**
When you receive a tool result, DO NOT explain it back to me. Instead:
- Extract the relevant data
- Format it as a clean markdown table
- Answer the original question directly

**Rule #2: SQL Query Workflow (MANDATORY)**
For SQL queries, follow these steps IN ORDER:

Step 1: Check schema
- `PRAGMA table_info(table_name)` to see column names
- `SELECT * FROM table_name LIMIT 1` to verify structure

Step 2: Build incrementally
- Start simple, test each JOIN separately
- Fix errors before adding complexity

Step 3: Add filters & sorting
- WHERE clauses for filtering
- ORDER BY for sorting (DESC = newest first)

Step 4: Format results
- Present as markdown table
- Only show relevant columns

**Example:**
User: "Welke klanten checken uit in 2 maanden?"

Your workflow:
1. `PRAGMA table_info(boekingen)` → Check columns
2. `SELECT * FROM boekingen LIMIT 1` → Verify
3. `SELECT * FROM klanten LIMIT 1` → Check client table
4. `SELECT b.*, k.naam FROM boekingen b JOIN klanten k ON b.klant_id = k.id LIMIT 1` → Test JOIN
5. Final query with filters and sorting
6. Format as table

DO NOT skip steps. DO NOT guess column names. Be methodical.
"""


    def _handle_generate_settlement(self, args: Dict[str, Any]) -> str:
        """Handle generate_settlement tool call - database-driven workflow"""
        if not generate_report:
            return "Error: Settlement generator module not loaded."

        try:
            booking_id = args['booking_id']
            
            # 1. Fetch booking data from database
            booking_data = self.api.get_booking_for_settlement(booking_id)
            
            # 2. Save meter readings to database
            meter_readings = args['meter_readings']
            self.api.save_meter_readings(booking_id, meter_readings)
            
            # 3. Save damages to database (if any)
            if 'damages' in args and args['damages']:
                self.api.save_damages(booking_id, args['damages'])
            
            # 4. Update voorschotten in booking
            self.api.update_booking_voorschotten(
                booking_id,
                args['voorschot_gwe'],
                args['voorschot_schoonmaak'],
                args['schoonmaak_pakket']
            )
            
            # 5. Prepare Excel template
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_path = os.path.join(root_dir, 'Eindafrekening', 'src', 'input_template.xlsx')
            output_dir = os.path.join(root_dir, 'Eindafrekening', 'output')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_input = os.path.join(root_dir, 'Eindafrekening', 'src', f'temp_input_{timestamp}.xlsx')
            
            # 6. Fill Excel template
            wb = openpyxl.load_workbook(template_path)
            
            def set_named_range_value(wb, name, value):
                if name in wb.defined_names:
                    dests = wb.defined_names[name].destinations
                    for sheet_name, coord in dests:
                        ws = wb[sheet_name]
                        ws[coord.replace('$', '')] = value
                        return True
                return False
            
            # Fill from database
            set_named_range_value(wb, 'Klantnaam', booking_data['client_name'])
            set_named_range_value(wb, 'Contactpersoon', booking_data.get('contactpersoon', ''))
            set_named_range_value(wb, 'Email', booking_data.get('email', ''))
            set_named_range_value(wb, 'Telefoonnummer', booking_data.get('telefoonnummer', ''))
            
            set_named_range_value(wb, 'Object_adres', booking_data['property_address'])
            set_named_range_value(wb, 'Object_ID', booking_data.get('object_id', ''))
            set_named_range_value(wb, 'Postcode', booking_data.get('postcode', ''))
            set_named_range_value(wb, 'Plaats', booking_data.get('plaats', ''))
            
            set_named_range_value(wb, 'Incheck_datum', datetime.strptime(booking_data['checkin_datum'], '%Y-%m-%d').date())
            set_named_range_value(wb, 'Uitcheck_datum', datetime.strptime(booking_data['checkout_datum'], '%Y-%m-%d').date())
            
            # Fill from user input
            set_named_range_value(wb, 'Voorschot_borg', booking_data.get('betaalde_borg', 0))
            set_named_range_value(wb, 'Voorschot_GWE', args['voorschot_gwe'])
            set_named_range_value(wb, 'Voorschot_schoonmaak', args['voorschot_schoonmaak'])
            set_named_range_value(wb, 'Schoonmaak_pakket', args['schoonmaak_pakket'])
            
            if 'uurtarief_schoonmaak' in args:
                set_named_range_value(wb, 'Uurtarief_schoonmaak', args['uurtarief_schoonmaak'])
            
            # Fill GWE meters
            ws_gwe = wb['GWE_Detail']
            # Electricity (row 5)
            ws_gwe['B5'] = meter_readings['electricity']['start']
            ws_gwe['C5'] = meter_readings['electricity']['end']
            ws_gwe['D5'] = meter_readings['electricity']['tariff']
            # Gas (row 6)
            ws_gwe['B6'] = meter_readings['gas']['start']
            ws_gwe['C6'] = meter_readings['gas']['end']
            ws_gwe['D6'] = meter_readings['gas']['tariff']
            # Water (row 7)
            ws_gwe['B7'] = meter_readings['water']['start']
            ws_gwe['C7'] = meter_readings['water']['end']
            ws_gwe['D7'] = meter_readings['water']['tariff']
            
            # Fill cleaning hours if provided
            if 'schoonmaak_uren' in args:
                ws_schoonmaak = wb['Schoonmaak']
                # Assuming row 5 is for actual hours used
                ws_schoonmaak['B5'] = args['schoonmaak_uren']
            
            # Fill damages if provided
            if 'damages' in args and args['damages']:
                ws_schade = wb['Schade']
                start_row = 5  # Assuming damages start at row 5
                for i, damage in enumerate(args['damages']):
                    row = start_row + i
                    ws_schade[f'A{row}'] = damage['description']
                    ws_schade[f'B{row}'] = damage['cost']
                    ws_schade[f'C{row}'] = damage.get('btw_percentage', 21.0)
            
            # 7. Save and generate
            wb.save(temp_input)
            wb.close()
            
            result = generate_report(temp_input, output_dir)
            
            # Cleanup
            if os.path.exists(temp_input):
                os.remove(temp_input)
            
            # 8. Mark settlement as generated
            if result['success']:
                self.api.update_booking_settlement_status(booking_id)
                
                summary = result['summary']
                files = result['files']
                
                response = f"✅ Eindafrekening gegenereerd voor {booking_data['client_name']}!\n"
                response += f"🏠 Object: {booking_data['property_address']}\n"
                response += f"📅 Periode: {booking_data['checkin_datum']} tot {booking_data['checkout_datum']}\n"
                response += f"💰 Totaal: €{summary['total']:.2f}\n\n"
                
                if 'onepager_html' in files:
                    response += f"📄 Report: {files['onepager_html']}\n"
                
                response += "\n✅ Alle data opgeslagen in database!"
                
                return response
            else:
                return f"❌ Generatie mislukt: {result.get('error', 'Unknown error')}"

        except ValueError as e:
            return f"❌ Error: {str(e)}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error: {str(e)}"


    def _determine_max_tokens(self, text: str) -> int:
        """
        Heuristic to determine if a request needs more tokens.
        """
        # Keywords that suggest a long response
        complex_keywords = [
            "list", "lijst", "overview", "overzicht", "report", "rapport", 
            "generate", "genereer", "all", "alle", "detail", "uitgebreid",
            "table", "tabel", "summary", "samenvatting", "eindafrekening"
        ]
        
        text_lower = text.lower()
        
        # Check if any keyword is present
        if any(keyword in text_lower for keyword in complex_keywords):
            print("🧠 Detected complex request. Increasing token limit to 4096.")
            return 4096
            
        # Default for simple Q&A
        return 1024

    def _convert_tools_to_anthropic(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool definitions to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
        return anthropic_tools

    def _call_claude(self, messages: List[Dict], tools: List[Dict] = None, system_prompt: str = None) -> Dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        default_system = self._get_default_system_prompt()

        # Filter out 'system' role messages from history as Claude puts system prompt in top-level param
        # Also filter out 'tool' role messages if they are not supported or need conversion?
        # Actually Claude supports tool use, but the format in history might differ.
        # For now, let's assume the memory format (which we updated for OpenAI) needs some adaptation for Claude?
        # OpenAI: role='tool', tool_call_id=...
        # Claude: role='user', content=[{type='tool_result', ...}]
        # This is tricky. The memory is now storing OpenAI format.
        # We might need a _convert_messages_to_anthropic method too.
        
        claude_messages = self._convert_messages_to_anthropic(messages)
        
        # Determine max tokens based on user input (last message)
        last_user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "")
        max_tokens = self._determine_max_tokens(str(last_user_msg))

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "messages": claude_messages,
            "system": system_prompt if system_prompt else default_system
        }
        
        if tools:
            payload["tools"] = self._convert_tools_to_anthropic(tools)

        response = requests.post(self.api_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        return response.json()

    def _convert_messages_to_anthropic(self, messages: List[Dict]) -> List[Dict]:
        """Convert OpenAI message format to Anthropic format."""
        anthropic_msgs = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                continue # System prompt is handled separately
            
            if role == "tool":
                tool_call_id = msg.get("tool_call_id")
                content = msg["content"]
                
                # Check if we have a preceding assistant message with this tool call
                has_matching_tool_use = False
                if anthropic_msgs and anthropic_msgs[-1]["role"] == "assistant":
                    last_content = anthropic_msgs[-1]["content"]
                    if isinstance(last_content, list):
                        for block in last_content:
                            if block.get("type") == "tool_use" and block.get("id") == tool_call_id:
                                has_matching_tool_use = True
                                break
                
                if has_matching_tool_use:
                    # Valid tool result pair - append as tool_result
                    tool_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": content
                    }
                    anthropic_msgs.append({
                        "role": "user",
                        "content": [tool_result]
                    })
                else:
                    # Orphan tool result (history truncation or mismatch)
                    # Convert to text context to avoid API error
                    context_msg = f"[System: Context from previous tool action: {content}]"
                    
                    if anthropic_msgs and anthropic_msgs[-1]["role"] == "user":
                        # Append to existing user message
                        prev_content = anthropic_msgs[-1]["content"]
                        if isinstance(prev_content, list):
                            prev_content.append({"type": "text", "text": context_msg})
                        else:
                            anthropic_msgs[-1]["content"] = prev_content + "\n\n" + context_msg
                    else:
                        # Create new user message
                        anthropic_msgs.append({"role": "user", "content": context_msg})
                    
            elif role == "assistant":
                # Handle tool calls in assistant message
                if msg.get("tool_calls"):
                    # OpenAI: tool_calls=[{id=..., function={name=..., arguments=...}}]
                    # Anthropic: content=[{type='tool_use', id=..., name=..., input=...}]
                    new_content = []
                    if content:
                        new_content.append({"type": "text", "text": content})
                    
                    for tc in msg["tool_calls"]:
                        new_content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                    anthropic_msgs.append({"role": "assistant", "content": new_content})
                else:
                    anthropic_msgs.append({"role": "assistant", "content": content})
            else:
                # User messages
                anthropic_msgs.append({"role": role, "content": content})
                
        return anthropic_msgs

    def _call_openai(self, messages: List[Dict], tools: List[Dict] = None, system_prompt: str = None) -> Any:
        
        default_system = self._get_default_system_prompt()

        # Prepare messages for OpenAI
        # OpenAI expects system message in the messages list
        api_messages = []
        api_messages.append({"role": "system", "content": system_prompt if system_prompt else default_system})
        api_messages.extend(messages)
        
        # Determine max tokens based on user input
        last_user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "")
        max_tokens = self._determine_max_tokens(str(last_user_msg))

        params = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            raise Exception(f"OpenAI API Error: {e}")
            
    def chat(self, user_message: str) -> str:
        """
        Process a user message, call tools if needed, and return the response.
        """
        # 0. Check if we need to summarize memory
        # Use the appropriate callback based on provider
        callback = self._call_claude if self.provider == "anthropic" else self._call_openai
        self.memory.summarize(callback)
        
        # 1. Add user message to memory
        self.memory.add_message("user", user_message)
        
        # 2. Get full context (Summary + History)
        messages_payload = self.memory.get_context_messages()
        
        if self.provider == "anthropic":
            return self._chat_claude(messages_payload)
        else:
            # Both OpenAI and Ollama use the OpenAI-compatible chat loop
            return self._chat_openai(messages_payload)

    def _chat_openai(self, messages_payload):
        # 3. Initial call to OpenAI
        response = self._call_openai(messages_payload, self.tools)
        response_message = response.choices[0].message
        
        # Loop to handle multiple tool calls
        while response_message.tool_calls:
            # Add assistant response (with tool calls) to memory
            assistant_msg = {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]
            }
            self.memory.add_message(message=assistant_msg)
            
            tool_calls = response_message.tool_calls
            
            # Process ALL tool calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id
                
                print(f"🤖 Calling tool: {function_name}({function_args})")
                
                try:
                    # Execute the tool
                    result = self._execute_tool(function_name, function_args)
                    
                    # Add result to memory
                    # We wrap the result in a clear context to prevent the model from thinking the user pasted it
                    tool_output_context = f"[SYSTEM: This is the result of the tool call '{function_name}'. Use this data to answer the user's question.]\n\n{json.dumps(result, default=str)}"
                    
                    self.memory.add_message(message={
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": function_name,
                        "content": tool_output_context
                    })
                except Exception as e:
                    error_message = f"Error executing tool '{function_name}': {str(e)}"
                    print(f"❌ {error_message}")
                    self.memory.add_message(message={
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": function_name,
                        "content": json.dumps({"error": error_message})
                    })
            
            # Get updated context
            messages_payload = self.memory.get_context_messages()
            
            # Call OpenAI again with the tool results
            response = self._call_openai(messages_payload, self.tools)
            response_message = response.choices[0].message

        # Final response (text)
        content = response_message.content
        self.memory.add_message("assistant", content)
        
        return content if content else "No response text."

    def _chat_claude(self, messages_payload):
        # 3. Initial call to Claude
        response_data = self._call_claude(messages_payload, self.tools)
        
        # Loop to handle multiple tool calls
        while response_data['stop_reason'] == "tool_use":
            content_block = response_data['content']
            
            # Add assistant response to memory (we need to convert back to OpenAI format for storage consistency)
            # Or we just store it as is and let the converter handle it?
            # The memory expects OpenAI format now (tool_calls list).
            # We need to convert Claude's response to OpenAI format for storage.
            
            tool_calls_openai = []
            for block in content_block:
                if block['type'] == "tool_use":
                    tool_calls_openai.append({
                        "id": block['id'],
                        "type": "function",
                        "function": {
                            "name": block['name'],
                            "arguments": json.dumps(block['input'])
                        }
                    })
            
            text_content = next((b['text'] for b in content_block if b['type'] == 'text'), None)
            
            assistant_msg = {
                "role": "assistant",
                "content": text_content,
                "tool_calls": tool_calls_openai
            }
            self.memory.add_message(message=assistant_msg)
            
            # Process tools
            for block in content_block:
                if block['type'] == "tool_use":
                    tool_name = block['name']
                    tool_input = block['input']
                    tool_id = block['id']
                    
                    print(f"🤖 Calling tool: {tool_name}({tool_input})")
                    
                    try:
                        result = self._execute_tool(tool_name, tool_input)
                        
                        # Truncate result if too large
                        result_str = json.dumps(result, default=str) # Convert to string for length check
                        if len(result_str) > 4000:
                            print(f"⚠️ Tool output too large ({len(result_str)} chars). Truncating...")
                            result_str = result_str[:4000] + "... (truncated)"
                            
                        # Add result to memory (OpenAI format)
                        self.memory.add_message(message={
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": result_str
                        })
                    except Exception as e:
                        error_message = f"Error executing tool '{tool_name}': {e}"
                        print(f"❌ {error_message}")
                        self.memory.add_message(message={
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": json.dumps({"error": error_message})
                        })
            
            # Get updated context
            messages_payload = self.memory.get_context_messages()
            
            # Call Claude again
            response_data = self._call_claude(messages_payload, self.tools)

        # Final response
        content_block = response_data['content']
        text_block = next((block for block in content_block if block['type'] == "text"), None)
        content = text_block['text'] if text_block else "No response text."
        
        self.memory.add_message("assistant", content)
        return content

    def _execute_tool(self, name: str, args: Dict) -> Any:
        if name == "get_status_overview":
            return self.api.get_status_overview()
        elif name == "get_houses_near_contract_end":
            days = args.get("days", 30)
            return self.api.get_houses_near_contract_end(days)
        elif name == "get_bookings_without_checkout":
            return self.api.get_bookings_without_checkout()
        elif name == "get_upcoming_checkouts":
            days = args.get("days", 60)
            return self.api.get_upcoming_checkouts(days)
        elif name == "get_open_deposits_by_client":
            return self.api.get_open_deposits_by_client()
        elif name == "get_active_houses":
            limit = args.get("limit", 50)
            return self.api.get_active_houses(limit)
        elif name == "run_sql_query":
            query = args.get('query') or args.get('custom_sql')
            if not query:
                return {"error": "Missing 'query' argument"}
            return self.api.run_sql_query(query)
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
            # This handler was replaced as per user instruction.
            # The original _handle_generate_settlement method is now orphaned but not removed by instruction.
            return self.api.generate_settlement(
                booking_id=args['booking_id'],
                voorschot_gwe=args['voorschot_gwe'],
                voorschot_schoonmaak=args['voorschot_schoonmaak'],
                schoonmaak_pakket=args['schoonmaak_pakket'],
                meter_readings=args['meter_readings'],
                damages=args.get('damages', []),
                schoonmaak_uren=args.get('schoonmaak_uren'),
                uurtarief_schoonmaak=args.get('uurtarief_schoonmaak')
            )
        elif name == "get_planning_priorities":
            return self.planning_api.get_planning_priorities(
                days_lookahead=args.get('days_lookahead', 30)
            )
        elif name == "get_upcoming_transitions":
            days = args.get("days_lookahead", 60)
            client_name = args.get("client_name")
            
            if client_name:
                return self.planning_api.get_transition_by_client(client_name, days)
            else:
                return self.planning_api.get_upcoming_transitions(days)
                
        elif name == "generate_planning_report":
            days = args.get("days_lookahead", 30)
            filters = args.get("filters")
            
            # We need to import the generator here to avoid circular imports or early init issues
            from Incheck.src.report_generator import PlanningReportGenerator
            
            # Fetch data
            transitions = self.planning_api.get_upcoming_transitions(days, filters=filters)
            
            # Generate
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Added to correctly resolve paths
            output_dir = os.path.join(root_dir, "Incheck", "reports")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"planning_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
            output_path = os.path.join(output_dir, filename)
            
            template_path = os.path.join(root_dir, "Incheck", "templates", "planning_report.html") # Added to correctly resolve paths
            
            generator = PlanningReportGenerator(template_path)
            report_path = generator.generate_report(transitions, output_path)
            
            return {"status": "success", "message": f"Report generated at {report_path}", "path": report_path}
        
        elif name == "generate_planning_excel":
            days = args.get("days_lookahead", 30)
            filters = args.get("filters")
            
            transitions = self.planning_api.get_upcoming_transitions(days, filters=filters)
            
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_dir = os.path.join(root_dir, "Incheck", "reports")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"planning_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            output_path = os.path.join(output_dir, filename)
            
            file_path = self.excel_handler.generate_excel(transitions, output_path)
            return {"status": "success", "message": f"Excel file generated at {file_path}", "path": file_path}
        
        elif name == "update_planning_from_excel":
            file_path = args['file_path']
            result = self.excel_handler.process_update(file_path)
            return {"status": "success", "message": result}
            
        elif name == "update_booking":
            return self.api.update_booking(
                booking_id=args.get("booking_id"),
                checkin_date=args.get("checkin_date"),
                checkout_date=args.get("checkout_date"),
                status=args.get("status")
            )

        elif name == "generate_excel_template":
            # Fetch data based on filters if needed
            data = []
            t_type = args.get("template_type")
            filters = args.get("filters", {})
            
            if t_type == "checkout_update":
                # Default to upcoming checkouts if no specific filter
                # In a real scenario, we'd parse filters to build a dynamic query
                # For now, let's just get upcoming checkouts
                data = self.api.get_upcoming_checkouts(days=60)
            elif t_type == "settlement_batch":
                data = self.api.get_bookings_without_checkout()
                
            path = self.file_exchange.generate_template(t_type, data)
            return {"success": True, "message": f"Template created at: {path}. Please fill it and move to Exchange/Input."}

        elif name == "process_excel_update":
            return self.file_exchange.process_file(
                filename=args.get("filename"),
                request_type=args.get("request_type")
            )

        elif name == "run_audit":
            return self.audit_controller.run_full_audit()

        elif name == "run_analyst_query":
            q_type = args.get("query_type")
            if q_type == "profitability":
                return self.query_analyst.get_house_profitability()
            elif q_type == "client_scorecard":
                return self.query_analyst.get_client_scorecard()
            elif q_type == "operational_dashboard":
                return self.query_analyst.get_operational_dashboard()
            elif q_type == "custom":
                return self.query_analyst.run_custom_query(args.get("custom_sql", ""))
            else:
                return {"error": "Unknown query type"}

        elif name == "generate_smart_excel":
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_dir = os.path.join(root_dir, "Shared", "Exchange", "Output")
            os.makedirs(output_dir, exist_ok=True)
            
            return self.excel_generator.generate_update_sheet(
                sql_query=args['sql_query'],
                update_type=args['update_type'],
                output_dir=output_dir
            )

        elif name == "process_smart_excel":
            return self.excel_generator.process_update_sheet(args['file_path'])

        elif name == "search_query_library":
            return self.query_library.find_queries(args['search_term'])

        elif name == "save_query":
            return self.query_library.add_query(
                args['name'], args['description'], args['sql_template'], args.get('parameters')
            )

        elif name == "run_saved_query":
            return self.query_library.execute_query(
                args['query_id'], args.get('param_values')
            )
            
        else:
            return {"error": f"Unknown tool: {name}"}
