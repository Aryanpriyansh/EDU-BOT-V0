import google.generativeai as genai

# ✅ Configure your Gemini API key here
genai.configure(api_key="AIzaSyBkLgfBLM5ZpDxyVHbkoXSm7b2X59gRDuY")

try:
    # ✅ Use stable model name (Gemini 1.5 Flash)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # ✅ Send a test prompt
    response = model.generate_content("What is Artificial Intelligence?")

    print("✅ Gemini API is working!")
    print("Response:", response.text)

except Exception as e:
    print("❌ Gemini API test failed!")
    print("Error:", e)
