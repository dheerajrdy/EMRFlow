#!/usr/bin/env python3
"""
Quick test script to verify Gemini API is working with GOOGLE_API_KEY from .env
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("Testing Gemini API Setup")
print("=" * 60)

# Check if API key is loaded
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY not found in environment")
    print("   Make sure .env file exists and contains GOOGLE_API_KEY")
    exit(1)
else:
    print(f"✓ GOOGLE_API_KEY found: {api_key[:10]}...{api_key[-5:]}")

# Try to import and use google.generativeai
print("\nAttempting to import google.generativeai...")
try:
    import google.generativeai as genai
    print("✓ Successfully imported google.generativeai")
except ImportError as e:
    print(f"❌ ERROR: Failed to import google.generativeai: {e}")
    print("   Install with: pip install google-generativeai")
    exit(1)

# Configure and test the client
print("\nConfiguring Gemini client...")
try:
    genai.configure(api_key=api_key)
    print("✓ Successfully configured genai with API key")
except Exception as e:
    print(f"❌ ERROR: Failed to configure genai: {e}")
    exit(1)

# Test a simple generation
print("\nTesting model generation...")
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Respond with exactly: IT WORKS")
    
    if response and response.text:
        print(f"✓ Model response received: {response.text[:50]}")
        print("\n✅ SUCCESS: Gemini API is properly configured!")
    else:
        print("❌ ERROR: Model returned empty response")
        exit(1)
except Exception as e:
    print(f"❌ ERROR: Failed to generate content: {e}")
    print("   This might be an API key issue, quota issue, or network problem")
    exit(1)

print("=" * 60)
