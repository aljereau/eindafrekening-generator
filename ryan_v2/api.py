from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from pydantic import BaseModel
import json
import logging
import asyncio

from .agent import RyanAgent
from . import config
from . import settings_service

# Create exports directory if not exists
EXPORTS_DIR = Path(__file__).parent / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ryan_api")

app = FastAPI(title="RyanRent Agent V2")

# Mount exports for file downloads - REPLACED with custom endpoint for headers
from fastapi.responses import FileResponse
from fastapi import HTTPException

@app.get("/exports/{filename}")
async def download_file(filename: str):
    file_path = EXPORTS_DIR / filename
    
    # Basic security check to prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=file_path, 
        filename=filename, 
        # generic binary or specific excel content type
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    )

# Allow CORS for development (React dev server on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"status": "online", "service": "RyanRent Agent V2"}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, model: str = None):
    await websocket.accept()
    
    # Initialize a fresh agent for this connection
    # distinct agents per connection allows multi-user (or multi-tab) usage
    from .config import AVAILABLE_MODELS
    
    # Determine model to use
    selected_model = None
    if model:
        # Validate against available models if strictness is needed, 
        # or just trust the client for flexibility (as this is an internal tool)
        # Check if it matches any ID or Label
        for m_label, m_id in AVAILABLE_MODELS:
            if model == m_id or model == m_label:
                selected_model = m_id
                break
        if not selected_model:
             # Fallback if unknown model string, or maybe it's a raw string for a new provider
             selected_model = model
    
    if not selected_model: 
        selected_model = AVAILABLE_MODELS[0][1] # Default

    agent = RyanAgent(provider=selected_model)
    
    try:
        while True:
            # Receive text from client
            data = await websocket.receive_text()
            user_message = data # Expecting raw string or JSON?
            
            # If JSON, parse it (client might send structured obj)
            try:
                msg_json = json.loads(data)
                if isinstance(msg_json, dict) and 'message' in msg_json:
                    user_message = msg_json['message']
            except:
                pass
                
            logger.info(f"Received: {user_message}")

            # Send a user ack (optional, helps UI update immediately)
            # await websocket.send_json({"type": "user_msg", "content": user_message})

            # 1. CLASSIFY & PROCESS VIA PIPELINE
            try:
                # Use the pipeline to classify and potentially execute
                pipeline = get_pipeline()
                
                # Notify UI we are analyzing
                await websocket.send_json({"type": "log", "content": "🧠 Analyzing intent..."})
                
                # Process (this is synchronous but fast for classification)
                result = pipeline.process(user_message, export_format="xlsx")
                
                # 2. HANDLE NON-DATA INTENTS (Fallback to Chitchat Agent)
                if result.intent == "chitchat":
                    # Pass to legacy RyanAgent for conversation
                    log_msg = "💬 " + ("Conversational intent detected." if result.confidence > 0.8 else "Fallback to chat.")
                    await websocket.send_json({"type": "log", "content": log_msg})
                    
                    for chunk in agent.run(user_message):
                        if chunk.startswith("🔧"):
                            clean_chunk = chunk.replace("🔧 *Calling", "Executing").replace("🔧 *Tool Output:", "Output:").replace("`", "")
                            await websocket.send_json({"type": "log", "content": clean_chunk})
                        elif "❌" in chunk or "⚠️" in chunk:
                            await websocket.send_json({"type": "log", "content": chunk, "is_error": True})
                        else:
                            await websocket.send_json({"type": "text", "content": chunk})
                    
                    await websocket.send_json({"type": "done"})
                    continue

                # 3. HANDLE DATA INTENTS (Pipeline Output)
                
                # Report intent
                await websocket.send_json({"type": "log", "content": f"🎯 Identified intent: `{result.intent}`"})
                
                if result.success and result.export_path:
                    # Successful export
                    await websocket.send_json({"type": "log", "content": f"📊 Executing query: {result.sql_used.split('LIMIT')[0].strip()}..."})
                    await websocket.send_json({"type": "log", "content": f"💾 Exporting {result.row_count} rows..."})
                    
                    # Create a friendly message with the download link
                    msg = f"""**✅ Export Ready**
                    
Found **{result.row_count} rows** matching your request.
                    
[📥 Download Excel Report]({result.download_url})
"""
                    await websocket.send_json({"type": "text", "content": msg})
                    await websocket.send_json({"type": "done"})
                
                elif result.intent == "general_query" and not result.success:
                    # SQL Generation failed or returned error
                    await websocket.send_json({"type": "log", "content": f"❌ SQL Generation Failed: {result.message}", "is_error": True})
                    await websocket.send_json({"type": "text", "content": f"I tried to run a query but encountered an error: {result.message}"})
                    await websocket.send_json({"type": "done"})
                    
                else:
                    # Other failure (0 rows etc)
                    await websocket.send_json({"type": "log", "content": f"⚠️ {result.message}"})
                    await websocket.send_json({"type": "text", "content": result.message})
                    await websocket.send_json({"type": "done"})

            except Exception as e:
                logger.error(f"Pipeline Execution Error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"System Error: {str(e)}"
                })
                
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")

# --- Database Explorer Endpoints ---
from .sql_service import SQLService

