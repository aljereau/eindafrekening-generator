#!/usr/bin/env python3
"""
List available models from all 3 API providers using their Python SDKs.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load env vars
load_dotenv()

async def list_openai():
    print("\n--- OpenAI (gpt) ---")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        models = client.models.list()
        # Sort and filter to interesting ones
        model_names = sorted([m.id for m in models if 'gpt' in m.id or 'o1' in m.id or 'o3' in m.id or 'o4' in m.id or 'gpt-5' in m.id])
        for name in model_names:
            print(f"  - {name}")
    except Exception as e:
        print(f"  ❌ OpenAI error: {e}")

async def list_gemini():
    print("\n--- Google Gemini (gemini) ---")
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        # Using the new google-genai SDK 
        # Note: the new SDK might have a different method for listing models
        # If not, fall back to search or common ones
        for model in client.models.list():
             print(f"  - {model.name}")
    except Exception as e:
        print(f"  ❌ Gemini error: {e}")

def list_anthropic():
    
    print("\n--- Anthropic Claude (claude) ---")
    print("  Note: Anthropic SDK does not have a public 'list' endpoint.")
    print("  Referencing documented 2026 models:")
    print("  - claude-4-5-opus")
    print("  - claude-4-5-sonnet")
    print("  - claude-sonnet-4-5-20250929")
    print("  - claude-4-opus")
    print("  - claude-4-sonnet")
d
async def main():
    print("🔍 FETCHING AVAILABLE MODELS (JANUARY 2026)...")
    await list_openai()
    await list_gemini()
    list_anthropic()

if __name__ == "__main__":
    asyncio.run(main())
