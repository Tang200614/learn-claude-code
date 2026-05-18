#!/usr/bin/env python3
"""Test the API connection"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("Environment variables loaded:")
print(f"  ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY')[:20] if os.getenv('ANTHROPIC_API_KEY') else None}...")
print(f"  ANTHROPIC_BASE_URL: {os.getenv('ANTHROPIC_BASE_URL')}")
print(f"  MODEL_ID: {os.getenv('MODEL_ID')}")
print()

# Try different client initialization methods
from anthropic import Anthropic

print("Testing with explicit api_key parameter...")
try:
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL")
    )

    # Try a simple request
    response = client.messages.create(
        model=os.getenv("MODEL_ID"),
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("✓ Success!")
    print(response)
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
