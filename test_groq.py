#!/usr/bin/env python3
"""
Simple test script to verify Groq client works correctly
"""

try:
    from groq import Groq
    
    # Test client initialization
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set")
        exit(1)
    
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized successfully")
    
    # Test a simple API call
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": "Say hello"}],
        temperature=0.1,
        max_tokens=10
    )
    
    print("✅ API call successful")
    print(f"Response: {response.choices[0].message.content}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure groq is installed: pip install groq")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check your API key and internet connection")