# HuizenManager Source Code

This directory contains the core logic for the RyanRent Chatbot and intelligence system.

## Core "Mini-APIs"

The system is built around several specialized modules:

### 🤖 Bot Logic
*   **`bot.py`**: The main entry point for the `RyanRentBot`. Handles conversation flow, tool execution loops, and context management.
*   **`strategy_bot.py`**: Specialized logic for strategy advice (if applicable).

### 🧠 Intelligence Layer
*   **`intelligence_api.py`**: Abstraction layer for LLM providers. Handles switching between OpenAI and Anthropic (Claude), managing API keys, and normalizing responses.
*   **`mcp_agent.py`**: Implements a "Model Context Protocol" agent that can query the SQL database using natural language. It acts as a specialized sub-agent for data retrieval.

### 💼 Business Logic
*   **`manager.py`**: The central "Manager" class that orchestrates high-level operations. It connects the bot, database, and file systems.
*   **`cli.py`**: Command Line Interface handling.

### 💾 Data & I/O
*   **`file_exchange.py`**: Handles reading and writing of Excel files, JSON exports, and file system interactions.
*   **`database/`**: Contains database connection logic and schema definitions.

## Key Flows

1.  **Chat**: `bot.py` receives a message -> calls `intelligence_api.py` -> LLM decides to call a tool -> `bot.py` executes tool via `manager.py` or `mcp_agent.py`.
2.  **Data Query**: User asks "Which houses...?". `bot.py` calls `ask_database` -> `mcp_agent.py` generates SQL -> `database` executes it -> results returned to Chat.
