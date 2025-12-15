#!/usr/bin/env python3
"""
RyanRent Intelligent Agent - Launcher
Launch in TUI mode (default) or Web Mode.

Usage:
    python launch.py [--web]
"""
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Launch RyanRent Agent")
    parser.add_argument("--web", action="store_true", help="Launch in Web App mode")
    parser.add_argument("--tui", action="store_true", help="Launch in TUI mode")
    
    args = parser.parse_args()

    # Default to TUI if no flags, or if --tui is explicit
    if args.web:
        launch_web()
    else:
        launch_tui()

def launch_tui():
    print("🚀 Launching RyanRent TUI...")
    try:
        from ryan_v2.tui import RyanApp
        app = RyanApp()
        app.run()
    except ImportError as e:
        print(f"❌ Error launching TUI: {e}")
        print("Make sure you have textual installed: pip install textual")
    except Exception as e:
        print(f"❌ TUI Error: {e}")

def launch_web():
    print("🌐 Launching RyanRent Web API...")
    try:
        import uvicorn
        # We run uvicorn programmatically or just hint the command
        print("Starting FastAPI Backend at http://localhost:8000")
        uvicorn.run("ryan_v2.api:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("❌ Error: FastAPI/Uvicorn not found.")
        print("Please install web dependencies: pip install fastapi uvicorn")
    except Exception as e:
        print(f"❌ Web Error: {e}")

if __name__ == "__main__":
    main()
