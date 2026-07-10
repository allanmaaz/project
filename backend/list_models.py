import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load backend env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path)

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    print("Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name} (supports generateContent)")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No GEMINI_API_KEY found.")
