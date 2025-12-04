#!/usr/bin/env python3
"""
Test script to verify GoogleModelClient works end-to-end
"""

import asyncio
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("Testing GoogleModelClient with Gemini")
print("=" * 60)

from src.models.model_client import GoogleModelClient, ModelResponse

async def test_google_model_client():
    """Test the GoogleModelClient"""
    
    print("\n1. Initializing GoogleModelClient...")
    try:
        client = GoogleModelClient()
        print("✓ GoogleModelClient initialized successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize GoogleModelClient: {e}")
        return False
    
    print("\n2. Testing generate() method...")
    try:
        response = await client.generate(
            prompt="Say exactly: GoogleModelClient works!",
            temperature=0.5,
            max_tokens=50
        )
        print(f"✓ Response received: {response.content[:60]}")
        print(f"  Model: {response.model}")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate content: {e}")
        return False
    
    print("\n3. Testing generate_structured() method...")
    try:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["working", "not_working"]},
                "message": {"type": "string"}
            },
            "required": ["status", "message"]
        }
        
        response = await client.generate_structured(
            prompt='Return {"status": "working", "message": "GoogleModelClient structured output works!"}',
            schema=schema
        )
        print(f"✓ Structured response received: {response}")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate structured content: {e}")
        return False
    
    print("\n✅ SUCCESS: GoogleModelClient is fully functional!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_google_model_client())
    exit(0 if success else 1)