sql_service = SQLService()

class SQLGenerateRequest(BaseModel):
    prompt: str
    model: str = "anthropic:claude-sonnet-4-5-20250929"

class SQLExecuteRequest(BaseModel):
    sql: str

@app.get("/api/tables")
async def get_tables():
    return {"tables": sql_service.get_tables()}

@app.get("/api/schema")
async def get_schema():
    return {"schema": sql_service.get_schema_details()}

@app.post("/api/sql/generate")
async def generate_sql(request: SQLGenerateRequest):
    sql = sql_service.generate_sql(request.prompt, request.model)
    # Clean up markdown fences if LLM ignored instructions
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return {"sql": sql}

@app.post("/api/sql/execute")
async def execute_sql(request: SQLExecuteRequest):
    result = sql_service.execute_sql(request.sql)
    return result

# --- System & Info Endpoints ---

@app.get("/api/system/status")
async def system_status():
    # Get active model from settings
    model_info = settings_service.get_active_model()
    
    return {
        "status": "online",
        "service": "RyanRent Agent V2",
        "last_refreshed": sql_service.last_refreshed,
        "active_model": model_info["display"]
    }

@app.get("/api/settings")
async def get_settings():
    """Get current settings"""
    return settings_service.load_settings()

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update settings"""
    success = settings_service.save_settings(settings)
    return {"success": success}

@app.post("/api/system/refresh")
async def refresh_system():
    timestamp = sql_service.refresh_schema()
    return {
        "status": "refreshed",
        "last_refreshed": timestamp
    }

@app.get("/api/files")
async def list_files():
    """Lists files in the exports directory, explicitly excluding intermediate query results."""
    files = []
    if EXPORTS_DIR.exists():
        for entry in os.scandir(EXPORTS_DIR):
            if entry.is_file():
                # Filter out query_result intermediate files
                if entry.name.startswith("query_result_"):
                    continue
                    
                stats = entry.stat()
                files.append({
                    "name": entry.name,
                    "url": f"http://localhost:8000/exports/{entry.name}",
                    "size": stats.st_size,
                    "created": stats.st_ctime
                })
    # Sort by creation time, newest first
    files.sort(key=lambda x: x['created'], reverse=True)
    return {"files": files}

# --- Config Endpoints ---
from .config import AVAILABLE_MODELS

@app.get("/api/config/models")
async def get_models():
    """Returns the list of available AI models from config."""
    # Convert list of tuples to list of objects for easier JSON consumption
    models = [{"label": label, "id": model_id} for label, model_id in AVAILABLE_MODELS]
    return {"models": models}

# --- Contract App Endpoints ---
from .contract_service import ContractService

contract_service = ContractService()

class ContractPrefillRequest(BaseModel):
    klant_id: int
    object_id: str
    overrides: dict = None

@app.get("/api/contracts/data")
async def get_contract_dropdown_data():
    return contract_service.get_dropdown_data()

@app.post("/api/contracts/prefill")
async def prefill_contract(request: ContractPrefillRequest):
    result = contract_service.get_prefilled_contract(
        request.klant_id, 
        request.object_id, 
        request.overrides
    )
    if not result:
        raise HTTPException(status_code=404, detail="Data not found for selection")
    return result

@app.get("/api/contracts/list")
async def list_contracts():
    return contract_service.list_generated_contracts()

@app.get("/api/contracts/download/{filename}")
async def download_contract(filename: str):
    file_path = contract_service.get_contract_file_path(filename)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

class ContractSaveRequest(BaseModel):
    filename: str
    markdown: str

@app.post("/api/contracts/save")
async def save_contract(request: ContractSaveRequest):
    success = contract_service.save_contract(request.filename, request.markdown)
    return {"success": success}


# --- Agentic Pipeline Endpoints ---
from .agentic import AgenticPipeline, INTENTS

# Singleton pipeline instance
_pipeline = None
def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = AgenticPipeline()
    return _pipeline

class AgenticAskRequest(BaseModel):
    question: str
    export_format: str = "xlsx"

@app.post("/api/agentic/ask")
async def agentic_ask(request: AgenticAskRequest):
    """
    Process a natural language question through the agentic pipeline.
    Returns export file info or error message.
    
    This is the token-efficient path:
    - Intent classification: ~200 tokens
    - Template resolution: 0 tokens (code)
    - Cache hit: 0 tokens
    """
    pipeline = get_pipeline()
    result = pipeline.process(request.question, request.export_format)
    return result.to_dict()

@app.get("/api/agentic/intents")
async def list_intents():
    """List available intents for the agentic pipeline."""
    return {
        "intents": [
            {
                "name": name,
                "description": defn.description,
                "supports_date_range": defn.supports_date_range,
                "supports_search": defn.supports_search
            }
            for name, defn in INTENTS.items()
            if name != "general_query"
        ],
        "fallback": "general_query"
    }

@app.get("/api/agentic/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    from .agentic.cache_manager import get_cache_stats
    return get_cache_stats()

@app.post("/api/agentic/cache/clear")
async def clear_cache():
    """Clear the export cache."""
    from .agentic.cache_manager import clear_cache
    deleted = clear_cache()
    return {"cleared": deleted}

