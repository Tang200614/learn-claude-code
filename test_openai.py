#!/usr/bin/env python3
"""Test with OpenAI SDK"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Try with OpenAI SDK
print("Testing with OpenAI SDK...")
try:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL")
    )

    response = client.chat.completions.create(
        model=os.getenv("MODEL_ID"),
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
