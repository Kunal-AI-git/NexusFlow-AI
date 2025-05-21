from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from datetime import datetime
import uuid

app = FastAPI()

# === CORS Middleware (Optional for frontend) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Load Zero-Shot Classifier ===
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# === Threat Categories & Regex Fallback ===
THREAT_CATEGORIES = [
    "harmless question", "how to hack", "prompt injection", "cyber attack",
    "exploit a website", "bypass login", "steal user data", "phishing",
    "data exfiltration", "malicious intent"
]
KEYWORDS = [
    "how to hack", "bypass login", "steal cookies", "csrf", "xss",
    "inject", "malware", "man in the middle", "phishing", "sql injection"
]

# === In-Memory Session Store ===
session_store = {}  # session_id => [messages]

# === Threat Detection ===
def is_llm_threat(text: str) -> bool:
    result = classifier(text, THREAT_CATEGORIES, multi_label=True)
    for label, score in zip(result["labels"], result["scores"]):
        if label != "harmless question" and score > 0.6:
            print(f"[Zero-Shot] Threat detected: {label} (score={score:.2f})")
            return True
    return False

def is_regex_threat(text: str) -> bool:
    text_lower = text.lower()
    for keyword in KEYWORDS:
        if keyword in text_lower:
            print(f"[Regex] Threat keyword matched: {keyword}")
            return True
    return False

def is_threatening(text: str) -> bool:
    return is_llm_threat(text) or is_regex_threat(text)

# === Dummy LLM Response ===
def dummy_llm_response(prompt: str) -> str:
    return f"🤖 **Response:** _{prompt}_"

# === Request Schema ===
class ChatInput(BaseModel):
    message: str
    session_id: str

class SessionInput(BaseModel):
    session_id: str

# === Welcome Endpoint ===
@app.get("/")
async def root():
    return {"message": "🚀 NexusFlow AI Chat is running!"}

# === Chat Endpoint ===
@app.post("/chat")
async def chat(input: ChatInput):
    message = input.message.strip()
    session_id = input.session_id.strip()

    if is_threatening(message):
        log_event = {
            "event": "Blocked Threat",
            "session_id": session_id,
            "input": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        print("[LOG]", log_event)

        return JSONResponse({
            "status": "error",
            "message": "🚨 Input flagged as malicious and blocked.",
            "blocked": True,
            "response_id": f"res_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
        })

    if session_id not in session_store:
        session_store[session_id] = []
    session_store[session_id].append({"role": "user", "content": message})

    response = dummy_llm_response(message)
    session_store[session_id].append({"role": "bot", "content": response})

    return {
        "status": "success",
        "response_id": f"res_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat(),
        "content": {"LLM Response": response},
        "session_context": session_store[session_id],
        "blocked": False
    }

# === View Chat History ===
@app.get("/history")
async def get_history(session_id: str):
    history = session_store.get(session_id)
    if history:
        return {"status": "success", "session_id": session_id, "history": history}
    return {"status": "error", "message": "Session not found."}

# === Clear History (Preserve Session ID) ===
@app.post("/clear-history")
async def clear_history(input: SessionInput):
    session_id = input.session_id
    if session_id in session_store:
        session_store[session_id] = []
        return {"status": "success", "message": "History cleared.", "session_id": session_id}
    return {"status": "error", "message": "Session not found."}

# === End Session Completely ===
@app.post("/end-session")
async def end_session(input: SessionInput):
    session_id = input.session_id
    session_store.pop(session_id, None)
    return {"status": "success", "message": "Session ended.", "session_id": session_id}
