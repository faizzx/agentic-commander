import os
from dotenv import load_dotenv
from google import genai

# Load the .env file
load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Ask a simple question
response = client.models.generate_content(
    model="gemini-2.5-flash",  # Use the stable 2026 workhorse
    contents="Hello! Confirm systems are online."
)

print(f"🤖 Gemini says: {response.text}")