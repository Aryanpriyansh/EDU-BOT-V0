import google.generativeai as genai

genai.configure(api_key="AIzaSyBkLgfBLM5ZpDxyVHbkoXSm7b2X59gRDuY")

models = genai.list_models()
print("✅ Available Gemini models:")
for m in models:
    print(m.name)
