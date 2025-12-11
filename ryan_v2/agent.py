"""
RYAN-V2: RyanRent Intelligent Agent
Main Agent Module

This is the heart of the agent: the manual agent loop.
Transparent, debuggable, and fully under our control.
"""
import json
import logging
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass, field
from datetime import datetime

from .config import MAX_ITERATIONS, MAX_RETRIES, DEFAULT_PROVIDER, MODEL_IDS
from .tools import get_tool_definitions, execute_tool, TOOLS
from .prompts import get_system_prompt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ryan_v2")


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # For tool results


@dataclass
class AgentState:
    """The agent's state across turns."""
    messages: List[Message] = field(default_factory=list)
    current_focus: Optional[str] = None  # e.g., "Keizersgracht property"
    iteration_count: int = 0
    
    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))
        self.iteration_count = 0  # Reset on new user turn
    
    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict]] = None):
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))
    
    def add_tool_result(self, tool_call_id: str, name: str, result: str):
        self.messages.append(Message(
            role="tool",
            content=result,
            tool_call_id=tool_call_id,
            name=name
        ))
    
    def to_openai_format(self) -> List[Dict]:
        """Convert messages to OpenAI API format."""
        formatted = []
        for msg in self.messages:
            if msg.role == "user":
                formatted.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                m = {"role": "assistant", "content": msg.content or ""}
                if msg.tool_calls:
                    m["tool_calls"] = msg.tool_calls
                formatted.append(m)
            elif msg.role == "tool":
                formatted.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name,
                    "content": msg.content
                })
        return formatted


class RyanAgent:
    """
    The RYAN V2 Agent.
    
    Uses a manual agent loop for full transparency and control.
    """
    
    def __init__(self, provider: str = DEFAULT_PROVIDER):
        # Handle composite "provider:model_id" strings (from TUI)
        if ":" in provider:
            self.provider, self.model_id = provider.split(":", 1)
        else:
            # Fallback for simple provider names
            self.provider = provider
            self.model_id = MODEL_IDS.get(provider, MODEL_IDS["anthropic"])
        
        self.state = AgentState()
        self.system_prompt = get_system_prompt()
        self.tools = get_tool_definitions()
        
        logger.info(f"Ryan V2 initialized with provider: {self.provider} (Model: {self.model_id})")
    
    def _call_llm(self, messages: List[Dict]) -> Dict:
        """
        Call the LLM and return the response.
        
        This is a placeholder - will be implemented with actual API calls.
        Returns format: {"content": str, "tool_calls": Optional[List]}
        """
        # Import provider-specific implementation
        if self.provider == "anthropic":
            return self._call_anthropic(messages)
        elif self.provider == "openai":
            return self._call_openai(messages)
        elif self.provider == "google":
            return self._call_google(messages)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _call_anthropic(self, messages: List[Dict]) -> Dict:
        """Call Claude API."""
        import anthropic
        
        client = anthropic.Anthropic()
        
        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            })
        
        # Convert messages to Anthropic format
        anthropic_msgs = []
        for msg in messages:
            if msg["role"] == "user":
                anthropic_msgs.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                anthropic_msgs.append({"role": "assistant", "content": content if content else msg.get("content", "")})
            elif msg["role"] == "tool":
                # Tool results - aggregate into user message
                if anthropic_msgs and anthropic_msgs[-1]["role"] == "user" and isinstance(anthropic_msgs[-1]["content"], list):
                    anthropic_msgs[-1]["content"].append({
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"]
                    })
                else:
                    anthropic_msgs.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"]
                        }]
                    })
        
        response = client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            system=self.system_prompt,
            tools=anthropic_tools,
            messages=anthropic_msgs
        )
        
        # Parse response
        result = {"content": "", "tool_calls": None}
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })
        
        if tool_calls:
            result["tool_calls"] = tool_calls
        
        return result
    
    def _call_openai(self, messages: List[Dict]) -> Dict:
        """Call OpenAI API."""
        from openai import OpenAI
        
        client = OpenAI()
        
        # Prepend system message
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages
        
        response = client.chat.completions.create(
            model=self.model_id,
            messages=full_messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        result = {"content": msg.content or "", "tool_calls": None}
        
        if msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        
        return result
    
    def _call_google(self, messages: List[Dict]) -> Dict:
        """Call Google Gemini API."""
        import google.generativeai as genai
        
        # Setup model
        model = genai.GenerativeModel(
            model_name=self.model_id,
            system_instruction=self.system_prompt
        )
        
        # Convert to Gemini format and call
        # This is a simplified version - expand as needed
        chat = model.start_chat()
        
        # Get the last user message
        last_user_msg = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break
        
        if last_user_msg:
            response = chat.send_message(last_user_msg)
            return {"content": response.text, "tool_calls": None}
        
        return {"content": "No message to process.", "tool_calls": None}
    
    def run(self, user_input: str) -> Generator[str, None, None]:
        """
        Process a user input and yield responses.
        
        This is the main agent loop - yields intermediate steps and final answer.
        """
        self.state.add_user_message(user_input)
        logger.info(f"User: {user_input[:100]}...")
        
        for iteration in range(MAX_ITERATIONS):
            self.state.iteration_count = iteration + 1
            logger.info(f"Agent loop iteration {iteration + 1}")
            
            # Call LLM
            messages = self.state.to_openai_format()
            response = self._call_llm(messages)
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls")
            
            # If no tool calls, this is the final answer
            if not tool_calls:
                self.state.add_assistant_message(content)
                logger.info("Final answer reached")
                yield content
                return
            
            # Process tool calls
            self.state.add_assistant_message(content, tool_calls)
            
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])
                tool_id = tc["id"]
                
                logger.info(f"Calling tool: {tool_name}({tool_args})")
                yield f"🔧 *Calling `{tool_name}`...*\n"
                
                # Execute the tool
                result = execute_tool(tool_name, tool_args)
                self.state.add_tool_result(tool_id, tool_name, result)
                
                logger.info(f"Tool result: {result[:200]}...")
        
        # If we hit max iterations, return what we have
        yield "⚠️ Maximum iterations reached. Here's what I found so far."
    
    def ask(self, user_input: str) -> str:
        """
        Synchronous version of run() - returns the final answer only.
        """
        final_answer = ""
        for response in self.run(user_input):
            if not response.startswith("🔧"):  # Skip tool call notifications
                final_answer = response
        return final_answer
    
    def reset(self):
        """Clear conversation history."""
        self.state = AgentState()
        logger.info("Agent state reset")


# =============================================================================
# CLI Interface for Testing
# =============================================================================
def main():
    """Simple CLI for testing the agent."""
    print("🏠 RYAN V2 - RyanRent Intelligent Agent")
    print("=" * 50)
    print("Type 'quit' to exit, 'reset' to clear history\n")
    
    agent = RyanAgent()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("Tot ziens! 👋")
                break
            
            if user_input.lower() == "reset":
                agent.reset()
                print("🔄 Conversation reset.\n")
                continue
            
            print("\nRyan: ", end="", flush=True)
            
            for response in agent.run(user_input):
                print(response)
            
            print()
            
        except KeyboardInterrupt:
            print("\nTot ziens! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
