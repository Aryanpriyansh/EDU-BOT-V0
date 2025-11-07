import os
import re
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import google.generativeai as genai
from rapidfuzz import fuzz
from insert_contact import admin_contact

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -----------------------------
# MongoDB setup
# -----------------------------
class InMemoryCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
    def find(self, *args, **kwargs): return list(self.docs)
    def insert_many(self, docs): self.docs.extend(docs)
    def delete_many(self, _): self.docs = []
    def count_documents(self, query): return len(self.docs)

client = db = faqs = contacts = None

if not MONGO_URL:
    logging.warning("MONGO_URL not set. Using in-memory fallback.")
    faqs = InMemoryCollection([])
    contacts = InMemoryCollection([])
else:
    try:
        kwargs = {"serverSelectionTimeoutMS": 5000}
        if "mongodb+srv" in MONGO_URL:
            kwargs["tlsCAFile"] = certifi.where()
        client = MongoClient(MONGO_URL, **kwargs)
        client.admin.command("ping")
        db = client["chatbot_db"]
        faqs = db["faqs"]
        contacts = db["contacts"]
        logging.info("Connected to MongoDB.")
    except Exception as e:
        logging.exception("MongoDB connection failed. Using fallback.")
        faqs = InMemoryCollection([])
        contacts = InMemoryCollection([])

# -----------------------------
# Admin info
# -----------------------------
admin_name = getattr(admin_contact, "get", lambda x, y=None: "GAT Admin")("name", "GAT Admin")
admin_email = getattr(admin_contact, "get", lambda x, y=None: "admin@example.com")("email", "admin@example.com")

# -----------------------------
# Gemini setup
# -----------------------------
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logging.info("Configured Gemini client.")
    except Exception as e:
        logging.warning("Gemini setup failed: %s", e)
else:
    logging.warning("GEMINI_API_KEY not set. AI responses will not work.")

# -----------------------------
# Utility: normalize text
# -----------------------------
def _normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# -----------------------------
# Custom rule: detect HOD queries
# -----------------------------
def handle_hod_query(question: str):
    q = question.lower()
    if "hod" not in q:
        return None

    hods = {
        "cse": "Dr. Kumaraswamy S. is the HOD of the Computer Science and Engineering Department.",
        "computer science": "Dr. Kumaraswamy S. is the HOD of the Computer Science and Engineering Department.",
        "ai": "Dr. R. Chandramma is the HOD of the CSE (AI & ML) Department.",
        "ml": "Dr. R. Chandramma is the HOD of the CSE (AI & ML) Department.",
        "ise": "Dr. Kiran Y. C. is the HOD of the Information Science Engineering Department.",
        "information": "Dr. Kiran Y. C. is the HOD of the Information Science Engineering Department.",
        "ece": "Dr. Madhavi Mallam is the HOD of the Electronics and Communication Engineering Department.",
        "electronics": "Dr. Madhavi Mallam is the HOD of the Electronics and Communication Engineering Department.",
        "eee": "Dr. Deepika Masand is the HOD of the Electrical and Electronics Engineering Department.",
        "electrical": "Dr. Deepika Masand is the HOD of the Electrical and Electronics Engineering Department.",
        "mechanical": "Dr. Bharat Vinjamuri is the HOD of the Mechanical Engineering Department.",
        "civil": "Dr. Allamaprabhu Kamatagi is the HOD of the Civil Engineering Department.",
        "math": "Dr. Rupa K is the HOD of the Department of Mathematics.",
        "mba": "Dr. Sanjeev Kumar Thalari is the HOD of Management Studies (MBA)."
    }

    for key, answer in hods.items():
        if key in q:
            return answer
    return None

# -----------------------------
# FAQ matching
# -----------------------------
def get_best_faq_match(user_question: str):
    if faqs is None:
        return None

    user_q = _normalize_text(user_question or "")
    if not user_q:
        return None

    try:
        candidates = list(faqs.find({}, {"question": 1, "answer": 1})) if hasattr(faqs, "find") else list(faqs)
    except Exception as e:
        logging.exception("Error reading FAQs: %s", e)
        return None

    best_match = None
    best_score = -1
    for faq in candidates:
        q_text = _normalize_text(faq.get("question", ""))
        score = fuzz.token_sort_ratio(user_q, q_text)
        if q_text.startswith(user_q): score += 5
        if score > best_score:
            best_score = score
            best_match = faq

    if best_score >= 70:
        logging.info("Matched FAQ (score=%d): %s", best_score, best_match.get("question"))
        return best_match
    return None

# -----------------------------
# Ask Gemini (AI)
# -----------------------------
def ask_gemini(message: str) -> str:
    if not GEMINI_API_KEY:
        return "Sorry, I’m unable to connect to AI right now."

    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(f"Answer this as GAT college assistant:\n{message}")
        return response.text.strip() if hasattr(response, "text") else str(response)
    except Exception as e:
        logging.exception("Gemini API error: %s", e)
        return "Sorry, I couldn't generate an answer right now."

# -----------------------------
# Chat logic
# -----------------------------
def get_response(question: str):
    try:
        logging.info("Processing question: %s", question)

        # Step 1: Check for HOD queries first
        hod_answer = handle_hod_query(question)
        if hod_answer:
            return {"response": hod_answer, "source": "rule"}

        # Step 2: FAQ matching
        faq = get_best_faq_match(question)
        if faq:
            return {"response": faq.get("answer", "No answer found."), "source": "faq"}

        # Step 3: Gemini AI fallback for college queries
        if is_college_related(question):
            return {"response": ask_gemini(question), "source": "ai"}

        # Step 4: Final fallback
        fallback = (
            f"Sorry, I can only answer queries related to Global Academy of Technology. "
            f"Please contact {admin_name} at {admin_email}."
        )
        return {"response": fallback, "source": "fallback"}

    except Exception as e:
        logging.exception("Error in get_response: %s", e)
        return {"response": "An error occurred.", "source": "error"}

# -----------------------------
# Detect college-related queries
# -----------------------------
def is_college_related(question: str) -> bool:
    keywords = ["college", "admission", "fee", "course", "department", "faculty",
                "placement", "exam", "hod", "cse", "ece", "ise", "ai", "ml", "mba",
                "hostel", "transport", "canteen", "library", "scholarship"]
    return any(word in (question or "").lower() for word in keywords)

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="College Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    user_message: str

@app.post("/chat")
async def chat(input: ChatInput):
    result = await asyncio.to_thread(get_response, input.user_message)
    return result

@app.get("/faqs")
async def list_faqs():
    docs = list(faqs.find({}, {"question": 1, "answer": 1})) if hasattr(faqs, "find") else list(faqs)
    return {"count": len(docs), "faqs": docs}

@app.get("/ping")
async def ping():
    return {"message": "pong"}
