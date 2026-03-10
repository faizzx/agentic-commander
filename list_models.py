import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 Discovering 2026 Gemini Models...")

# The new SDK uses a simple list() method
for m in client.models.list():
    # We strip the 'models/' prefix for our code
    clean_name = m.name.replace("models/", "")
    print(f"✅ Available: {clean_name}")
    # print(dir(m)) # Print the attributes of the model object