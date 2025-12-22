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

            # Stream Agent Responses
            try:
                for chunk in agent.run(user_message):
                    # Check if chunk describes a tool call or text
                    if chunk.startswith("🔧"):
                         # Clean text for UI but keep some context if needed
                         # The TUI keeps "Executing" and "Output", let's pass the raw-ish string 
                         # but maybe clean up the bold markers if they are annoying.
                         # TUI does: content.replace("🔧 *Calling", "🔧 Executing").replace("🔧 *Tool Output:", "✅ Output:")
                         
                        clean_chunk = chunk.replace("🔧 *Calling", "Executing").replace("🔧 *Tool Output:", "Output:").replace("`", "")
                        await websocket.send_json({
                            "type": "log",
                            "content": clean_chunk
                        })
                    elif "❌" in chunk or "⚠️" in chunk:
                         await websocket.send_json({
                            "type": "log", # Treat as log for the thinking process
                            "content": chunk,
                            "is_error": True
                        })
                    else:
                        # Normal text stream
                        await websocket.send_json({
                            "type": "text",
                            "content": chunk
                        })
                
                # Signal done
                await websocket.send_json({"type": "done"})
                
            except Exception as e:
                logger.error(f"Agent Error: {e}")
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

