from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import logging
import asyncio

from .agent import RyanAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ryan_api")

app = FastAPI(title="RyanRent Agent API")

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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize a fresh agent for this connection
    # distinct agents per connection allows multi-user (or multi-tab) usage
    from .config import AVAILABLE_MODELS
    # Use the same default as TUI
    default_model = AVAILABLE_MODELS[0][1]
    agent = RyanAgent(provider=default_model)
    
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
