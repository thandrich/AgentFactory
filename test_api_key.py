import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_key():
    print("Loading .env file...")
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment variables.")
        print("Please ensure you have a .env file with GOOGLE_API_KEY=AIzaSy...")
        return

    print(f"Found API Key: {api_key[:5]}...{api_key[-5:]}")
    
    print("Configuring Gemini API...")
    genai.configure(api_key=api_key)
    
    print("Attempting to list models...")
    try:
        models = list(genai.list_models())
        print(f"SUCCESS! Found {len(models)} models.")
        
        valid_model = None
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"Found supported model: {m.name}")
                valid_model = m.name
                break
        
        if not valid_model:
            print("ERROR: No model found that supports generateContent.")
            return

        print(f"\nAttempting simple generation with {valid_model}...")
        model = genai.GenerativeModel(valid_model)
        response = model.generate_content("Say 'Hello, World!'")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"\nERROR: API call failed.")
        print(f"Details: {e}")

if __name__ == "__main__":
    test_key()
