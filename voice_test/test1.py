import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")

# Test with a sample audio file from Sarvam's own docs
# We'll use a simple GET to check if our key is valid
url = "https://api.sarvam.ai/speech-to-text"

headers = {
    "api-subscription-key": API_KEY
}

print("Testing Sarvam API connection...")
print(f"API Key found: {'YES' if API_KEY else 'NO - check your .env file'}")
print(f"API Key starts with: {API_KEY[:8]}..." if API_KEY else "")
print("\nAPI key loaded. Proceed to Test 2.")
