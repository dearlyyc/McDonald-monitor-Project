import google.generativeai as genai
import config
import os

def test():
    print(f"Testing model: {config.GEMINI_MODEL}")
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    try:
        response = model.generate_content("Hello")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test()
