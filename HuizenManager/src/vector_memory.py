import chromadb
from chromadb.config import Settings
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

class VectorMemory:
    """
    Persistent semantic memory using ChromaDB.
    Stores complete conversation history and retrieves relevant context.
    """
    
    def __init__(self, db_path: str = "database/memory_db", collection_name: str = "chat_history"):
        self.db_path = os.path.abspath(db_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize Client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or Create Collection
        # Using default embedding function (all-MiniLM-L6-v2) which is built-in
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        print(f"🧠 Vector Memory initialized at {self.db_path} (Collection: {collection_name})")

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a message to vector store.
        """
        if not content:
            return

        # Prepare metadata
        meta = metadata or {}
        meta.update({
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "year": datetime.now().year,
            "month": datetime.now().month
        })
        
        try:
            # Add to Chroma
            # We store the raw text as 'documents' for embedding
            self.collection.add(
                documents=[content],
                metadatas=[meta],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            print(f"⚠️ Failed to save to Vector Memory: {e}")

    def get_relevant_context(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Retrieve 'n_results' most relevant past messages for the query.
        """
        if not query:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Reformat results into a clean list of dicts
            context_messages = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    context_messages.append({
                        "role": meta.get("role", "unknown"),
                        "content": doc,
                        "timestamp": meta.get("timestamp")
                    })
            
            return context_messages
            
        except Exception as e:
            print(f"⚠️ Vector Search Failed: {e}")
            return []

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """
        Get the most recent 'limit' messages chronologically.
        Note: Chroma isn't optimized for strict time-ordering without a custom index,
        but we can query all and sort, or rely on simple metadata filtering if needed. 
        For true 'history', we might simple fetch the last N inserted if IDs were sequential, 
        but IDs are UUIDs.
        
        Solution: We might still keep a small 'hot' buffer in memory for immediate context, 
        and use Chroma for 'long term' retrieval.
        Or, we can query by 'timestamp' if we set up where clauses, but Chroma is strictly vector similarity by default.
        
        Actually, for a chat bot, we usually want:
        1. The very last X messages (immediate context)
        2. Relevant older messages (RAG)
        
        So 'VectorMemory' is redundant for 'Recent History' if we don't store it separately.
        WE WILL KEEP 'ConversationMemory' for the hot window, and use 'VectorMemory' for the long tail.
        """
        return [] 

    def search(self, query: str, n_results: int = 5) -> str:
        """
        Returns a formatted string of retrieved context for insertion into System Prompt.
        """
        messages = self.get_relevant_context(query, n_results)
        if not messages:
            return ""
            
        context_str = "--- PREVIOUS RELEVANT CONVERSATION ---\n"
        for msg in messages:
            context_str += f"[{msg['timestamp']}] {msg['role'].upper()}: {msg['content']}\n"
        context_str += "--------------------------------------\n"
        
        return context_str
