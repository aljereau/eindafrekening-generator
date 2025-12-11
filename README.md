# RyanRent Bot & Tools

This repository contains the RyanRent Intelligence Bot (TUI) and utilities like the Eindafrekening Generator.

## 🚀 Quick Start (Any Machine)

The easiest way to run the bot is using the provided start script. It handles Docker setup automatically.

### Prerequisites
- Docker & Docker Compose installed.
- A `.env` file with your API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`).

### Launch
```bash
./start.sh
```

This will:
1.  Build the secure container.
2.  Install all dependencies.
3.  Launch the interactive Chat TUI.

---

## 🛠️ Manual Launch (Developers)

### Local Python
If you prefer running without Docker:
```bash
# 1. Setup venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run
./start_bot.command
# OR
python3 HuizenManager/src/chat.py
```

### Docker Manual
If you want to run docker commands yourself:
*   **Build**: `docker compose build`
*   **Run**: `docker compose run --rm --service-ports ryanrent-bot`
    *   *Note: usage of `run` instead of `up` is required to allow you to type in the chat window.*

## 📂 Directory Structure
*   **`HuizenManager/`**: Core logic and source code.
    *   `src/`: Main python source (`bot.py`, `chat.py`).
*   **`TUI/`**: The visual terminal interface (Textual based).
*   **`Eindafrekening/`**: The Excel generator module.
*   **`Shared/`**: Shared resources (DB schema, scripts).
